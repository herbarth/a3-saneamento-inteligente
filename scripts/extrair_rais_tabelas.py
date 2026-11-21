"""Extrai estoque RAIS 2024 de todos os setores; não mede empregos verdes.

Fonte: MTE, RAIS Complementar - Tabelas 2023x2024, TABELA 4.
O código municipal de seis dígitos é ligado ao prefixo único de cod_ibge.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
from collections import Counter
import openpyxl

SOURCE_URL = 'https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1/rais-complementar-tabelas-2023x2024.xlsx'
ROOT = Path(__file__).resolve().parents[1]


def metadata_path(path):
    """Identifica arquivos sem publicar o caminho do perfil da execução."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.name


def extract(raw_path, ibge_csv, output_dir):
    raw_path, ibge_csv, output_dir = map(Path, (raw_path, ibge_csv, output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)
    with ibge_csv.open(encoding='utf-8-sig', newline='') as f:
        ibge = list(csv.DictReader(f))
    codes = [r['cod_ibge'] for r in ibge]
    assert all(len(c) == 7 and c.isdigit() for c in codes)
    counts = Counter(c[:6] for c in codes)
    assert all(n == 1 for n in counts.values()), 'Prefixos IBGE não são únicos'
    lookup = {r['cod_ibge'][:6]: r for r in ibge}
    wb = openpyxl.load_workbook(raw_path, read_only=True, data_only=True)
    sheet = wb['TABELA 4']
    assert sheet.cell(14, 26).value == 2024
    assert sheet.cell(13, 25).value == 'Total'
    records, unmatched, sector_errors = [], [], []
    for row_number, row in enumerate(sheet.iter_rows(values_only=True), 1):
        code = row[2]
        if not isinstance(code, int):
            continue
        code = str(code).zfill(6)
        total = row[25]
        assert isinstance(total, (int, float)) and total >= 0 and int(total) == total
        sector_sum = sum(row[i] for i in (5, 9, 13, 17, 21))
        if sector_sum != total:
            sector_errors.append({'linha': row_number, 'codigo_6': code,
                                  'total_2024': int(total), 'soma_grandes_setores': int(sector_sum),
                                  'diferenca': int(total - sector_sum)})
        record = dict(cod_municipio_rais=code, uf_rais=row[1], municipio_rais=row[3],
                      ano=2024, vinculos_formais_totais_3112=int(total),
                      linha_origem_rais=row_number)
        if code not in lookup:
            unmatched.append(record)
            continue
        assert lookup[code]['uf'] == row[1], f'UF inconsistente: {code}'
        record = {'cod_ibge': lookup[code]['cod_ibge'], **record}
        records.append(record)
    assert len(records) == len(set(r['cod_ibge'] for r in records))
    assert {r['cod_ibge'] for r in records} == set(codes), 'Cobertura municipal incompleta'
    national = next(row[2] for row in wb['TABELA 1'].iter_rows(values_only=True) if row[1] == 2024)
    municipal_total = sum(r['vinculos_formais_totais_3112'] for r in records)
    unidentified = [r for r in unmatched if r['cod_municipio_rais'] == '999999']
    outside_geography = [r for r in unmatched if r['cod_municipio_rais'] != '999999']
    non_identified_total = sum(r['vinculos_formais_totais_3112'] for r in unidentified)
    outside_total = sum(r['vinculos_formais_totais_3112'] for r in outside_geography)
    assert municipal_total + non_identified_total + outside_total == national
    assert all(r['cod_municipio_rais'] == '510183' for r in outside_geography), 'Código novo não previsto; investigar antes de integrar'
    output_file = output_dir / 'rais_vinculos_totais_municipios_2024.csv'
    with output_file.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    metadata = {
        'fonte': 'MTE / RAIS 2024 divulgação complementar',
        'url': SOURCE_URL, 'arquivo': metadata_path(raw_path),
        'sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        'tabela': 'TABELA 4', 'cabecalhos_linhas': [13, 14],
        'colunas_excel': {'codigo_6': 'C', 'uf': 'B', 'total_2024': 'Z'},
        'chave': 'prefixo único de seis dígitos de cod_ibge; UF validada; sem ligação por nome',
        'municipios': len(records), 'ufs': len(set(r['uf_rais'] for r in records)),
        'soma_vinculos_municipais': municipal_total,
        'registros_sem_municipio': unidentified,
        'soma_nao_identificados': non_identified_total,
        'registros_fora_recorte_ibge': outside_geography,
        'soma_fora_recorte_ibge': outside_total,
        'estoque_brasil_tabela_1': national,
        'reconciliacao_total': municipal_total + non_identified_total + outside_total == national,
        'somas_cinco_grandes_setores_conferem': not sector_errors,
        'divergencias_soma_setorial_original': sector_errors,
        'decisao_soma_setorial': 'Preservado Total oficial da coluna Z. Divergências em relação aos cinco grupos foram registradas e não corrigidas; causa não confirmada.',
        'escopo': 'Estoque em 31/12/2024, todos os setores; vínculos, não pessoas únicas.',
        'limitacao': 'Variável contextual do mercado formal. Não representa empregos verdes nem CNAE 38. Não cobre trabalho informal. Recorte setorial dos microdados ainda pendente.',
        'csv': metadata_path(output_file),
    }
    (output_dir / 'rais_metadados_validacoes.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw_path')
    parser.add_argument('ibge_csv')
    parser.add_argument('output_dir')
    args = parser.parse_args()
    print(json.dumps(extract(args.raw_path, args.ibge_csv, args.output_dir), ensure_ascii=False, indent=2))
