"""Diagnóstico transversal municipal e prescrições preliminares, com dados reais.

Uso, na raiz do projeto: python scripts/diagnostico.py
Requer numpy, pandas, matplotlib, scipy e statsmodels. Não modifica a base.
Modelos servem para explorar associações; não estimam efeitos causais ou economia.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.stats import spearmanr
import statsmodels
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
COST = "despesa_manejo_por_hab_ibge2024"
TON = "despesa_manejo_por_t_rsu"
REC = "recuperacao_total_calculada_pct"
SEL = "cobertura_seletiva_ibge2024_pct"
POP = "populacao_ibge_2024"
DEX = "despesa_exploracao_manejo_rs_ano"
MASS = "massa_rsu_coletada_t_ano"
RMASS = "massa_recuperada_secos_organicos_t_ano"
RAIS = "vinculos_formais_totais_por_1000_hab"
PORTES = ["até 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "mais de 500 mil"]
REGIONS = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]


def metadata_path(path: Path) -> str:
    """Identifica arquivos sem publicar o caminho do perfil da execução."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.name


def save(frame: pd.DataFrame, directory: Path, name: str) -> None:
    frame.to_csv(directory / name, index=False, encoding="utf-8-sig")


def br(value, decimals=2) -> str:
    if pd.isna(value):
        return "indisponível"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def md_table(frame: pd.DataFrame) -> str:
    text = "| " + " | ".join(str(c) for c in frame.columns) + " |\n"
    text += "|" + "|".join("---" for _ in frame.columns) + "|\n"
    for row in frame.itertuples(index=False, name=None):
        text += "| " + " | ".join(str(v).replace("|", "/").replace("\n", " ") for v in row) + " |\n"
    return text


def descriptive(frame: pd.DataFrame, variables: list[str], sample: str) -> pd.DataFrame:
    result = frame[variables].describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).T.reset_index(names="variavel")
    result.insert(0, "amostra", sample)
    result["zeros"] = [int(frame[c].eq(0).sum()) for c in variables]
    result["ausentes"] = [int(frame[c].isna().sum()) for c in variables]
    return result


def grouped(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for group, part in frame.groupby(keys, observed=True, sort=False):
        group = group if isinstance(group, tuple) else (group,)
        rows.append(dict(zip(keys, group)) | {
            "n": len(part), "populacao_amostra": int(part[POP].sum()),
            "custo_hab_mediana": part[COST].median(), "custo_hab_q1": part[COST].quantile(.25),
            "custo_hab_q3": part[COST].quantile(.75), "custo_hab_media": part[COST].mean(),
            "custo_t_mediana": part[TON].median(), "recuperacao_mediana_pct": part[REC].median(),
            "recuperacao_media_pct": part[REC].mean(), "recuperacao_positiva_n": int(part[REC].gt(0).sum()),
            "recuperacao_positiva_pct": part[REC].gt(0).mean() * 100,
            "seletiva_mediana_pct": part[SEL].median(),
            "seletiva_positiva_pct": part[SEL].gt(0).mean() * 100,
            "dex_soma_rs": part[DEX].sum(), "rsu_soma_t": part[MASS].sum(),
            "recuperada_soma_t": part[RMASS].sum(),
            "razao_somas_recuperacao_pct": part[RMASS].sum() / part[MASS].sum() * 100,
            "razao_somas_dex_hab": part[DEX].sum() / part[POP].sum(),
        })
    return pd.DataFrame(rows)


def rho(frame: pd.DataFrame, x: str, y: str) -> tuple[int, float]:
    values = frame[[x, y]].dropna()
    if len(values) < 3 or values[x].nunique() < 2 or values[y].nunique() < 2:
        return len(values), float("nan")
    return len(values), float(spearmanr(values[x], values[y]).statistic)


def partial_rank(frame: pd.DataFrame, x: str, y: str, control: list[str]) -> tuple[int, float]:
    """Pearson dos resíduos dos postos: correlação parcial nos postos, com UF."""
    part = frame[[x, y, "uf"] + control].dropna()
    ranked = part[[x, y] + control].rank(method="average")
    states = pd.get_dummies(part["uf"], drop_first=True, dtype=float)
    design = np.column_stack([np.ones(len(part)), ranked[control].to_numpy(), states.to_numpy()])
    residuals = []
    for col in [x, y]:
        values = ranked[col].to_numpy()
        fitted = design @ np.linalg.lstsq(design, values, rcond=None)[0]
        residuals.append(values - fitted)
    return len(part), float(np.corrcoef(residuals)[0, 1])


def models(samples: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    coefficients, diagnostics = [], []
    specifications = {
        "cobertura_sem_controles": "rec ~ sel_10",
        "custo_sem_controles": "rec ~ log_custo",
        "cobertura_porte_uf": "rec ~ sel_10 + log_pop + C(uf)",
        "custo_porte_uf": "rec ~ log_custo + log_pop + C(uf)",
        "conjunto_porte_uf": "rec ~ sel_10 + log_custo + log_pop + C(uf)",
        "conjunto_contexto_formal": "rec ~ sel_10 + log_custo + log_pop + log_densidade_formal + C(uf)",
    }
    for sample_name, original in samples.items():
        for model_name, formula in specifications.items():
            frame = pd.DataFrame({"rec": original[REC], "sel_10": original[SEL] / 10,
                                  "log_custo": np.log(original[COST]), "log_pop": np.log(original[POP]),
                                  "uf": original["uf"]})
            if "log_densidade_formal" in formula:
                if RAIS not in original:
                    continue
                frame["log_densidade_formal"] = np.log1p(original[RAIS])
            frame = frame.dropna()
            groups = frame.uf.nunique()
            fit = smf.ols(formula, data=frame).fit(cov_type="cluster", cov_kwds={"groups": frame.uf, "use_correction": True}, use_t=True)
            interval = fit.conf_int(alpha=.05)
            prediction = fit.predict(frame)
            diagnostics.append({"amostra": sample_name, "modelo": model_name, "formula": formula,
                                "n": int(fit.nobs), "ufs": int(groups), "r2": fit.rsquared,
                                "previsoes_lineares_fora_0_100": int((~prediction.between(0, 100)).sum()),
                                "covariancia": "cluster UF; correção amostra finita; IC t com G-1 graus de liberdade",
                                "df_ic": float(fit.df_resid_inference),
                                "interpretacao": "associação transversal; não usar para previsão ou efeito causal"})
            for term in ["sel_10", "log_custo", "log_pop", "log_densidade_formal"]:
                if term not in fit.params:
                    continue
                factor = np.log(2) if term == "log_custo" else 1
                coefficients.append({"amostra": sample_name, "modelo": model_name, "n": int(fit.nobs),
                                     "termo": term, "coeficiente": fit.params[term],
                                     "erro_padrao_cluster_uf": fit.bse[term],
                                     "ic95_inferior": interval.loc[term, 0], "ic95_superior": interval.loc[term, 1],
                                     "p_valor_descritivo": fit.pvalues[term],
                                     "contraste_interpretavel_pp": fit.params[term] * factor,
                                     "contraste_ic95_inferior_pp": interval.loc[term, 0] * factor,
                                     "contraste_ic95_superior_pp": interval.loc[term, 1] * factor,
                                     "unidade_contraste": "10 pontos de cobertura" if term == "sel_10" else ("dobro da despesa por habitante" if term == "log_custo" else "uma unidade logarítmica")})
    return pd.DataFrame(coefficients), pd.DataFrame(diagnostics)


def audit_raw(root: Path, sample: pd.DataFrame, directory: Path) -> dict:
    files = list((root / "data/raw").rglob("*Despesas*.xlsx"))
    if not files:
        return {"executada": False, "motivo": "planilha bruta extraída de despesas não encontrada"}
    source = files[0]
    raw = pd.read_excel(source, header=12)
    raw.columns = [re.sub(r"[^A-Za-z0-9_]", "", str(c)) for c in raw]
    raw["cod_ibge"] = raw.Cod_IBGE.astype("Int64").astype(str)
    selected = set()
    for col in [COST, TON]:
        selected.update(sample.nlargest(10, col).cod_ibge)
        selected.update(sample.nsmallest(10, col).cod_ibge)
    columns = ["cod_ibge", "GFI2209", "GFI2210", "GFI2219", "GFI2220", "GFI2221"]
    part = sample.loc[sample.cod_ibge.isin(selected), ["cod_ibge", "municipio", "uf", POP, COST, TON, DEX, MASS]].merge(raw[columns], on="cod_ibge", validate="one_to_one")
    for col in columns[1:]:
        part[col] = pd.to_numeric(part[col], errors="raise")
    part["soma_componentes_dex"] = part[["GFI2209", "GFI2210", "GFI2219", "GFI2220"]].sum(axis=1, min_count=4)
    part["diferenca_soma_componentes_rs"] = part.GFI2221 - part.soma_componentes_dex
    part["diferenca_base_vs_bruto_rs"] = part[DEX] - part.GFI2221
    save(part.sort_values(COST, ascending=False), directory, "auditoria_extremos_componentes_sinisa.csv")
    assert part.diferenca_base_vs_bruto_rs.abs().le(.01).all(), "Diferença inesperada ETL versus planilha original"
    return {"executada": True, "arquivo": str(source.relative_to(root)).replace("\\", "/"),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "n_extremos_distintos": len(part),
            "diferenca_maxima_base_bruto_rs": float(part.diferenca_base_vs_bruto_rs.abs().max()),
            "diferenca_maxima_componentes_rs": float(part.diferenca_soma_componentes_rs.abs().max())}


def figures(sample, trimmed, sensitivity, by_size, bins, correlation, coefficients, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    teal, orange = "#147D78", "#C65B2D"
    paths = []
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.7), layout="constrained")
    axes[0].hist(np.log10(sample[COST]), bins=48, color=teal, edgecolor="white")
    axes[0].set(xlabel="log10 da DEX de manejo por habitante residente", ylabel="Municípios", title=f"Distribuição completa (n = {len(sample):,})".replace(",", "."))
    mean = sensitivity.loc[sensitivity.amostra.isin(["base", "corte_p1_p99_hab"])]
    positions = np.arange(len(mean))
    axes[1].barh(positions-.16, mean.custo_hab_media, height=.3, color=orange, label="Média municipal")
    axes[1].barh(positions+.16, mean.custo_hab_mediana, height=.3, color=teal, label="Mediana municipal")
    axes[1].set(yticks=positions, yticklabels=["Base completa", "Corte de custos P1–P99"], xlabel="R$/habitante residente.ano", title="A média muda com os extremos")
    axes[1].legend(frameon=False, loc="center right")
    fig.suptitle("Custos declarados exigem auditoria antes de comparações", fontweight="bold")
    fig.supxlabel("SINISA + IBGE, 2024. O corte é análise de sensibilidade; valores originais foram preservados.", fontsize=9)
    path = directory / "01_custos_extremos_sensibilidade.png"; fig.savefig(path, dpi=180); plt.close(fig); paths.append(path.name)

    fig, ax = plt.subplots(figsize=(9.5, 5), layout="constrained")
    groups = [trimmed.loc[trimmed.porte_populacional.eq(p), COST] for p in PORTES]
    ax.boxplot(groups, tick_labels=[f"{p}\n(n={len(g):,})".replace(",", ".") for p, g in zip(PORTES, groups)], showfliers=False)
    ax.set(ylabel="DEX de manejo (R$/habitante residente.ano)", xlabel="População municipal", title="Comparar custos exige considerar o porte do município")
    fig.supxlabel("Corte P1–P99 da despesa/habitante. Box plot oculta pontos além dos bigodes, preservados nos CSVs.", fontsize=9)
    path = directory / "02_custos_por_porte.png"; fig.savefig(path, dpi=180); plt.close(fig); paths.append(path.name)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), layout="constrained")
    axes[0].scatter(sample[SEL], sample[REC], alpha=.16, s=9, linewidth=0, color=teal)
    axes[0].set(xlabel="População coberta por coleta seletiva (%)", ylabel="Massa de secos + orgânicos recuperada / RSU (%)", title="Todos os municípios da amostra")
    x = np.arange(len(bins))
    axes[1].plot(x, bins.recuperacao_mediana_pct, marker="o", color=teal, label="Mediana")
    axes[1].plot(x, bins.recuperacao_media_pct, marker="s", color=orange, label="Média")
    axes[1].set(xticks=x, xticklabels=bins.faixa_cobertura, xlabel="Cobertura seletiva (%)", ylabel="Recuperação (%)", title="Cobertura e intensidade não são equivalentes")
    axes[1].legend(frameon=False)
    for i, row in bins.iterrows():
        axes[1].annotate(f"n={int(row.n):,}".replace(",", "."), (i, row.recuperacao_media_pct), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8)
    fig.suptitle("A associação inclui muitos zeros declarados", fontweight="bold")
    fig.supxlabel("Mesma fonte operacional para cobertura e recuperação. Associação transversal não mede o efeito de ampliar o serviço.", fontsize=9)
    path = directory / "03_cobertura_recuperacao.png"; fig.savefig(path, dpi=180); plt.close(fig); paths.append(path.name)

    selected = coefficients.loc[coefficients.modelo.eq("conjunto_porte_uf") & coefficients.termo.eq("sel_10")].copy()
    labels = {"base": "Base completa", "corte_p1_p99_hab": "Custos P1–P99", "recuperacao_positiva": "Recuperação > 0", "corte_e_recuperacao_positiva": "P1–P99 e recuperação > 0"}
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    for i, row in enumerate(selected.itertuples()):
        ax.errorbar(row.contraste_interpretavel_pp, i,
                    xerr=[[row.contraste_interpretavel_pp-row.contraste_ic95_inferior_pp], [row.contraste_ic95_superior_pp-row.contraste_interpretavel_pp]],
                    fmt="o", color=teal, capsize=4)
    ax.set(yticks=range(len(selected)), yticklabels=[f"{labels[r.amostra]} (n={r.n:,})".replace(",", ".") for r in selected.itertuples()],
           xlabel="Associação linear: pontos de recuperação por 10 pontos de cobertura", title="A interpretação muda quando os zeros são separados")
    ax.axvline(0, color="#666666", lw=1, linestyle="--")
    ax.invert_yaxis()
    fig.supxlabel("OLS com log da população, log da despesa/habitante e efeitos de UF. IC 95% agrupados por UF; sem interpretação causal.", fontsize=9)
    path = directory / "04_associacao_ajustada_sensibilidade.png"; fig.savefig(path, dpi=180); plt.close(fig); paths.append(path.name)
    return paths


def report(root, directory, info, sensitivity, by_region, by_size, correlations, coeff, bins, zero_cases, extremes):
    def coefficient(sample, model, term):
        return coeff.loc[coeff.amostra.eq(sample) & coeff.modelo.eq(model) & coeff.termo.eq(term)].iloc[0]
    def coefficient_text(row):
        return f"{br(row.contraste_interpretavel_pp)} pp (IC descritivo de 95% {br(row.contraste_ic95_inferior_pp)} a {br(row.contraste_ic95_superior_pp)}; n={br(row.n, 0)})"
    def correlation(sample, x, y):
        return correlations.loc[correlations.amostra.eq(sample) & correlations.x.eq(x) & correlations.y.eq(y) & correlations.metodo.eq("Spearman")].iloc[0]
    base = sensitivity.loc[sensitivity.amostra.eq("base")].iloc[0]
    trim = sensitivity.loc[sensitivity.amostra.eq("corte_p1_p99_hab")].iloc[0]
    positive = sensitivity.loc[sensitivity.amostra.eq("recuperacao_positiva")].iloc[0]
    full_coverage = coefficient("base", "conjunto_porte_uf", "sel_10")
    positive_coverage = coefficient("recuperacao_positiva", "conjunto_porte_uf", "sel_10")
    full_cost = coefficient("base", "conjunto_porte_uf", "log_custo")
    trim_cost = coefficient("corte_p1_p99_hab", "conjunto_porte_uf", "log_custo")
    rais_coverage = coefficient("base", "conjunto_contexto_formal", "sel_10") if (coeff.modelo == "conjunto_contexto_formal").any() else None
    core_corr = correlation("base", SEL, REC)
    positive_corr = correlation("recuperacao_positiva", SEL, REC)
    sens_table = sensitivity[["amostra", "n", "custo_hab_media", "custo_hab_mediana", "custo_t_media", "custo_t_mediana", "recuperacao_mediana_pct"]].copy()
    sens_table.columns = ["Amostra", "n", "Média R$/hab", "Mediana R$/hab", "Média R$/t", "Mediana R$/t", "Mediana recuperação %"]
    for c in sens_table.columns[1:]:
        sens_table[c] = sens_table[c].map(lambda v: br(v, 0 if c == "n" else 2))
    region_table = by_region[["regiao", "n", "custo_hab_mediana", "recuperacao_positiva_pct"]].copy()
    region_table.columns = ["Região", "n", "Mediana R$/hab", "Municípios com recuperação >0 (%)"]
    size_table = by_size[["porte_populacional", "n", "custo_hab_mediana", "recuperacao_positiva_pct"]].copy()
    size_table.columns = ["Porte", "n", "Mediana R$/hab", "Municípios com recuperação >0 (%)"]
    for t in [region_table, size_table]:
        for c in t.columns[1:]:
            t[c] = t[c].map(lambda v: br(v, 0 if c == "n" else 2))
    p1, p99 = info["corte_custo_hab_p1"], info["corte_custo_hab_p99"]
    response_min = min(info["cobertura_respostas"], key=lambda row: row["resposta_pct"])
    response_max = max(info["cobertura_respostas"], key=lambda row: row["resposta_pct"])
    audit = info["auditoria_bruta"]
    audit_text = (f"A comparação dos {br(audit['n_extremos_distintos'], 0)} municípios distintos selecionados nas dez maiores e dez menores razões por habitante ou tonelada confirmou diferença máxima de R$ {br(audit['diferenca_maxima_base_bruto_rs'])} entre a base e GFI2221 na planilha original. O máximo desvio da soma de componentes foi R$ {br(audit['diferenca_maxima_componentes_rs'])}." if audit["executada"] else f"Auditoria da planilha original não executada: {audit['motivo']}.")
    text = f"""# Diagnóstico e prescrições

## O que os dados sustentam agora

O problema imediato é a confiabilidade de valores extremos de despesa. A coleta seletiva e a recuperação aparecem associadas, mas boa parte dessa associação distingue municípios com zero e com valor positivo. Os dados transversais de 2024 não demonstram que aumentar cobertura cause determinada recuperação, economia ou contratação.

Fonte analisada: `data/processed/saneamento_municipios_2024_parcial.csv`, SHA256 `{info['sha256_dataset']}`. Execução em UTC: {info['executado_em_utc']}. A base lida tem {br(info['linhas_base'],0)} linhas e {br(info['colunas_base'],0)} colunas. O script `scripts/diagnostico.py` leu os bytes uma única vez e calculou o hash dessa mesma versão. Resultados completos estão em `analises/diagnostico/`; o JSON `resumo_diagnostico.json` registra regras, versões e números.

## Amostra e decisões

Dos {br(info['linhas_base'],0)} municípios, {br(info['respondentes'],0)} responderam ao SINISA e {br(info['nao_respondentes'],0)} não responderam. A amostra principal tem {br(base.n,0)} municípios: respondentes com DEX e massa coletada positivas, recuperação entre 0% e 100% e sem os alertas de qualidade definidos pelo ETL. Os dois alertas de soma de massa ficam fora dessa análise, com os dados preservados. Nenhum não respondente foi transformado em zero.

Na amostra principal, {br(info['recuperacao_zero_n'],0)} municípios ({br(info['recuperacao_zero_pct'])}%) têm recuperação declarada igual a zero; {br(info['seletiva_zero_n'],0)} ({br(info['seletiva_zero_pct'])}%) têm cobertura seletiva igual a zero. A análise também foi repetida apenas nos {br(positive.n,0)} municípios com recuperação positiva. Essa segunda população responde a outra pergunta: intensidade entre quem já declara recuperação. Ela não substitui a amostra principal e pode selecionar municípios com melhor capacidade de registro.

As médias, medianas e correlações são municipais, sem ponderação, salvo quando o arquivo indica explicitamente “razão de somas”. Essas razões descrevem apenas os municípios da amostra, sem extrapolação para o Brasil inteiro. DEX é despesa operacional de manejo, inclui atividades além da coleta e não representa investimento. Recuperação inclui secos e orgânicos. O indicador oficial IFR2002 usa habitante **coberto**; o indicador analítico usa habitante **residente** do IBGE DOU 29/08/2024.

## 1. Custos extremos e sensibilidade

A mediana é R$ {br(base.custo_hab_mediana)} por habitante. A média de R$ {br(base.custo_hab_media)} é muito sensível à cauda superior. Para verificar essa dependência, foram conservados os municípios entre o percentil 1 (R$ {br(p1)}) e o percentil 99 (R$ {br(p99)}) da despesa por habitante. Os limites foram calculados na amostra principal, sem alterar o CSV original. O corte é uma ferramenta de diagnóstico, não uma prova de erro nem um padrão de custo aceitável.

{md_table(sens_table)}

No corte P1–P99, a média por habitante muda {br((trim.custo_hab_media/base.custo_hab_media-1)*100)}%, enquanto a mediana muda {br((trim.custo_hab_mediana/base.custo_hab_mediana-1)*100)}%. A igualdade exata da mediana também decorre de retirar o mesmo número de observações de cada cauda dessa variável; não é uma validação independente dos dados. O corte simultâneo por custo por tonelada mostra outra sensibilidade na tabela. Mediana e intervalo interquartil devem acompanhar a auditoria dos extremos. Os {br(info['top1pct_n'],0)} municípios acima de P99 por habitante concentram {br(info['top1pct_dex_share_pct'])}% da DEX declarada da amostra, mas {br(info['top1pct_population_share_pct'])}% de sua população. As somas de despesa também precisam dessa ressalva.

Exemplos para conferir documentos de origem, sem classificação de eficiência:

{md_table(extremes)}

{audit_text} Os montantes extremos já estão no arquivo oficial e, em diversos casos, são dominados pelo campo de serviços de terceiros GFI2210. O ETL não gerou esses montantes ao converter números. Compatibilidade aritmética não comprova veracidade econômica. Valores de unidade, competência anual, escopo e contratos ainda exigem confirmação. Não foram divididos por mil, substituídos ou imputados.

O valor baixo também requer cuidado: Feira de Santana (BA) declara DEX de R$ {br(info['feira_dex'])}, equivalente a R$ {br(info['feira_custo_hab'])}/habitante. Esses registros não justificam concluir que é um município mais eficiente. A lista completa de extremos e os componentes estão nos CSVs de auditoria.

## 2. Porte e região mudam a comparação

{md_table(region_table)}

{md_table(size_table)}

Os grupos apresentam composição, escala e distribuição de despesas diferentes. As tabelas completas `por_regiao_porte.csv` e `por_regiao_porte_corte_p1_p99.csv` permitem comparar dentro do mesmo porte e região, com o n de cada célula. A própria resposta à coleta SINISA é desigual: {br(response_min['resposta_pct'])}% no {response_min['regiao']} e {br(response_max['resposta_pct'])}% no {response_max['regiao']}. Esse contraste não foi corrigido por ponderação ou imputação e pode influenciar a comparação regional. Não se deve usar uma mediana regional como meta para todos os municípios. Células pequenas e valores extremos exigem leitura individual. Densidade urbana, distância de transporte, qualidade dos contratos, preço da disposição e nível do serviço não estão na base e continuam como explicações concorrentes.

## 3. Coleta seletiva e recuperação: presença versus intensidade

Spearman entre cobertura seletiva e recuperação é {br(core_corr.rho,3)} na amostra completa (n={br(core_corr.n,0)}). Entre municípios com recuperação positiva, passa a {br(positive_corr.rho,3)} (n={br(positive_corr.n,0)}). O contraste demonstra que a interpretação depende de incluir ou separar os zeros. Isso não torna nenhum dos resultados inválido; são perguntas diferentes.

Com cobertura seletiva positiva, {br(info['seletiva_positiva_recuperacao_positiva_n'],0)} de {br(info['seletiva_positiva_n'],0)} municípios têm recuperação positiva ({br(info['seletiva_positiva_recuperacao_positiva_pct'])}%). Com cobertura seletiva zero, {br(info['seletiva_zero_recuperacao_positiva_n'],0)} de {br(info['seletiva_zero_n'],0)} têm recuperação positiva ({br(info['seletiva_zero_recuperacao_positiva_pct'])}%). Cobertura é população servida com frequência mínima semanal e recuperação é massa anual. Uma não substitui a outra. Os dois indicadores vêm da mesma cadeia operacional e da mesma fonte administrativa, o que também limita uma leitura causal independente.

As faixas de cobertura não apresentam intensidade estritamente crescente. O gráfico `03_cobertura_recuperacao.png` exibe essa diferença e o n de cada faixa. Há {br(len(zero_cases),0)} municípios que declaram cobertura positiva e recuperação zero; a lista foi salva para conferir pesagem, destinação, rejeitos e período de funcionamento, sem presumir erro. Há ainda {br(info['seletiva_zero_recuperacao_positiva_n'],0)} com cobertura zero e recuperação positiva, que exigem entender frequência, rotas e registro institucional.

## 4. Controles estatísticos e o que não explicam

Os modelos lineares exploratórios relacionam a recuperação em pontos percentuais à cobertura (por dez pontos), ao logaritmo da despesa por habitante e ao logaritmo da população, com indicadores fixos para cada UF. Usam erros padrão agrupados por UF, correção para amostra finita e intervalos t com G−1 graus de liberdade. Eles comparam diferenças condicionais, sem eliminar seleção de respondentes, simultaneidade ou variáveis omitidas.

Na amostra completa, a associação ajustada de dez pontos adicionais de cobertura é {coefficient_text(full_coverage)}. Apenas nos municípios com recuperação positiva, é {coefficient_text(positive_coverage)}. A figura `04_associacao_ajustada_sensibilidade.png` mostra as quatro amostras. Condicionar a análise a um resultado positivo muda a população e pode alterar a associação por seleção e composição. O sinal negativo dessa subamostra não demonstra que ampliar coleta reduza a recuperação. Não interpretar os coeficientes como o ganho esperado de uma política.

Dobrar a despesa por habitante está associado a {coefficient_text(full_cost)} na amostra completa, mantendo os demais termos do modelo. No corte P1–P99, a associação é {coefficient_text(trim_cost)}. O sinal e sua estabilidade devem ser lidos com os intervalos, sem concluir que mais despesa cause melhor desempenho ou que cortar despesa mantenha o mesmo serviço.

{"Ao acrescentar o contexto da densidade de vínculos formais de todos os setores, a associação ajustada de cobertura é " + coefficient_text(rais_coverage) + ". Quatro municípios de Mato Grosso com incompatibilidade territorial ficam sem a taxa RAIS; o modelo usa somente as observações disponíveis. Essa variável contextual não mede emprego verde." if rais_coverage is not None else "A taxa contextual da RAIS total não estava disponível para esse controle."}

OLS pode produzir valores ajustados fora de 0% a 100%: isso ocorre em {br(info['ols_base_previsoes_fora_0_100_n'],0)} observações no modelo conjunto da amostra principal. `diagnosticos_modelos.csv` registra a quantidade por especificação. Por isso não foi usado como preditor operacional. Os intervalos refletem hipóteses do modelo, não corrigem erros administrativos nem garantem representação dos não respondentes. Os CSVs também registram Spearman por porte/região e correlações parciais nos postos com controles. Valores-p não foram usados para declarar sucesso de políticas.

Não foi usado “custo por tonelada versus recuperação” como evidência de efeito: ambos dividem pela massa coletada, podendo criar associação matemática por denominador comum. As comparações principais usam despesa por habitante e explicitam o papel da população.

## 5. Prescrições vinculadas às evidências

| Evidência executada | Ação proposta para o gestor | Como acompanhar e limite |
|---|---|---|
| Média de custo depende da cauda e {br(info['fora_corte_custo_hab_n'],0)} registros ficam fora de P1–P99; extremos conferem com a planilha bruta. | Priorizar conferência documental desses registros e dos dois alertas de massa. Conferir reais versus milhares, anual versus mensal, soma de componentes, escopo e terceirização. | Registrar cada confirmação ou retificação. Suspender metas de economia e comparações públicas de eficiência desses casos até a conferência. Percentis são prioridade de auditoria, não prova de erro. |
| Custos e recuperação variam por porte e região. | Escolher comparáveis do mesmo porte e região, validar escopo e usar mediana e quartis como referência de investigação. | Acrescentar distância de rotas, cobertura efetiva, toneladas pesadas e preço de destinação antes de avaliar contratos. Sem esses dados, não atribuir diferença a desperdício. |
| {br(info['recuperacao_zero_n'],0)} municípios da amostra declaram recuperação zero; a associação de cobertura muda ao separar os zeros. | Conferir se o zero representa ausência real, rejeição total ou registro incompleto. Planejar piloto de coleta, triagem e destinação com medição de massa e rejeitos. | Medir secos e orgânicos separadamente, custo incremental, regularidade, contaminação e rejeitos. A análise não fornece uma previsão de recuperação nem um número de vagas a contratar. |
| {br(len(zero_cases),0)} casos combinam cobertura seletiva positiva e recuperação zero. | Conferir primeiro a operação e o registro desses casos: frequência, início do serviço, pesagem e destino. | Resolver divergências de conceito antes de ampliar infraestrutura. Cobertura populacional isolada não prova recuperação de material. |
| O custo inclui manejo completo; recuperação mede secos e orgânicos. | Elaborar orçamento de um piloto com coleta, triagem, tratamento, transporte, disposição dos rejeitos e receita efetiva de materiais. | Comparar custos adicionais e qualidade de serviço ao cenário atual. Não prometer que a venda de materiais cobrirá a despesa nem impor redução de pessoal com base nesta correlação. |
| A RAIS usada nos controles deste diagnóstico é o total de todos os setores. No SINISA, catadores autônomos têm {br(info['catadores_autonomos_ausentes_respondentes'],0)} ausências entre os {br(info['respondentes'],0)} respondentes. | Interpretar o recorte CNAE 38 e seus grupos no estudo separado `docs/EMPREGO_SETORIAL_ANALISE.md`. Combinar o diagnóstico agregado com cadastro local de cooperativas e trabalhadores. | Não chamar vínculo total ou toda atividade da CNAE 38 de emprego verde, nem trabalhador SINISA de vínculo RAIS. Medir qualidade, formalização e renda em futuro piloto. Automatização e exigências de contratação podem excluir trabalhadores; prever qualificação e participação antes de mudanças. |

As propostas de piloto são decisões de gestão a testar, não intervenções com efeito estimado neste estudo. Custos de implantação, manutenção, demanda por material recuperado e possíveis mudanças no trabalho podem reduzir o benefício líquido. A base atual não quantifica essas parcelas nem a informalidade municipal completa.

## Hipóteses e perguntas para a próxima etapa

1. As despesas extremas correspondem a unidades, período, escopo ou contratos diferentes? A soma aritmética correta ainda precisa de confirmação documental.
2. Após verificar custos e comparar municípios semelhantes, o padrão de recuperação permanece? A sensibilidade já executada ajuda a delimitar, sem resolver, essa questão.
3. Em municípios com serviço seletivo declarado, perdas de triagem e frequência explicam a intensidade de recuperação? Essas variáveis operacionais precisam ser obtidas.
4. A distribuição de vínculos formais na CNAE 38 e seus grupos é examinada separadamente em `docs/EMPREGO_SETORIAL_ANALISE.md`. Associação municipal com recuperação não comprova criação líquida de empregos verdes.

Referências de definição: glossários de informações e indicadores do [SINISA 2025, ano de referência 2024](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025) e [estimativas municipais IBGE 2024](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/). Códigos e fórmulas utilizados estão no dicionário do projeto e nos scripts. As conclusões deste documento derivam dos arquivos efetivamente processados, não de percentuais nacionais de notícias.
"""
    path = root / "docs/DIAGNOSTICO_E_PRESCRICOES.md"
    path.write_text(text, encoding="utf-8")


def run(source: Path, directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(directory / ".matplotlib_cache"))
    content = source.read_bytes()
    data = pd.read_csv(io.BytesIO(content), dtype={"cod_ibge": str})
    required = {COST, TON, REC, SEL, POP, DEX, MASS, RMASS, "uf", "regiao", "apta_analise_custo_recuperacao"}
    assert required.issubset(data.columns)
    assert data.cod_ibge.str.fullmatch(r"\d{7}").all() and not data.cod_ibge.duplicated().any()
    sample = data.loc[data.apta_analise_custo_recuperacao.eq(True)].copy()
    assert sample[[COST, TON, REC, SEL, POP]].notna().all().all()
    assert sample[COST].gt(0).all() and sample[TON].gt(0).all() and sample[REC].between(0, 100).all()
    sample["porte_populacional"] = pd.Categorical(sample.porte_populacional, PORTES, ordered=True)
    sample["regiao"] = pd.Categorical(sample.regiao, REGIONS, ordered=True)
    p1, p99 = sample[COST].quantile([.01, .99]).tolist()
    t1, t99 = sample[TON].quantile([.01, .99]).tolist()
    trimmed = sample.loc[sample[COST].between(p1, p99)].copy()
    both = trimmed.loc[trimmed[TON].between(t1, t99)].copy()
    samples = {"base": sample, "corte_p1_p99_hab": trimmed,
               "corte_p1_p99_hab_e_t": both,
               "recuperacao_positiva": sample.loc[sample[REC].gt(0)].copy(),
               "corte_e_recuperacao_positiva": trimmed.loc[trimmed[REC].gt(0)].copy()}
    sensitivity = pd.concat([pd.DataFrame([{
        "amostra": name, "n": len(part), "custo_hab_media": part[COST].mean(),
        "custo_hab_mediana": part[COST].median(), "custo_t_media": part[TON].mean(),
        "custo_t_mediana": part[TON].median(), "recuperacao_mediana_pct": part[REC].median(),
        "recuperacao_media_pct": part[REC].mean(), "cobertura_seletiva_mediana_pct": part[SEL].median(),
        "recuperacao_zero_n": int(part[REC].eq(0).sum()),
        "razao_somas_dex_hab": part[DEX].sum()/part[POP].sum(),
        "razao_somas_dex_t": part[DEX].sum()/part[MASS].sum(),
        "razao_somas_recuperacao_pct": part[RMASS].sum()/part[MASS].sum()*100,
    }]) for name, part in samples.items()], ignore_index=True)
    save(sensitivity, directory, "sensibilidade_amostras.csv")
    variables = [COST, TON, REC, SEL, POP, "pessoal_manejo_sinisa", "catadores_organizados_sinisa", "catadores_autonomos_informados_sinisa"]
    if RAIS in data:
        variables.append(RAIS)
    save(pd.concat([descriptive(part, variables, name) for name, part in samples.items()], ignore_index=True), directory, "estatisticas_por_amostra.csv")
    coverage = data.groupby("regiao").agg(n=("cod_ibge", "size"), respondentes=("respondeu_sinisa", lambda v: v.eq("Sim").sum())).reset_index()
    coverage["resposta_pct"] = coverage.respondentes / coverage.n * 100
    save(coverage, directory, "cobertura_respostas.csv")
    by_region, by_size = grouped(sample, ["regiao"]), grouped(sample, ["porte_populacional"])
    by_region = by_region.set_index("regiao").reindex(REGIONS).reset_index()
    by_size = by_size.set_index("porte_populacional").reindex(PORTES).reset_index()
    save(by_region, directory, "por_regiao.csv"); save(by_size, directory, "por_porte.csv")
    save(grouped(sample, ["regiao", "porte_populacional"]), directory, "por_regiao_porte.csv")
    save(grouped(trimmed, ["regiao", "porte_populacional"]), directory, "por_regiao_porte_corte_p1_p99.csv")
    bin_labels = ["0", ">0–25", ">25–50", ">50–75", ">75–100"]
    categories = pd.cut(sample[SEL], [-.001, 0, 25, 50, 75, 100], labels=bin_labels)
    bins = grouped(sample.assign(faixa_cobertura=categories), ["faixa_cobertura"])
    bins = bins.set_index("faixa_cobertura").reindex(bin_labels).reset_index()
    save(bins, directory, "por_faixa_cobertura_seletiva.csv")
    correlations = []
    pairs = [(SEL, REC), (COST, REC), (POP, REC), (POP, COST)]
    if RAIS in data:
        pairs.append((RAIS, REC))
    for name, part in samples.items():
        for x, y in pairs:
            n, value = rho(part, x, y)
            correlations.append({"amostra": name, "x": x, "y": y, "n": n, "rho": value, "metodo": "Spearman", "controles": "nenhum"})
        for x, control in [(SEL, [POP, COST]), (COST, [POP, SEL])]:
            n, value = partial_rank(part, x, REC, control)
            correlations.append({"amostra": name, "x": x, "y": REC, "n": n, "rho": value,
                                 "metodo": "parcial nos postos", "controles": ";".join(control) + ";UF"})
    corr_frame = pd.DataFrame(correlations)
    save(corr_frame, directory, "correlacoes_sensibilidade.csv")
    stratified = []
    for group in ["regiao", "porte_populacional"]:
        for label, part in sample.groupby(group, observed=True):
            for x in [SEL, COST]:
                for only_positive in [False, True]:
                    chosen = part.loc[part[REC].gt(0)] if only_positive else part
                    n, value = rho(chosen, x, REC)
                    stratified.append({"grupo": group, "categoria": label, "somente_recuperacao_positiva": only_positive, "x": x, "y": REC, "n": n, "rho_spearman": value})
    save(pd.DataFrame(stratified), directory, "correlacoes_por_porte_regiao.csv")
    coeff, model_diag = models({key: part for key, part in samples.items() if key != "corte_p1_p99_hab_e_t"})
    assert np.isfinite(coeff[["coeficiente", "erro_padrao_cluster_uf", "ic95_inferior", "ic95_superior"]]).all().all()
    save(coeff, directory, "coeficientes_modelos.csv"); save(model_diag, directory, "diagnosticos_modelos.csv")
    extreme_cols = ["cod_ibge", "municipio", "uf", POP, DEX, MASS, COST, TON, REC, SEL, "pessoal_manejo_sinisa"]
    audits = []
    for variable in [COST, TON]:
        for side in ["maiores", "menores"]:
            selection = sample.nlargest(10, variable) if side == "maiores" else sample.nsmallest(10, variable)
            audits.append(selection[extreme_cols].assign(criterio=variable, cauda=side))
    save(pd.concat(audits, ignore_index=True), directory, "extremos_para_auditoria.csv")
    zero_cases = sample.loc[sample[SEL].gt(0) & sample[REC].eq(0), extreme_cols]
    save(zero_cases, directory, "cobertura_positiva_recuperacao_zero.csv")
    save(sample.loc[sample[SEL].eq(0) & sample[REC].gt(0), extreme_cols], directory, "cobertura_zero_recuperacao_positiva.csv")
    missing = pd.DataFrame({"coluna": data.columns, "ausentes_base": data.isna().sum().to_numpy(),
                            "zeros_base": [int(data[c].eq(0).sum()) if pd.api.types.is_numeric_dtype(data[c]) else None for c in data]})
    save(missing, directory, "zeros_e_ausentes.csv")
    audit = audit_raw(ROOT, sample, directory)
    high = sample.loc[sample[COST].gt(p99)]
    feira = sample.loc[sample.cod_ibge.eq("2910800")].iloc[0]
    info = {"executado_em_utc": datetime.now(timezone.utc).isoformat(), "sha256_dataset": hashlib.sha256(content).hexdigest(),
            "arquivo_entrada": metadata_path(source), "linhas_base": len(data), "colunas_base": len(data.columns),
            "respondentes": int(data.respondeu_sinisa.eq("Sim").sum()), "nao_respondentes": int(data.respondeu_sinisa.ne("Sim").sum()),
            "n_principal": len(sample), "recuperacao_zero_n": int(sample[REC].eq(0).sum()), "recuperacao_zero_pct": float(sample[REC].eq(0).mean()*100),
            "seletiva_zero_n": int(sample[SEL].eq(0).sum()), "seletiva_zero_pct": float(sample[SEL].eq(0).mean()*100),
            "seletiva_positiva_n": int(sample[SEL].gt(0).sum()),
            "seletiva_positiva_recuperacao_positiva_n": int((sample[SEL].gt(0)&sample[REC].gt(0)).sum()),
            "seletiva_positiva_recuperacao_positiva_pct": float(sample.loc[sample[SEL].gt(0),REC].gt(0).mean()*100),
            "seletiva_zero_recuperacao_positiva_n": int((sample[SEL].eq(0)&sample[REC].gt(0)).sum()),
            "seletiva_zero_recuperacao_positiva_pct": float(sample.loc[sample[SEL].eq(0),REC].gt(0).mean()*100),
            "corte_custo_hab_p1": p1, "corte_custo_hab_p99": p99, "corte_custo_t_p1": t1, "corte_custo_t_p99": t99,
            "fora_corte_custo_hab_n": len(sample)-len(trimmed), "top1pct_n": len(high),
            "top1pct_dex_share_pct": float(high[DEX].sum()/sample[DEX].sum()*100),
            "top1pct_population_share_pct": float(high[POP].sum()/sample[POP].sum()*100),
            "feira_dex": float(feira[DEX]), "feira_custo_hab": float(feira[COST]),
            "catadores_autonomos_ausentes_base": int(data.catadores_autonomos_informados_sinisa.isna().sum()),
            "catadores_autonomos_ausentes_respondentes": int(data.loc[data.respondeu_sinisa.eq("Sim"),"catadores_autonomos_informados_sinisa"].isna().sum()),
            "setorial_cnae38_presente_na_base": "vinculos_cnae38_3112" in data,
            "auditoria_bruta": audit,
            "versoes": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "scipy": scipy.__version__, "statsmodels": statsmodels.__version__},
            "regras": {"amostra": "apta_analise_custo_recuperacao == True; sem mudar zeros ou valores originais",
                       "cortes": "quantis 1 e 99 calculados na amostra principal; intervalo inclusivo; não substitui validação de origem",
                       "modelos": "OLS associativo, não preditivo, com IC95% cluster UF e t G-1; efeito da despesa expresso por duplicação",
                       "rais": "vínculos formais totais de todos os setores como controle contextual; não emprego verde"}}
    info["estatisticas_principais"] = json.loads(sensitivity.loc[sensitivity.amostra.eq("base")].to_json(orient="records"))[0]
    info["cobertura_respostas"] = json.loads(coverage.to_json(orient="records"))
    info["ols_base_previsoes_fora_0_100_n"] = int(model_diag.loc[model_diag.amostra.eq("base") & model_diag.modelo.eq("conjunto_porte_uf"), "previsoes_lineares_fora_0_100"].iloc[0])
    info["sensibilidade_amostras"] = json.loads(sensitivity.to_json(orient="records"))
    info["correlacoes_principais"] = json.loads(corr_frame.loc[corr_frame.x.isin([SEL,COST])].to_json(orient="records"))
    info["modelos_ajustados_principais"] = json.loads(coeff.loc[coeff.modelo.eq("conjunto_porte_uf") & coeff.termo.isin(["sel_10","log_custo"])].to_json(orient="records"))
    info["por_porte"] = json.loads(by_size.to_json(orient="records"))
    info["por_regiao"] = json.loads(by_region.to_json(orient="records"))
    info["prescricoes"] = ["Auditar extremos monetários, componentes e os dois alertas de massa antes de metas de economia.",
        "Comparar municípios do mesmo porte e região, verificando nível e escopo do serviço.",
        "Separar presença de recuperação de sua intensidade; verificar zeros e fluxo de pesagem/rejeitos.",
        "Testar um piloto com custo incremental, qualidade, rejeitos e receitas efetivas, sem prometer economia causal.",
        "Interpretar CNAE 38 e grupos em estudo separado; medir qualidade do trabalho e incluir catadores, sem equiparar vínculos a empregos verdes."]
    info["figuras"] = figures(sample, trimmed, sensitivity, by_size, bins, corr_frame, coeff, directory)
    extremes = sample.nlargest(5, COST)[["municipio", "uf", POP, DEX, COST]].copy()
    extremes.columns = ["Município", "UF", "População", "DEX anual (R$)", "DEX R$/hab"]
    for col in extremes.columns[2:]:
        extremes[col] = extremes[col].map(lambda value: br(value, 0 if col == "População" else 2))
    report(ROOT, directory, info, sensitivity, by_region, by_size, corr_frame, coeff, bins, zero_cases, extremes)
    (directory / "resumo_diagnostico.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=ROOT / "data/processed/saneamento_municipios_2024_parcial.csv")
    parser.add_argument("--saida", type=Path, default=ROOT / "analises/diagnostico")
    args = parser.parse_args()
    result = run(args.entrada, args.saida)
    print(json.dumps({key: result[key] for key in ["executado_em_utc", "sha256_dataset", "linhas_base", "colunas_base", "n_principal", "figuras"]}, ensure_ascii=False, indent=2))
