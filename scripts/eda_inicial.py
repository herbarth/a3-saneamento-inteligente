"""EDA preliminar executável, sem inferência causal nem resultados de emprego verde."""
from pathlib import Path
import json
import os
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "evidencias/matplotlib_cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = ROOT / "analises"
OUT.mkdir(exist_ok=True)
df = pd.read_csv(ROOT / "data/processed/saneamento_municipios_2024_parcial.csv", dtype={"cod_ibge": str})
sample = df.loc[df.apta_analise_custo_recuperacao].copy()
columns = ["populacao_ibge_2024", "despesa_manejo_por_hab_ibge2024", "despesa_manejo_por_t_rsu", "recuperacao_total_calculada_pct", "cobertura_seletiva_sinisa_oficial_pct"]
if "vinculos_formais_totais_por_1000_hab" in sample:
    columns.append("vinculos_formais_totais_por_1000_hab")
description = sample[columns].describe(percentiles=[.25, .5, .75]).T
description.to_csv(OUT / "estatisticas_descritivas_preliminares.csv", encoding="utf-8-sig")
coverage = df.groupby("regiao", observed=True).agg(municipios=("cod_ibge", "size"), respondentes=("respondeu_sinisa", lambda v: v.eq("Sim").sum()))
coverage["resposta_pct"] = coverage.respondentes / coverage.municipios * 100
coverage.to_csv(OUT / "cobertura_respostas_por_regiao.csv", encoding="utf-8-sig")
sample.groupby("regiao", observed=True)[columns[1:]].median().to_csv(OUT / "medianas_municipais_por_regiao.csv", encoding="utf-8-sig")
# Spearman = Pearson nos postos médios; não precisa SciPy para o coeficiente.
sample[columns].rank(method="average").corr(method="pearson").to_csv(OUT / "correlacao_spearman_preliminar.csv", encoding="utf-8-sig")
present = sample[columns].notna().astype(int)
(present.T @ present).to_csv(OUT / "n_pares_correlacao.csv", encoding="utf-8-sig")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), layout="constrained")
color = "#12766B"
axes[0].hist(np.log10(sample.despesa_manejo_por_hab_ibge2024), bins=40, color=color, edgecolor="white")
axes[0].set(xlabel="log10 da despesa de manejo (R$/hab.ano)", ylabel="Número de municípios", title="Distribuição de despesas")
regions = sorted(sample.regiao.unique())
axes[1].boxplot([sample.loc[sample.regiao.eq(r), "despesa_manejo_por_hab_ibge2024"] for r in regions], tick_labels=regions, showfliers=False)
axes[1].tick_params(axis="x", rotation=30)
axes[1].set(ylabel="R$/habitante.ano", title="Dispersão por região")
axes[1].text(.03, .97, "Pontos extremos preservados na base;\nocultados apenas neste box plot.", transform=axes[1].transAxes, va="top", fontsize=8)
axes[2].scatter(sample.despesa_manejo_por_hab_ibge2024, sample.recuperacao_total_calculada_pct, s=8, alpha=.25, color=color, linewidths=0)
axes[2].set(xscale="log", xlabel="Despesa de manejo (R$/hab.ano; escala log)", ylabel="Recuperação de secos + orgânicos (%)", title="Associação a investigar")
fig.suptitle(f"Resíduos sólidos | Brasil, 2024 | EDA preliminar, n = {len(sample):,}".replace(",", "."), fontsize=15, fontweight="bold")
fig.supxlabel("Fontes: SINISA 2025 (referência 2024) + IBGE 2024. Amostra municipal com dados e verificações iniciais; não representa censo de desempenho.", fontsize=9)
fig.savefig(OUT / "eda_preliminar.png", dpi=180)
plt.close(fig)
summary = {"amostra_municipios": len(sample), "universo_territorial": len(df),
           "mediana_despesa_manejo_rs_hab_ano": float(sample.despesa_manejo_por_hab_ibge2024.median()),
           "mediana_recuperacao_secos_organicos_pct": float(sample.recuperacao_total_calculada_pct.median()),
           "municipios_amostra_recuperacao_zero": int(sample.recuperacao_total_calculada_pct.eq(0).sum()),
           "observacoes_por_variavel": {c: int(sample[c].notna().sum()) for c in columns},
           "interpretacao": "Estatísticas municipais não ponderadas. Ausência de resposta não foi convertida em zero. Recuperação inclui orgânicos conforme definição SINISA. Correlações são exploratórias, sem prova de causalidade ou de geração de empregos."}
(OUT / "resumo_eda_preliminar.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
