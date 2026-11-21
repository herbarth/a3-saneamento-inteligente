"""ETL municipal 2024: SINISA + IBGE e, quando disponível, agregado RAIS.

Executar da raiz do projeto: python scripts/etl.py
Não preenche dados ausentes com zero e não usa nomes para integrar municípios.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
OUT = ROOT / "data/processed"
EVID = ROOT / "evidencias"

# Código oficial -> (nome analítico, unidade). Não são sinônimos de investimento.
FIELDS = {
    "GFI2221": ("despesa_exploracao_manejo_rs_ano", "R$/ano"),
    "GFI2208": ("despesa_exploracao_limpeza_urbana_rs_ano", "R$/ano"),
    "GFI2233": ("despesa_total_servicos_rs_ano", "R$/ano"),
    "GFI2237": ("investimento_total_rs_ano", "R$/ano"),
    "GFI2266": ("pessoal_manejo_sinisa", "trabalhadores"),
    "GTR1025": ("massa_domiciliar_coletada_t_ano", "t/ano"),
    "GTR1026": ("massa_coleta_seletiva_t_ano", "t/ano"),
    "GTR1027": ("massa_limpeza_urbana_t_ano", "t/ano"),
    "GTR1028": ("massa_rsu_coletada_t_ano", "t/ano"),
    "GTR1029": ("massa_recuperada_secos_organicos_t_ano", "t/ano"),
    "GTR1309": ("associacoes_cooperativas_catadores", "associações/cooperativas"),
    "GTR1310": ("catadores_organizados_sinisa", "catadores"),
    "GTR1311": ("catadores_autonomos_informados_sinisa", "catadores"),
    "GTR0201": ("populacao_coberta_coleta_sinisa", "habitantes"),
    "GTR0205": ("populacao_coberta_seletiva_sinisa", "habitantes"),
    "IFR2002": ("despesa_manejo_por_hab_coberto_sinisa_oficial", "R$/habitante coberto.ano"),
    "IRS0001": ("cobertura_coleta_sinisa_oficial_pct", "%"),
    "IRS0005": ("cobertura_seletiva_sinisa_oficial_pct", "%"),
    "IRS3010": ("recuperacao_total_sinisa_oficial_pct", "%"),
    "IRS3011": ("recuperacao_secos_sinisa_oficial_pct", "%"),
    "IRS3012": ("recuperacao_organicos_sinisa_oficial_pct", "%"),
    "IRS3002": ("disposicao_inadequada_sinisa_oficial_pct", "%"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "", str(value or ""))


def sinisa_table(path: Path, indicators: bool = False) -> tuple[pd.DataFrame, dict, list]:
    """Lê a aba municipal; cabeçalho de indicadores difere do de informações."""
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.worksheets[0]
    rows = sheet.iter_rows(values_only=True)
    top = [next(rows) for _ in range(13)]
    headers = [normalized(v) for v in top[10 if indicators else 12]]
    # As primeiras 16 colunas são cadastrais e têm posição confirmada na inspeção.
    headers[:16] = ["respondeu_sinisa", "cod_ibge", "municipio_sinisa", "uf_sinisa",
                    "regiao", "capital", "cnpj", "setor", "natureza_juridica",
                    "populacao_base_sinisa", "pop_urbana", "pop_rural",
                    "dom_total", "dom_urbano", "dom_rural", "area_km2"]
    assert len(headers) == len(set(headers)), f"Cabeçalho duplicado em {path}"
    df = pd.DataFrame(rows, columns=headers)
    workbook.close()
    n_read = len(df)
    # A planilha Manejo inclui linhas formatadas sem município após os dados.
    df["cod_ibge"] = df["cod_ibge"].map(lambda v: str(int(v)) if isinstance(v, (int, float)) and pd.notna(v) else str(v).strip())
    valid = df["cod_ibge"].str.fullmatch(r"\d{7}", na=False)
    rejected = df.loc[~valid, ["cod_ibge", "municipio_sinisa"]].copy()
    df = df.loc[valid].copy()
    assert not df["cod_ibge"].duplicated().any(), f"Município duplicado em {path}"
    assert len(df) == 5570, f"Universo municipal inesperado em {path}: {len(df)}"
    dictionary = []
    for code, (name, unit) in FIELDS.items():
        if code in df:
            description = str(top[11 if indicators else 10][headers.index(code)]).strip()
            dictionary.append({"coluna": name, "fonte": "SINISA", "codigo_original": code,
                               "descricao": description, "unidade": unit,
                               "arquivo": path.name, "aba": sheet.title})
    report = {"arquivo": path.name, "linhas_lidas_apos_cabecalho": n_read,
              "linhas_sem_chave_removidas": len(rejected), "municipios": len(df),
              "respondentes": int(df.respondeu_sinisa.eq("Sim").sum()), "sha256": sha256(path)}
    return df, report, dictionary


def ratio(numerator: pd.Series, denominator: pd.Series, scale: float = 1) -> pd.Series:
    return (numerator / denominator.where(denominator > 0) * scale).replace([np.inf, -np.inf], np.nan)


def run(ibge_path: Path | None = None) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    EVID.mkdir(parents=True, exist_ok=True)
    zip_path = RAW / "SINISA_RESIDUOS_planilhas_2024.zip"
    extracted = RAW / "sinisa_extraido"
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if not (extracted / member.filename).resolve().is_relative_to(extracted.resolve()):
                raise ValueError("Caminho inseguro no ZIP")
        archive.extractall(extracted)
    reports, dictionary = [], []
    base = None
    for pattern, indicators in [("*Indicadores*.xlsx", True), ("*Despesas*.xlsx", False),
                                ("*Formulario_Manejo*.xlsx", False), ("*Cobertura*.xlsx", False)]:
        path = next(extracted.rglob(pattern))
        df, report, entries = sinisa_table(path, indicators)
        reports.append(report)
        dictionary.extend(entries)
        if base is None:
            base = df[["cod_ibge", "municipio_sinisa", "uf_sinisa", "regiao", "respondeu_sinisa", "populacao_base_sinisa"]].copy()
        else:
            assert set(base.cod_ibge) == set(df.cod_ibge), "Cobertura municipal diferente entre formulários"
            joined = base[["cod_ibge", "respondeu_sinisa"]].merge(df[["cod_ibge", "respondeu_sinisa"]], on="cod_ibge", validate="one_to_one")
            assert joined.respondeu_sinisa_x.equals(joined.respondeu_sinisa_y)
        selected = [c for c in FIELDS if c in df]
        for col in selected:
            raw = df[col].replace({"null": None, "": None, "-": None})
            converted = pd.to_numeric(raw, errors="coerce")
            unexpected = raw.notna() & converted.isna()
            assert not unexpected.any(), f"Valor numérico não reconhecido em {col}"
            df[col] = converted
            assert df.loc[df.respondeu_sinisa.ne("Sim"), col].isna().all(), f"Não respondente com valor em {col}"
        base = base.merge(df[["cod_ibge"] + selected].rename(columns={c: FIELDS[c][0] for c in selected}), on="cod_ibge", validate="one_to_one")
    assert base is not None
    ibge_path = ibge_path or OUT / "ibge_populacao_municipios_2024.csv"
    pop = pd.read_csv(ibge_path, dtype={"cod_ibge": str})
    assert pop.cod_ibge.str.fullmatch(r"\d{7}").all() and not pop.cod_ibge.duplicated().any()
    assert pop.populacao_2024.gt(0).all() and pop.ano.eq(2024).all()
    population_unmatched = pop.loc[~pop.cod_ibge.isin(base.cod_ibge)].copy()
    population_unmatched.to_csv(EVID / "ibge_sem_municipio_sinisa.csv", index=False, encoding="utf-8-sig")
    # Left join: mantém não respondentes, em vez de ocultar ausência de resposta.
    base = base.merge(pop.drop(columns=["ano"]).rename(columns={"municipio": "municipio", "populacao_2024": "populacao_ibge_2024"}), on="cod_ibge", how="left", validate="one_to_one", indicator="juncao_ibge")
    assert base.juncao_ibge.eq("both").all(), "Há municípios SINISA sem correspondência IBGE"
    assert base.uf_sinisa.eq(base.uf).all(), "UFs inconsistentes na junção"
    base = base.drop(columns=["juncao_ibge", "uf_sinisa"])
    base.insert(1, "ano", 2024)
    base["populacao_base_sinisa"] = pd.to_numeric(base.populacao_base_sinisa, errors="raise")
    base["diferenca_populacao_sinisa_ibge"] = base.populacao_base_sinisa - base.populacao_ibge_2024
    base["despesa_manejo_por_hab_ibge2024"] = ratio(base.despesa_exploracao_manejo_rs_ano, base.populacao_ibge_2024)
    # Escopo inclui manejo como um todo. Não rotular como preço da coleta.
    base["despesa_manejo_por_t_rsu"] = ratio(base.despesa_exploracao_manejo_rs_ano, base.massa_rsu_coletada_t_ano)
    base["recuperacao_total_calculada_pct"] = ratio(base.massa_recuperada_secos_organicos_t_ano, base.massa_rsu_coletada_t_ano, 100)
    base["cobertura_coleta_ibge2024_pct"] = ratio(base.populacao_coberta_coleta_sinisa, base.populacao_ibge_2024, 100)
    base["cobertura_seletiva_ibge2024_pct"] = ratio(base.populacao_coberta_seletiva_sinisa, base.populacao_ibge_2024, 100)
    base["porte_populacional"] = pd.cut(base.populacao_ibge_2024, [0, 20000, 50000, 100000, 500000, float("inf")], labels=["até 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "mais de 500 mil"], right=True)
    rais_reports = []
    rais_present = pd.Series(False, index=base.index)
    for filename, valuecol in [("rais_residuos_municipios_2024.csv", "vinculos_cnae38_3112"),
                               ("rais_vinculos_totais_municipios_2024.csv", "vinculos_formais_totais_3112")]:
        rais_file = OUT / filename
        if not rais_file.exists():
            continue
        rais = pd.read_csv(rais_file, dtype={"cod_ibge": str})
        required = {"cod_ibge", "ano", valuecol}
        assert required.issubset(rais.columns), "Agregado RAIS sem campos obrigatórios"
        assert len(rais) > 0 and rais.ano.eq(2024).all()
        assert rais.cod_ibge.str.fullmatch(r"\d{7}", na=False).all(), "RAIS deve ter códigos IBGE de sete dígitos auditados"
        assert not rais.cod_ibge.duplicated().any()
        measures = [valuecol]
        if valuecol == "vinculos_cnae38_3112":
            measures += [c for c in ["vinculos_coleta_381_3112", "vinculos_tratamento_382_3112", "vinculos_recuperacao_383_3112", "estabelecimentos_cnae38_declarantes", "estabelecimentos_cnae38_com_vinculos_3112"] if c in rais]
        for measure in measures:
            rais[measure] = pd.to_numeric(rais[measure], errors="raise")
            values = rais[measure].dropna()
            assert len(values) > 0 and values.ge(0).all() and values.mod(1).eq(0).all(), "Contagens RAIS devem ser inteiras não negativas"
        unmatched = rais.loc[~rais.cod_ibge.isin(base.cod_ibge)]
        unmatched.to_csv(EVID / (rais_file.stem + "_sem_correspondencia.csv"), index=False, encoding="utf-8-sig")
        assert unmatched.empty, "RAIS com município fora do universo; revisar territorialização antes de integrar"
        base = base.merge(rais[["cod_ibge"] + measures], on="cod_ibge", how="left", validate="one_to_one")
        matched = base[valuecol].notna()
        assert matched.any(), "Nenhum dado RAIS efetivamente pareado"
        rais_present |= matched
        rais_reports.append({"arquivo": filename, "variavel": valuecol, "linhas": len(rais), "municipios_com_valor_pareado": int(matched.sum()), "sha256": sha256(rais_file)})
    rais_integrada = bool(rais_present.any())
    # A RAIS complementar já lista Boa Esperança do Norte; SINISA/IBGE DOU
    # mantêm o território anterior. Não redistribuir seus vínculos por população.
    territorial_rais = base.cod_ibge.isin(["5106240", "5106307", "5107925", "5108501"]) & rais_present
    if rais_integrada:
        base["flag_compatibilidade_territorial_rais"] = territorial_rais
    if "vinculos_cnae38_3112" in base:
        base["vinculos_residuos_por_1000_hab"] = ratio(base.vinculos_cnae38_3112, base.populacao_ibge_2024, 1000).where(~territorial_rais)
        base["vinculos_recuperacao_383_por_1000_hab"] = ratio(base.vinculos_recuperacao_383_3112, base.populacao_ibge_2024, 1000).where(~territorial_rais)
        base["status_rais"] = np.where(base.vinculos_cnae38_3112.notna(), "CNAE 38 disponível; aproximação setorial de emprego", "CNAE 38 ausente")
        if "vinculos_formais_totais_3112" in base:
            assert base.vinculos_cnae38_3112.le(base.vinculos_formais_totais_3112).all()
            base["participacao_cnae38_no_emprego_formal_pct"] = ratio(base.vinculos_cnae38_3112, base.vinculos_formais_totais_3112, 100)
    elif "vinculos_formais_totais_3112" in base:
        base["vinculos_formais_totais_por_1000_hab"] = ratio(base.vinculos_formais_totais_3112, base.populacao_ibge_2024, 1000).where(~territorial_rais)
        base["status_rais"] = np.where(rais_present, "total de todos os setores; recorte resíduos pendente", "ausente; recorte resíduos pendente")
    else:
        base["status_rais"] = "pendente de extração municipal setorial"
    if "vinculos_formais_totais_3112" in base:
        base["vinculos_formais_totais_por_1000_hab"] = ratio(base.vinculos_formais_totais_3112, base.populacao_ibge_2024, 1000).where(~territorial_rais)
    base["fontes_integradas"] = np.where(rais_present, "SINISA;IBGE;RAIS", "SINISA;IBGE")

    # Sinalizar inconsistências. Preservar valores originais para auditoria.
    checks = pd.DataFrame({"cod_ibge": base.cod_ibge, "ano": base.ano})
    for col in [c for c in base if c.endswith("_pct")]:
        checks[col + "_fora_0_100"] = base[col].notna() & ~base[col].between(0, 100)
    checks["despesa_manejo_nao_positiva"] = base.despesa_exploracao_manejo_rs_ano.notna() & base.despesa_exploracao_manejo_rs_ano.le(0)
    checks["massa_rsu_nao_positiva"] = base.massa_rsu_coletada_t_ano.notna() & base.massa_rsu_coletada_t_ano.le(0)
    checks["massa_rsu_difere_domiciliar_mais_limpeza"] = (base.massa_rsu_coletada_t_ano - base.massa_domiciliar_coletada_t_ano - base.massa_limpeza_urbana_t_ano).abs().gt(0.05)
    calc = base.recuperacao_total_calculada_pct
    official = base.recuperacao_total_sinisa_oficial_pct
    checks["recuperacao_diverge_oficial_mais_0_02_pp"] = calc.notna() & official.notna() & (calc - official).abs().gt(0.02)
    base["flag_qualidade"] = checks.iloc[:, 2:].any(axis=1)
    # Amostra válida por pergunta; não exigir completude de todas as colunas.
    base["apta_analise_custo_recuperacao"] = (base.respondeu_sinisa.eq("Sim") & base.despesa_exploracao_manejo_rs_ano.gt(0) & base.massa_rsu_coletada_t_ano.gt(0) & calc.between(0, 100) & ~base.flag_qualidade)
    assert not base[["cod_ibge", "ano"]].duplicated().any()
    assert len(base) == 5570
    assert not np.isinf(base.select_dtypes(include="number").to_numpy(dtype=float)).any()
    base.to_csv(OUT / "saneamento_municipios_2024_parcial.csv", index=False, encoding="utf-8-sig")
    checks.to_csv(EVID / "validacoes_por_municipio.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(dictionary).to_csv(ROOT / "docs/dicionario_sinisa.csv", index=False, encoding="utf-8-sig")
    summary = {"executado_em_utc": datetime.now(timezone.utc).isoformat(), "ano": 2024,
               "status": "parcial", "fontes_realmente_integradas": ["SINISA", "IBGE"] + (["RAIS"] if rais_integrada else []),
               "linhas": len(base), "colunas": len(base.columns), "municipios_unicos": base.cod_ibge.nunique(), "rais_agregados": rais_reports,
               "municipios_rais_com_revisao_territorial_pendente": int(territorial_rais.sum()),
               "respondentes_sinisa": int(base.respondeu_sinisa.eq("Sim").sum()),
               "nao_respondentes_sinisa": int(base.respondeu_sinisa.ne("Sim").sum()),
               "linhas_ibge_arquivo": len(pop), "registros_ibge_sem_correspondencia_sinisa": len(population_unmatched),
               "diferencas_populacao_sinisa_ibge": int(base.diferenca_populacao_sinisa_ibge.ne(0).sum()),
               "municipios_com_alerta_qualidade": int(base.flag_qualidade.sum()),
               "amostra_inicial_custo_recuperacao": int(base.apta_analise_custo_recuperacao.sum()),
               "alertas_por_regra": {c: int(checks[c].sum()) for c in checks.columns[2:]},
               "nao_nulos_por_coluna": {c: int(base[c].notna().sum()) for c in base},
               "sinisa_formularios": reports,
               "sha256_dataset": sha256(OUT / "saneamento_municipios_2024_parcial.csv")}
    (EVID / "validacoes_etl.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ibge", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.ibge), ensure_ascii=False, indent=2))
