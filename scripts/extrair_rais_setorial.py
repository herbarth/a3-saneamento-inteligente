"""Agrega microdados oficiais RAIS Estabelecimentos 2024 por município/CNAE 38.

Publica saída apenas após reconciliação com o estoque e o número de declarantes
da divulgação complementar 2024. Não identifica pessoas nem empregadores.
"""
from pathlib import Path
from collections import Counter
import argparse
import csv
import hashlib
import json
import re
import time
import unicodedata
import pandas as pd


def normalizar(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', value.lower())


def sha256(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def extract(raw_path, ibge_csv, output_dir, evidence_dir, total_csv=None):
    started = time.monotonic()
    raw_path, ibge_csv, output_dir, evidence_dir = map(Path, (raw_path, ibge_csv, output_dir, evidence_dir))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with raw_path.open('rb') as source:
        sample = source.read(128 * 1024)
    try:
        sample_text = sample.decode('utf-8-sig')
        encoding = 'utf-8-sig'
    except UnicodeDecodeError:
        sample_text, encoding = sample.decode('cp1252'), 'cp1252'
    dialect = csv.Sniffer().sniff(sample_text[:sample_text.rfind('\n')], delimiters=',;\t')
    header = next(csv.reader(sample_text.splitlines(), dialect=dialect))
    normalized = {normalizar(name): name for name in header}
    wanted = ['municipiocodigo', 'cnae20classecodigo', 'cnae20subclassecodigo', 'qtdvinculosativos']
    assert all(name in normalized for name in wanted), f'Cabeçalhos inesperados: {header}'
    selected = [normalized[name] for name in wanted]
    ibge = pd.read_csv(ibge_csv, dtype={'cod_ibge': str})
    ibge['codigo6'] = ibge.cod_ibge.str[:6]
    assert ibge.codigo6.is_unique and ibge.cod_ibge.str.fullmatch(r'\d{7}').all()
    ibge_lookup = dict(zip(ibge.codigo6, ibge.cod_ibge))
    stock, sector_stock, missing_cnae_municipal = Counter(), Counter(), Counter()
    sectors = {group: Counter() for group in ('381', '382', '383')}
    estab_declarantes, estab_com_vinculos = Counter(), Counter()
    observed_cnae38 = Counter()
    original_class_lengths, original_subclass_lengths = Counter(), Counter()
    class_subclass_mismatches = 0
    rows_total, stock_total, missing_cnae_rows, missing_cnae_stock = 0, 0, 0, 0
    for number, chunk in enumerate(pd.read_csv(raw_path, sep=dialect.delimiter, encoding=encoding,
            dtype=str, keep_default_na=False, usecols=selected, chunksize=250_000), 1):
        chunk.columns = [normalizar(name) for name in chunk.columns]
        code = chunk['municipiocodigo'].str.strip()
        original_class = chunk['cnae20classecodigo'].str.strip()
        subclass = chunk['cnae20subclassecodigo'].str.strip()
        original_class_lengths.update(original_class.str.len().value_counts().to_dict())
        original_subclass_lengths.update(subclass.str.len().value_counts().to_dict())
        class_subclass_mismatches += int(original_class.ne(subclass).sum())
        active = chunk['qtdvinculosativos'].str.strip()
        assert code.str.fullmatch(r'\d{6}').all(), 'Código municipal inválido'
        assert active.str.fullmatch(r'\d+').all(), 'Estoque inválido'
        active = active.astype('int64')
        assert active.ge(0).all()
        assert subclass.str.fullmatch(r'\d{7}').all(), 'CNAE subclasse fora do formato esperado'
        cnae = subclass.str[:5]
        frame = pd.DataFrame({'codigo6': code, 'cnae': cnae, 'ativos': active})
        stock.update(frame.groupby('codigo6').ativos.sum().to_dict())
        selected_frame = frame[cnae.str.startswith('38')]
        assert selected_frame.cnae.isin(['38114', '38122', '38211', '38220', '38319', '38327', '38394']).all()
        sector_stock.update(selected_frame.groupby('codigo6').ativos.sum().to_dict())
        estab_declarantes.update(selected_frame.groupby('codigo6').size().to_dict())
        estab_com_vinculos.update(selected_frame[selected_frame.ativos.gt(0)].groupby('codigo6').size().to_dict())
        observed_cnae38.update(selected_frame.cnae.value_counts().to_dict())
        for group in sectors:
            sectors[group].update(selected_frame[selected_frame.cnae.str.startswith(group)].groupby('codigo6').ativos.sum().to_dict())
        missing = frame.cnae.eq('00000')
        missing_cnae_rows += int(missing.sum())
        missing_cnae_stock += int(frame.loc[missing, 'ativos'].sum())
        missing_cnae_municipal.update(frame.loc[missing].groupby('codigo6').ativos.sum().to_dict())
        rows_total += len(frame)
        stock_total += int(frame.ativos.sum())
        progress = {'bloco': number, 'linhas': rows_total, 'estoque': stock_total,
                    'segundos': round(time.monotonic() - started, 1)}
        (evidence_dir / 'rais_setorial_progresso.json').write_text(json.dumps(progress), encoding='utf-8')
        print(json.dumps(progress), flush=True)
    # Confirma que o arquivo completo corresponde à divulgação complementar.
    assert rows_total == 13_186_059, f'Declarantes não reconciliam: {rows_total}'
    assert stock_total == 57_132_156, f'Estoque não reconcilia: {stock_total}'
    extras = sorted(set(stock) - set(ibge_lookup))
    assert set(extras).issubset({'999999', '510183'}), f'Municípios não previstos: {extras}'
    assert set(ibge_lookup).issubset(stock), 'Município IBGE não observado no arquivo completo'
    total_comparison = []
    if total_csv:
        table = pd.read_csv(total_csv, dtype={'cod_municipio_rais': str})
        for record in table.itertuples(index=False):
            code = record.cod_municipio_rais
            observed = stock[code]
            expected = int(record.vinculos_formais_totais_3112)
            if observed != expected:
                total_comparison.append({'codigo6': code, 'estoque_microdados': observed, 'estoque_tabela': expected})
        assert not total_comparison, f'{len(total_comparison)} totais municipais divergem da tabela oficial'
    records = []
    for record in ibge.itertuples(index=False):
        code = record.codigo6
        values = dict(cod_ibge=record.cod_ibge, ano=2024,
            vinculos_cnae38_3112=int(sector_stock[code]),
            vinculos_coleta_381_3112=int(sectors['381'][code]),
            vinculos_tratamento_382_3112=int(sectors['382'][code]),
            vinculos_recuperacao_383_3112=int(sectors['383'][code]),
            estabelecimentos_cnae38_declarantes=int(estab_declarantes[code]),
            estabelecimentos_cnae38_com_vinculos_3112=int(estab_com_vinculos[code]))
        assert values['vinculos_cnae38_3112'] <= stock[code]
        assert sum(values[f'vinculos_{label}_{group}_3112'] for label, group in
                   [('coleta', '381'), ('tratamento', '382'), ('recuperacao', '383')]) == values['vinculos_cnae38_3112']
        records.append(values)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / 'rais_residuos_municipios_2024.csv'
    pd.DataFrame(records).to_csv(destination, index=False, encoding='utf-8-sig')
    metadata = {
        'arquivo': str(raw_path), 'sha256': sha256(raw_path), 'bytes': raw_path.stat().st_size,
        'encoding': encoding, 'delimitador': dialect.delimiter, 'cabecalho': header,
        'colunas_utilizadas': selected, 'linhas_lidas': rows_total,
        'estoque_nacional_todos_setores': stock_total,
        'estoque_nacional_cnae38': sum(sector_stock.values()),
        'estoque_grupos_nacional': {group: sum(value.values()) for group, value in sectors.items()},
        'estabelecimentos_cnae38_declarantes_nacional': sum(estab_declarantes.values()),
        'estabelecimentos_cnae38_com_vinculos_nacional': sum(estab_com_vinculos.values()),
        'classes_cnae38_observadas': dict(observed_cnae38),
        'comprimentos_coluna_rotulada_classe': dict(original_class_lengths),
        'comprimentos_coluna_subclasse': dict(original_subclass_lengths),
        'registros_classe_diferente_subclasse': class_subclass_mismatches,
        'decisao_cnae': 'Utilizada a coluna Subclasse de sete dígitos. Classe derivada dos primeiros cinco; divisão dos primeiros dois; grupo dos primeiros três. A coluna rotulada Classe é inspecionada e não usada para classificação.',
        'estoque_cnae_ausente_00000': missing_cnae_stock, 'registros_cnae_ausente_00000': missing_cnae_rows,
        'estoque_cnae_00000_por_municipio': {code: int(value) for code, value in missing_cnae_municipal.items() if value > 0},
        'codigos_nao_pareados': [{'codigo6': code, 'estoque_total': stock[code],
            'estoque_cnae38': sector_stock[code]} for code in extras],
        'municipios_saida': len(records), 'municipios_cnae38_positivo': sum(r['vinculos_cnae38_3112'] > 0 for r in records),
        'municipios_totais_divergentes_tabela': total_comparison,
        'validacoes': {'estoque_e_declarantes_nacionais_reconciliados': True,
            'codigo_municipal_formato_valido': True, 'estoques_nao_negativos_inteiros': True,
            'cnae38_soma_grupos_confere': True, 'zeros_preenchidos_apos_leitura_completa': True},
        'escopo': 'Vínculos ativos31/12 em estabelecimentos CNAE2.0 divisão38. Aproximação setorial; não certifica emprego verde/decente, exclui informais e emprego em outros CNAEs.',
        'csv': str(destination), 'duracao_segundos': round(time.monotonic() - started, 1),
    }
    (evidence_dir / 'rais_setorial_metadados_validacoes.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw_path')
    parser.add_argument('ibge_csv')
    parser.add_argument('output_dir')
    parser.add_argument('evidence_dir')
    parser.add_argument('--total-csv')
    args = parser.parse_args()
    print(json.dumps(extract(args.raw_path, args.ibge_csv, args.output_dir, args.evidence_dir, args.total_csv), ensure_ascii=True, indent=2))
