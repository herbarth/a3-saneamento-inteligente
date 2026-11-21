"""Reproduz a extração das três fontes e o ETL; --download baixa arquivos oficiais.

Uso: python scripts/preparar_dados.py [--download]
"""
from pathlib import Path
import argparse
import shutil
import urllib.request
from extrair_ibge import extract
from extrair_rais_tabelas import extract as extract_rais
from etl import run

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--reprocessar-setorial", action="store_true", help="Baixa se necessário e relê os microdados RAIS de estabelecimentos (1,43 GB extraído)")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    sources = {
        "SINISA_RESIDUOS_planilhas_2024.zip": "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/SINISA_RESIDUOS_planilhas_2024.zip",
        "estimativa_dou_2024.ods": "https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/estimativa_dou_2024.ods",
        "rais-complementar-tabelas-2023x2024.xlsx": "https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1/rais-complementar-tabelas-2023x2024.xlsx",
    }
    if args.download:
        for name, url in sources.items():
            req = urllib.request.Request(url, headers={"User-Agent": "A3-UNIFACS/1.0"})
            with urllib.request.urlopen(req, timeout=90) as response:
                (RAW / name).write_bytes(response.read())
    meta = extract(RAW, "dou")
    processed = ROOT / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(RAW / meta["arquivo_limpo"], processed / "ibge_populacao_municipios_2024.csv")
    extract_rais(RAW / "rais-complementar-tabelas-2023x2024.xlsx", processed / "ibge_populacao_municipios_2024.csv", processed)
    evidence = ROOT / "evidencias"
    evidence.mkdir(exist_ok=True)
    shutil.copyfile(processed / "rais_metadados_validacoes.json", evidence / "rais_metadados_validacoes.json")
    if args.reprocessar_setorial:
        from obter_rais_setorial import run as run_setorial
        run_setorial()
    print(run())
