"""Teste funcional do dashboard usando os dados reais, sem serviço publicado."""
from pathlib import Path
import importlib.metadata
import json
import sys
from datetime import datetime, timezone

import pandas as pd
from streamlit.testing.v1 import AppTest

PROJECT = Path(__file__).resolve().parents[1]
df = pd.read_csv(PROJECT / "data/processed/saneamento_municipios_2024_parcial.csv", dtype={"cod_ibge": "string"})
report = {
    "executado_em_utc": datetime.now(timezone.utc).isoformat(),
    "metodo": "streamlit.testing.v1.AppTest; CSV real; sem publicação",
    "versoes": {p: importlib.metadata.version(p) for p in ("streamlit", "plotly", "pandas", "numpy")},
    "cenarios": [],
}


def check(app, name, count):
    errors = [e.message for e in app.exception]
    assert not errors, (name, errors)
    metrics = {m.label: m.value for m in app.metric}
    wanted = f"{count:,}".replace(",", ".")
    assert metrics["Municípios selecionados"] == wanted, (name, metrics)
    report["cenarios"].append({"cenario": name, "municipios_esperados": count, "municipios_exibidos": metrics["Municípios selecionados"], "excecoes": errors, "resultado": "aprovado"})
    print(name, count, "aprovado", flush=True)


app = AppTest.from_file(str(PROJECT / "app.py"), default_timeout=45).run()
check(app, "abertura nacional e todas as abas", len(df))
app.multiselect(key="regions").set_value(["Nordeste"]).run()
check(app, "filtro de região Nordeste", int(df["regiao"].eq("Nordeste").sum()))
app.multiselect(key="ufs").set_value(["BA"]).run()
ba = df[df["uf"].eq("BA")]
check(app, "região e UF Bahia", len(ba))
porte = "20 a 50 mil"
app.multiselect(key="portes").set_value([porte]).run()
ba_porte = ba[ba["porte_populacional"].eq(porte)]
check(app, "região UF e porte", len(ba_porte))
row = ba_porte.sort_values(["municipio", "uf"]).iloc[0]
app.selectbox(key="municipality").set_value(f"{row.municipio} / {row.uf} · {row.cod_ibge}").run()
check(app, "município individual", 1)
app.checkbox(key="quality").uncheck().run()
check(app, "alteração do critério de qualidade", 1)

# Novo estado: município não respondente, sem indicadores de despesas/recuperação.
app = AppTest.from_file(str(PROJECT / "app.py"), default_timeout=45).run()
row = df[df["respondeu_sinisa"].eq("Não")].iloc[0]
app.selectbox(key="municipality").set_value(f"{row.municipio} / {row.uf} · {row.cod_ibge}").run()
check(app, "não respondente sem preencher ausências", 1)
metrics = {m.label: m.value for m in app.metric}
assert metrics["Responderam ao SINISA"] == "0"
assert metrics["Não responderam"] == "1"
assert metrics["Por habitante residente"] == "Sem dados"

app = AppTest.from_file(str(PROJECT / "app.py"), default_timeout=45).run()
app.checkbox(key="cost_central").check().run()
check(app, "corte visual p1-p99 preserva universo", len(df))
app.checkbox(key="cost_log").uncheck().run()
app.radio(key="recovery_type").set_value("Apenas secos").run()
app.selectbox(key="recovery_x").set_value("DEX por tonelada coletada").run()
check(app, "controles de despesa recuperação e escala log", len(df))
assert app.get("download_button"), "Botão de download ausente"
report["resultado"] = "aprovado"
report["observacoes"] = [
    "AppTest executa todas as abas e transições verificadas; não substitui inspeção visual no navegador.",
    "Não foi publicado endereço externo nem testado acesso público nesta execução.",
]
path = PROJECT / "evidencias" / "testes_dashboard.json"
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(path, flush=True)
