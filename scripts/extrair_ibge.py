"""Extrai a estimativa oficial IBGE 2024 sem dependências externas.

Uso: python extrair_ibge.py [--versao tcu|dou] [--download] [--diretorio CAMINHO]
A opção --download consulta exclusivamente a URL oficial declarada abaixo.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SOURCE_PAGE = "https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/"
VERSIONS = {
    "tcu": {"filename": "POP2024_20241230.ods", "date": "2024-12-30", "rows": 5571},
    "dou": {"filename": "estimativa_dou_2024.ods", "date": "2024-08-29", "rows": 5570},
}
NS = {"table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
      "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
      "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0"}


def expanded_row(row: ET.Element, limit: int = 8) -> list[dict[str, str]]:
    """Expande somente as primeiras colunas úteis; evita 16 mil vazias no ODS."""
    cells: list[dict[str, str]] = []
    for cell in row:
        if cell.tag not in {f"{{{NS['table']}}}table-cell", f"{{{NS['table']}}}covered-table-cell"}:
            continue
        repeat = int(cell.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
        value = cell.get(f"{{{NS['office']}}}value", "")
        text = "\n".join("".join(p.itertext()) for p in cell.findall("text:p", NS))
        cells.extend([{"text": text, "value": value}] * min(repeat, limit - len(cells)))
        if len(cells) == limit:
            break
    return cells


def extract(directory: Path, version: str = "tcu") -> dict:
    spec = VERSIONS[version]
    raw_path = directory / spec["filename"]
    data = raw_path.read_bytes()
    with zipfile.ZipFile(raw_path) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    tables = root.findall(".//table:table", NS)
    if len(tables) != 2:
        raise ValueError(f"Esperadas 2 abas IBGE; encontradas {len(tables)}")

    records = []
    notes = []
    for row in tables[1].findall("table:table-row", NS):
        cells = expanded_row(row)
        texts = [c["text"].strip() for c in cells]
        if len(cells) < 5 or texts[0] == "UF" or not re.fullmatch(r"[A-Z]{2}", texts[0]):
            if texts and (texts[0].startswith("(") or texts[0].startswith("Fonte:") or texts[0] == "Notas:"):
                notes.append(texts[0])
            continue
        uf, cod_uf, cod_mun, municipio = texts[:4]
        if not re.fullmatch(r"\d{2}", cod_uf) or not re.fullmatch(r"\d{5}", cod_mun):
            raise ValueError(f"Código municipal inválido: {texts[:4]}")
        if cells[4]["value"]:
            pop_value = float(cells[4]["value"])
            if not pop_value.is_integer():
                raise ValueError(f"População não inteira: {municipio}")
            population = int(pop_value)
        else:
            # Apenas número principal; chamadas de notas não viram população.
            match = re.fullmatch(r"([\d.]+)\s*(\([^)]*\))*", texts[4])
            if match is None:
                raise ValueError(f"População não reconhecida: {texts[4]}")
            population = int(match.group(1).replace(".", ""))
        footnotes = " ".join(t for t in texts[5:] if t)
        footnotes_in_number = " ".join(re.findall(r"\([^)]*\)", texts[4]))
        footnotes = " ".join(x for x in [footnotes_in_number, footnotes] if x)
        records.append({"cod_ibge": cod_uf + cod_mun, "municipio": municipio,
                        "uf": uf, "populacao_2024": population, "ano": 2024,
                        "notas_ibge": footnotes, "versao_ibge": spec["date"]})

    national_rows = [expanded_row(row) for row in tables[0].findall("table:table-row", NS)]
    national = next(int(float(row[1]["value"])) for row in national_rows
                    if len(row) > 1 and row[0]["text"] == "Brasil")
    codes = [r["cod_ibge"] for r in records]
    checks = {
        "linhas": len(records), "municipios_unicos": len(set(codes)),
        "ufs_distintas": len({r["uf"] for r in records}),
        "codigos_7_digitos": all(re.fullmatch(r"\d{7}", code) is not None for code in codes),
        "populacao_positiva": all(r["populacao_2024"] > 0 for r in records),
        "soma_populacao_municipal": sum(r["populacao_2024"] for r in records),
        "populacao_brasil_aba_oficial": national,
        "municipios_com_notas": sum(bool(r["notas_ibge"]) for r in records),
    }
    checks["soma_confere_brasil"] = checks["soma_populacao_municipal"] == national
    assert checks["linhas"] == spec["rows"], checks
    assert checks["municipios_unicos"] == spec["rows"], checks
    assert checks["ufs_distintas"] == 27, checks
    assert all(checks[k] for k in ["codigos_7_digitos", "populacao_positiva", "soma_confere_brasil"]), checks

    suffix = f"{version}_{spec['date'].replace('-', '')}"
    out = directory / f"ibge_populacao_municipios_2024_{suffix}.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (directory / f"notas_originais_ibge_{suffix}.txt").write_text("\n\n".join(notes), encoding="utf-8")
    metadata = {
        "fonte": "IBGE / DPE / COPIS — Estimativas da População 2024",
        "url_arquivo": SOURCE_PAGE + spec["filename"], "url_pagina": SOURCE_PAGE,
        "data_referencia": "2024-07-01", "versao": spec["date"],
        "processado_em_utc": datetime.now(timezone.utc).isoformat(),
        "arquivo_original": spec["filename"], "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "arquivo_limpo": out.name, "validacoes": checks,
        "decisao_notas": "Usada a coluna POPULAÇÃO ESTIMADA da tabela. Chamadas de notas judiciais preservadas em notas_ibge; valores citados nas notas não substituem a estimativa.",
        "alerta_territorial": "TCU revisado inclui Boa Esperança do Norte 5101837 (instalação 01/01/2025) e redistribui população dos municípios doadores em MT; DOU original conserva 5.570 registros. Compatibilizar território antes de usar taxas municipais.",
    }
    (directory / f"ibge_metadados_validacoes_{suffix}.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--versao", choices=VERSIONS, default="tcu")
    parser.add_argument("--diretorio", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.diretorio.mkdir(parents=True, exist_ok=True)
    if args.download:
        spec = VERSIONS[args.versao]
        request = urllib.request.Request(SOURCE_PAGE + spec["filename"], headers={"User-Agent": "A3-UNIFACS/1.0 (academic data analysis)"})
        with urllib.request.urlopen(request, timeout=90) as response:
            (args.diretorio / spec["filename"]).write_bytes(response.read())
    print(json.dumps(extract(args.diretorio, args.versao), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
