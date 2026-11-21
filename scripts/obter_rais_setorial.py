"""Obtém o arquivo oficial RAIS 2024 e reproduz a agregação CNAE 38.

O arquivo compactado tem 140,7 MB; o texto extraído ocupa 1,43 GB.
Os agregados prontos já acompanham o projeto. Reprocessamento é opcional.
"""
from pathlib import Path
import argparse
import ftplib
import hashlib
import json
import py7zr
from extrair_rais_setorial import extract

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f5dbd564a8c9afa4242ecd48a9a112b184e0a1a3ffa2df0ff28051057ad1a267"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(archive_path=None, extracted_dir=None):
    archive_path = Path(archive_path or ROOT / "data/raw/RAIS_ESTAB_PUB_2024.7z")
    extracted_dir = Path(extracted_dir or ROOT / "data/raw/rais_setorial_extraido")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if not archive_path.exists():
        part = archive_path.with_suffix(".7z.part")
        offset = part.stat().st_size if part.exists() else 0
        with ftplib.FTP("ftp.mtps.gov.br", timeout=60, encoding="cp1252") as ftp:
            ftp.login()
            ftp.cwd("/pdet/microdados/RAIS/2024")
            with part.open("ab" if offset else "wb") as dest:
                ftp.retrbinary("RETR RAIS_ESTAB_PUB.7z", dest.write, blocksize=1024 * 1024, rest=offset or None)
        part.replace(archive_path)
    if digest(archive_path) != EXPECTED_SHA256:
        raise ValueError("O arquivo difere da versão oficial inspecionada. Conferir a revisão da fonte e atualizar o inventário antes de usar.")
    extracted_dir.mkdir(parents=True, exist_ok=True)
    text = extracted_dir / "RAIS_ESTAB_PUB.COMT"
    if not text.exists():
        with py7zr.SevenZipFile(archive_path) as archive:
            for name in archive.getnames():
                if not (extracted_dir / name).resolve().is_relative_to(extracted_dir.resolve()):
                    raise ValueError("Caminho inseguro no arquivo compactado")
            archive.extractall(extracted_dir)
    return extract(text, ROOT / "data/processed/ibge_populacao_municipios_2024.csv",
                   ROOT / "data/processed", ROOT / "evidencias",
                   ROOT / "data/processed/rais_vinculos_totais_municipios_2024.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path)
    parser.add_argument("--extraido", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.arquivo, args.extraido), ensure_ascii=False, indent=2))
