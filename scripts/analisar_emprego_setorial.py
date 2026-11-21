"""Descritivas e associações exploratórias RAIS/SINISA/IBGE, sem inferência causal."""
from pathlib import Path
import hashlib
import json
import os
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analises/emprego_setorial'
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'evidencias/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REGIONS = ['Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']
SIZES = ['até 20 mil', '20 a 50 mil', '50 a 100 mil', '100 a 500 mil', 'mais de 500 mil']
STOCK = 'vinculos_cnae38_3112'
REC_STOCK = 'vinculos_recuperacao_383_3112'
FORMAL = 'vinculos_formais_totais_3112'
RATE = 'vinculos_residuos_por_1000_hab'
REC_RATE = 'vinculos_recuperacao_383_por_1000_hab'
SHARE = 'participacao_cnae38_no_emprego_formal_pct'
REC_SHARE = 'participacao_recuperacao_383_no_emprego_formal_pct'
RECOVERY = ['recuperacao_secos_sinisa_oficial_pct', 'recuperacao_total_sinisa_oficial_pct']
LABELS = {RATE: 'CNAE 38 / mil hab.', REC_RATE: 'Recuperação 38.3 / mil hab.',
          SHARE: 'CNAE 38 / emprego formal (%)', REC_SHARE: 'Recuperação / emprego formal (%)',
          STOCK: 'Vínculos CNAE 38 (contagem)', REC_STOCK: 'Vínculos recuperação (contagem)',
          'populacao_ibge_2024': 'População municipal'}
SOURCE = ROOT / 'data/processed/saneamento_municipios_2024_parcial.csv'
df = pd.read_csv(SOURCE, dtype={'cod_ibge': str})
assert len(df) == 5570 and df.cod_ibge.is_unique
assert int(df[STOCK].sum()) == 265143
geo_ok = ~df.flag_compatibilidade_territorial_rais
assert int((~geo_ok).sum()) == 4
assert df.loc[~geo_ok, [RATE, REC_RATE]].isna().all().all()
df[REC_SHARE] = df[REC_STOCK].div(df[FORMAL].where(df[FORMAL].gt(0))).mul(100)
# As quatro unidades com mudança territorial ficam fora das associações,
# inclusive para shares; as contagens absolutas permanecem nas descritivas.
valid = df.apta_analise_custo_recuperacao & geo_ok
sample = df.loc[valid].copy()
sample['log10_populacao'] = np.log10(sample.populacao_ibge_2024)


def spearman(pair):
    if len(pair) < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return None
    return float(pair.iloc[:, 0].rank(method='average').corr(pair.iloc[:, 1].rank(method='average')))


def partial_spearman(frame, x, y):
    # Correlação de Pearson entre resíduos dos postos de x e y após regressão
    # linear nos postos de log(população); intercepto incluído em ambos.
    if len(frame) < 4 or frame[x].nunique() < 2 or frame[y].nunique() < 2:
        return None
    ranks = frame[[x, y, 'log10_populacao']].rank(method='average')
    control = np.column_stack([np.ones(len(ranks)), ranks.log10_populacao.to_numpy()])
    rx = ranks[x].to_numpy() - control @ np.linalg.lstsq(control, ranks[x].to_numpy(), rcond=None)[0]
    ry = ranks[y].to_numpy() - control @ np.linalg.lstsq(control, ranks[y].to_numpy(), rcond=None)[0]
    if np.std(rx) < 1e-12 or np.std(ry) < 1e-12:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def grouped(group):
    records = []
    for key, frame in df.groupby(group, observed=True, sort=False):
        rate_frame = frame.loc[~frame.flag_compatibilidade_territorial_rais]
        analytical = frame.loc[valid.loc[frame.index]]
        record = {group: key, 'municipios': len(frame), 'municipios_base_taxas': len(rate_frame),
            'populacao_base_taxas': int(rate_frame.populacao_ibge_2024.sum()),
            'vinculos_cnae38': int(frame[STOCK].sum()),
            'vinculos_coleta_381': int(frame.vinculos_coleta_381_3112.sum()),
            'vinculos_tratamento_382': int(frame.vinculos_tratamento_382_3112.sum()),
            'vinculos_recuperacao_383': int(frame[REC_STOCK].sum()),
            'vinculos_formais_totais': int(frame[FORMAL].sum()),
            'estabelecimentos_cnae38_declarantes': int(frame.estabelecimentos_cnae38_declarantes.sum()),
            'estabelecimentos_cnae38_com_vinculos': int(frame.estabelecimentos_cnae38_com_vinculos_3112.sum()),
            'municipios_cnae38_zero': int(frame[STOCK].eq(0).sum()),
            'municipios_recuperacao_383_zero': int(frame[REC_STOCK].eq(0).sum()),
            'municipios_cnae38_zero_pct': float(frame[STOCK].eq(0).mean() * 100),
            'municipios_recuperacao_383_zero_pct': float(frame[REC_STOCK].eq(0).mean() * 100),
            'municipios_sinisa_sem_resposta': int(frame.respondeu_sinisa.ne('Sim').sum()),
            'vinculos_cnae38_por_1000_hab_agregado': float(rate_frame[STOCK].sum() / rate_frame.populacao_ibge_2024.sum() * 1000),
            'vinculos_recuperacao_383_por_1000_hab_agregado': float(rate_frame[REC_STOCK].sum() / rate_frame.populacao_ibge_2024.sum() * 1000),
            'participacao_cnae38_formal_agregada_pct': float(frame[STOCK].sum() / frame[FORMAL].sum() * 100),
            'participacao_recuperacao_383_formal_agregada_pct': float(frame[REC_STOCK].sum() / frame[FORMAL].sum() * 100),
            'mediana_municipal_vinculos38_por_1000': float(frame[RATE].median()),
            'mediana_municipal_vinculos383_por_1000': float(frame[REC_RATE].median()),
            'n_amostra_associacoes': len(analytical),
            'mediana_recuperacao_secos_oficial_pct': float(analytical[RECOVERY[0]].median()) if len(analytical) else None,
            'mediana_recuperacao_total_oficial_pct': float(analytical[RECOVERY[1]].median()) if len(analytical) else None,
        }
        records.append(record)
    result = pd.DataFrame(records)
    if group == 'regiao':
        result[group] = pd.Categorical(result[group], REGIONS, ordered=True)
    elif group == 'porte_populacional':
        result[group] = pd.Categorical(result[group], SIZES, ordered=True)
    result = result.sort_values(group)
    result.to_csv(OUT / f'descritivas_por_{group}.csv', index=False, encoding='utf-8-sig')
    return result


by_region, by_size, by_uf = [grouped(group) for group in ('regiao', 'porte_populacional', 'uf')]
metrics = [STOCK, REC_STOCK, RATE, REC_RATE, SHARE, REC_SHARE, 'populacao_ibge_2024']
desc = df[[STOCK, REC_STOCK, RATE, REC_RATE, SHARE, REC_SHARE]].describe(percentiles=[.25, .5, .75, .9, .95, .99]).T
desc.to_csv(OUT / 'descritivas_municipais.csv', encoding='utf-8-sig')
correlations = []
for y in RECOVERY:
    for x in metrics:
        complete = sample[[x, y, 'log10_populacao']].dropna()
        masks = {'todos_validos': pd.Series(True, index=complete.index),
                 'recuperacao_positiva': complete[y].gt(0),
                 'vinculos_positivos': complete[x].gt(0),
                 'ambos_positivos': complete[x].gt(0) & complete[y].gt(0)}
        if x == 'populacao_ibge_2024':
            masks = {'todos_validos': masks['todos_validos'], 'recuperacao_positiva': masks['recuperacao_positiva']}
        for label, mask in masks.items():
            subset = complete.loc[mask]
            correlations.append({'emprego_ou_porte': x, 'indicador_recuperacao': y, 'amostra': label,
                'n': len(subset), 'rho_spearman': spearman(subset[[x, y]]),
                'rho_parcial_controlando_postos_log_pop': None if x == 'populacao_ibge_2024' else partial_spearman(subset, x, y),
                'municipios_emprego_zero': int(subset[x].eq(0).sum()),
                'municipios_recuperacao_zero': int(subset[y].eq(0).sum())})
corr = pd.DataFrame(correlations)
corr.to_csv(OUT / 'associacoes_spearman_com_n.csv', index=False, encoding='utf-8-sig')


def fetch_corr(metric, recovery=RECOVERY[0], subset='todos_validos'):
    record = corr.loc[corr.emprego_ou_porte.eq(metric) & corr.indicador_recuperacao.eq(recovery) & corr.amostra.eq(subset)].iloc[0]
    return {'rho': float(record.rho_spearman), 'rho_parcial_porte': float(record.rho_parcial_controlando_postos_log_pop) if pd.notna(record.rho_parcial_controlando_postos_log_pop) else None, 'n': int(record.n)}


summary = {'ano': 2024, 'universo_municipios': len(df), 'amostra_associacoes': len(sample),
    'municipios_excluidos_taxas_territorio': int((~geo_ok).sum()),
    'municipios_excluidos_sinisa_nao_resposta': int(df.respondeu_sinisa.ne('Sim').sum()),
    'municipios_excluidos_alerta_qualidade': int(df.flag_qualidade.sum()),
    'cnae38_vinculos_municipais': int(df[STOCK].sum()),
    'coleta381_vinculos_municipais': int(df.vinculos_coleta_381_3112.sum()),
    'tratamento382_vinculos_municipais': int(df.vinculos_tratamento_382_3112.sum()),
    'recuperacao383_vinculos_municipais': int(df[REC_STOCK].sum()),
    'cnae38_zero_municipios': int(df[STOCK].eq(0).sum()),
    'cnae38_zero_pct': float(df[STOCK].eq(0).mean() * 100),
    'recuperacao383_zero_municipios': int(df[REC_STOCK].eq(0).sum()),
    'recuperacao383_zero_pct': float(df[REC_STOCK].eq(0).mean() * 100),
    'cnae38_por1000_agregado_sem_4_mt': float(df.loc[geo_ok, STOCK].sum() / df.loc[geo_ok, 'populacao_ibge_2024'].sum() * 1000),
    'recuperacao383_por1000_agregado_sem_4_mt': float(df.loc[geo_ok, REC_STOCK].sum() / df.loc[geo_ok, 'populacao_ibge_2024'].sum() * 1000),
    'cnae38_participacao_formal_agregada_pct': float(df[STOCK].sum() / df[FORMAL].sum() * 100),
    'recuperacao383_participacao_formal_agregada_pct': float(df[REC_STOCK].sum() / df[FORMAL].sum() * 100),
    'associacoes_principais_secos': {metric: {subset: fetch_corr(metric, subset=subset) for subset in ['todos_validos', 'recuperacao_positiva', 'vinculos_positivos', 'ambos_positivos']} for metric in [RATE, REC_RATE, SHARE, REC_SHARE]},
    'associacoes_principais_total': {metric: {subset: fetch_corr(metric, RECOVERY[1], subset) for subset in ['todos_validos', 'recuperacao_positiva', 'vinculos_positivos', 'ambos_positivos']} for metric in [RATE, REC_RATE, SHARE, REC_SHARE]},
    'correlacao_contagens_para_comparar_efeito_porte': {metric: fetch_corr(metric) for metric in [STOCK, REC_STOCK, 'populacao_ibge_2024']},
    'metodo': 'Spearman por postos médios, pares completos, municípios com resposta SINISA, sem os dois alertas iniciais e sem quatro unidades MT com revisão territorial. Sensibilidades definidas por indicador/variável >0. Correlação parcial residualiza postos de X e Y nos postos de log10(população), com intercepto. Não foram calculados testes de hipótese ou previsões causais.',
    'limitacoes': ['CNAE é atividade principal do estabelecimento, não ocupação ou certificação de emprego verde.', 'RAIS exclui informais; zero não implica ausência de reciclagem ou de catadores.', 'Município do estabelecimento difere da área atendida por prestadores regionais e da residência dos trabalhadores.', 'SINISA mede serviços municipais; divisão38 abrange também resíduos industriais e perigosos.', 'Associar percentuais e taxas reduz o efeito do porte, mas não elimina confusão, viés de resposta, concentração regional ou endogeneidade.', 'Subamostras positivas são análises de sensibilidade com seleção diferente; não são mais representativas por definição.'],
    'sha256_dataset_entrada': hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
(OUT / 'resumo_diagnostico_setorial.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'amostra_associacoes': len(sample), 'taxa383_secos_todos': fetch_corr(REC_RATE), 'taxa383_secos_ambospositivos': fetch_corr(REC_RATE, subset='ambos_positivos'), 'share383_secos_todos': fetch_corr(REC_SHARE)}, ensure_ascii=True), flush=True)

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
palette = ['#137D83', '#658EBC', '#E4AA46']
fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), layout='constrained')
bottom = np.zeros(len(by_region))
for column, label, color in zip(['vinculos_coleta_381', 'vinculos_tratamento_382', 'vinculos_recuperacao_383'], ['Coleta 38.1', 'Tratamento 38.2', 'Recuperação 38.3'], palette):
    values = by_region[column].to_numpy() / 1000
    axes[0].bar(by_region.regiao.astype(str), values, bottom=bottom, label=label, color=color)
    bottom += values
axes[0].tick_params(axis='x', rotation=30)
axes[0].set(title='Onde estão os vínculos registrados', ylabel='Mil vínculos ativos em 31/12')
axes[0].legend(frameon=False, fontsize=8, loc='upper left')
positions = np.arange(len(by_size))
axes[1].barh(positions + .17, by_size.municipios_cnae38_zero_pct, height=.32, color=palette[0], label='Divisão 38')
axes[1].barh(positions - .17, by_size.municipios_recuperacao_383_zero_pct, height=.32, color=palette[2], label='Recuperação 38.3')
axes[1].set(yticks=positions, yticklabels=[f'{s}\n(n={n:,})'.replace(',', '.') for s, n in zip(by_size.porte_populacional.astype(str), by_size.municipios)], xlabel='Municípios com zero vínculos (%)', xlim=(0, 100), title='Zeros no registro formal, por porte')
axes[1].invert_yaxis()
axes[1].legend(frameon=False, fontsize=8, loc='lower right')
axes[2].scatter(sample[REC_RATE], sample[RECOVERY[0]], s=10, alpha=.28, color=palette[0], linewidths=0)
axes[2].set(xscale='symlog', xlabel='Vínculos em recuperação / mil hab.\n(escala simétrica log; inclui zero)', ylabel='Recuperação oficial de secos SINISA (%)', title='Emprego e desempenho municipal')
axes[2].set_xscale('symlog', linthresh=.03)
c = fetch_corr(REC_RATE)
axes[2].text(.98, .97, f"Spearman ρ = {c['rho']:.3f}\nn = {c['n']:,}".replace(',', '.'), transform=axes[2].transAxes, ha='right', va='top', fontsize=9)
fig.suptitle('Resíduos e recuperação de materiais | Brasil, 2024', fontsize=16, fontweight='bold')
fig.supxlabel('Fontes: RAIS 2024 + SINISA 2025 (ano-base 2024) + IBGE 2024. CNAE 38 é aproximação setorial; correlação não demonstra causalidade.', fontsize=9)
fig.savefig(OUT / 'panorama_emprego_setorial.png', dpi=180)
plt.close(fig)

metrics_plot = [RATE, REC_RATE, SHARE, REC_SHARE]
subsets = ['todos_validos', 'recuperacao_positiva', 'vinculos_positivos', 'ambos_positivos']
fig, axes = plt.subplots(1, 2, figsize=(15, 6.5), layout='constrained')
for axis, y, title in zip(axes, RECOVERY, ['Recuperação de secos (%)', 'Recuperação total: secos + orgânicos (%)']):
    matrix = np.array([[fetch_corr(x, y, subset)['rho'] for subset in subsets] for x in metrics_plot])
    last = axis.imshow(matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    axis.set(xticks=np.arange(4), xticklabels=['Todos\nválidos', 'Recuperação\n> 0', 'Vínculos\n> 0', 'Ambos\n> 0'], yticks=np.arange(4), yticklabels=[LABELS[x] for x in metrics_plot], title=title)
    axis.tick_params(length=0, pad=8)
    for row, x in enumerate(metrics_plot):
        for col, subset in enumerate(subsets):
            c = fetch_corr(x, y, subset)
            axis.text(col, row, f"ρ={c['rho']:.3f}\nn={c['n']:,}".replace(',', '.'), ha='center', va='center', fontsize=9)
fig.colorbar(last, ax=axes, shrink=.75, label='Spearman ρ', ticks=[-1, -.5, 0, .5, 1])
fig.suptitle('As associações mudam conforme a população de municípios analisada', fontsize=15, fontweight='bold')
fig.supxlabel('Pares completos; exclusões de qualidade e território descritas no relatório. Subamostras positivas mudam o recorte e não corrigem seleção.', fontsize=9)
fig.savefig(OUT / 'associacoes_emprego_recuperacao.png', dpi=180)
plt.close(fig)

ufs = by_uf.sort_values('vinculos_cnae38')
fig, axes = plt.subplots(1, 2, figsize=(12, 10), layout='constrained', sharey=True)
bottom = np.zeros(len(ufs))
for column, label, color in zip(['vinculos_coleta_381', 'vinculos_tratamento_382', 'vinculos_recuperacao_383'], ['Coleta', 'Tratamento', 'Recuperação'], palette):
    values = ufs[column].to_numpy() / 1000
    axes[0].barh(ufs.uf, values, left=bottom, label=label, color=color)
    bottom += values
axes[0].set(xlabel='Mil vínculos CNAE 38', title='Estoque por UF e grupo')
axes[0].legend(frameon=False, loc='lower right')
axes[1].barh(ufs.uf, ufs.vinculos_cnae38_por_1000_hab_agregado, color=palette[0])
axes[1].set(xlabel='Vínculos CNAE 38 / mil habitantes', title='Taxa agregada com população compatível')
fig.suptitle('Distribuição estadual do emprego formal em resíduos | 2024', fontsize=15, fontweight='bold')
fig.supxlabel('Contagens incluem 5.570 municípios. Taxas excluem quatro unidades de MT com incompatibilidade territorial; mesma exclusão no numerador e denominador.', fontsize=9)
fig.savefig(OUT / 'distribuicao_por_uf.png', dpi=180)
plt.close(fig)

def br(value, digits=3):
    return f'{value:,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')

c0 = fetch_corr(REC_RATE)
cp = fetch_corr(REC_RATE, subset='ambos_positivos')
cshare = fetch_corr(REC_SHARE)
main_rows = []
for metric in metrics_plot:
    values = [fetch_corr(metric, subset=subset) for subset in subsets]
    main_rows.append('| ' + LABELS[metric] + ' | ' + ' | '.join(f"{br(c['rho'])} (n={c['n']})" for c in values) + ' |')
doc = f'''# Emprego formal em resíduos: análise exploratória de 2024

## O que os registros mostram

O universo municipal reúne 265.143 vínculos ativos na divisão CNAE 38: 198.344 em coleta, 23.856 em tratamento/disposição e 42.943 em recuperação de materiais. São vínculos no município do estabelecimento, não pessoas únicas nem novas vagas. O total Brasil do arquivo bruto é 265.151; oito vínculos sem município, todos em recuperação, ficam fora do dataset municipal.

Dos 5.570 municípios, {summary['cnae38_zero_municipios']} ({br(summary['cnae38_zero_pct'], 1)}%) têm zero vínculo formal registrado em CNAE 38, e {summary['recuperacao383_zero_municipios']} ({br(summary['recuperacao383_zero_pct'], 1)}%) têm zero em recuperação de materiais. Isso não demonstra ausência de atividade: trabalho informal, cooperativas sem vínculos formais e serviços classificados em outros CNAEs podem ficar fora do recorte.

Após excluir quatro municípios de MT com delimitação territorial incompatível entre numerador e população, a taxa agregada é {br(summary['cnae38_por1000_agregado_sem_4_mt'])} vínculo CNAE 38 por mil habitantes; para recuperação, {br(summary['recuperacao383_por1000_agregado_sem_4_mt'])}. A participação agregada no estoque de todos os setores é {br(summary['cnae38_participacao_formal_agregada_pct'])}% para CNAE 38 e {br(summary['recuperacao383_participacao_formal_agregada_pct'])}% para recuperação. Taxas agregadas são razão entre somas; medianas municipais são medidas distintas, não ponderadas.

## Relação com a recuperação informada ao SINISA

A amostra de associações tem **{len(sample)} municípios**: resposta SINISA, verificações iniciais de qualidade aprovadas e território compatível. Os 716 não respondentes não foram transformados em zero; dois municípios com alerta de qualidade e as quatro unidades de MT ficam fora das associações. A mesma amostra básica é usada para shares, para manter a comparação entre indicadores.

Para vínculos em recuperação por mil habitantes versus recuperação oficial de resíduos secos, Spearman é **{br(c0['rho'])} (n={c0['n']})**. Na subamostra com ambos positivos, passa a **{br(cp['rho'])} (n={cp['n']})**. A mudança ilustra a influência dos zeros e da seleção do recorte; não indica que uma amostra seja automaticamente superior à outra.

| Medida de emprego vs recuperação de secos | Todos válidos | Recuperação > 0 | Vínculos > 0 | Ambos > 0 |
|---|---:|---:|---:|---:|
{chr(10).join(main_rows)}

O CSV `associacoes_spearman_com_n.csv` contém também as associações com recuperação total (secos + orgânicos), contagens absolutas para comparação do efeito do porte e população. Cada linha informa n, quantos zeros permanecem e a correlação parcial por porte. A participação do grupo 38.3 no estoque formal tem correlação {br(cshare['rho'])} com recuperação de secos (n={cshare['n']}).

## Método e sensibilidade ao porte

Spearman foi calculado como correlação de Pearson entre postos médios, em pares completos. Para a correlação parcial, foram regredidos separadamente os postos de emprego e recuperação sobre os postos de log10 da população, com intercepto; correlacionaram-se os resíduos. Para a taxa de recuperação 38.3 e recuperação de secos, o coeficiente parcial é {br(c0['rho_parcial_porte'])}, com o mesmo n={c0['n']}. Como log é monotônico, seus postos são os mesmos da população. Esse ajuste é um controle exploratório de porte, não um modelo causal.

As subamostras positivas são definidas separadamente para cada indicador SINISA e medida de emprego. Para taxas e shares, emprego positivo equivale a estoque positivo, pois denominadores são positivos. As contagens e taxas não foram aparadas nem winsorizadas. Os gráficos mantêm os extremos; o diagrama usa escala simétrica log para acomodar zeros e assimetria. Não foram usados testes de significância para escolher conclusões.

## Desagregações e implicações para diagnóstico

As tabelas por UF, região e porte apresentam estoques por grupo, estabelecimentos, frequência de zeros, shares, taxas agregadas, medianas municipais e n da amostra SINISA. Contagens incluem todas as 5.570 unidades; nas taxas, numerador e denominador excluem conjuntamente as quatro unidades de MT. Não se deve comparar uma soma nacional a uma mediana municipal como se fossem a mesma medida.

Os registros permitem localizar concentração de emprego formal e municípios onde o setor registrado é pequeno. Eles não identificam, sozinhos, um déficit de empregos verdes nem o número de vagas que determinada intervenção geraria. Municípios com recuperação SINISA positiva e poucos vínculos CNAE 38 são candidatos a investigação sobre cooperativas, informalidade, prestadores regionais e classificação econômica. Municípios com emprego setorial elevado e baixa recuperação também precisam de diagnóstico do tipo de resíduo, área atendida e composição dos serviços.

Prescrições devem combinar esses sinais com custos, cobertura, infraestrutura e inclusão de catadores. Capacitação e formalização podem ser discutidas como medidas a avaliar, com custos e condições de trabalho. Automatização pode substituir tarefas e exigir novas competências; estes dados transversais não quantificam esse efeito.

## Limites que permanecem

- A CNAE é atividade principal do estabelecimento, não ocupação individual. Divisão 38 inclui resíduos urbanos, industriais e perigosos, e o grupo 38.3 é recuperação de materiais; nenhum equivale automaticamente a emprego verde e decente.
- Informais não entram na RAIS. Um trabalhador pode possuir mais de um vínculo. Postos em prefeituras classificadas como administração pública podem ficar fora da divisão 38.
- Estabelecimento, residência do trabalhador e área atendida por prestadores regionais são geografias diferentes. SINISA descreve o serviço municipal, enquanto RAIS descreve a localização e atividade do estabelecimento.
- Não resposta, zeros, concentração regional, diferenças econômicas e de capacidade institucional podem alterar as associações. Taxas, shares e controle de porte não eliminam esses fatores.
- A análise é transversal, de 2024. Não demonstra causalidade, impacto de políticas, redução futura de custos ou geração futura de vagas.

## Arquivos e reprodução

Executar `scripts/analisar_emprego_setorial.py` após o ETL. O script gera os CSVs, o JSON `analises/emprego_setorial/resumo_diagnostico_setorial.json` e os PNGs nessa mesma pasta; a impressão digital do dataset de entrada fica no JSON. As fontes, layouts e reconciliações originais estão documentados em `docs/RAIS_SETORIAL.md` e nas evidências RAIS.

![Panorama do emprego setorial](../analises/emprego_setorial/panorama_emprego_setorial.png)

![Sensibilidade das associações](../analises/emprego_setorial/associacoes_emprego_recuperacao.png)

![Desagregação por UF](../analises/emprego_setorial/distribuicao_por_uf.png)
'''
(ROOT / 'docs/EMPREGO_SETORIAL_ANALISE.md').write_text(doc, encoding='utf-8')
print(json.dumps({'status': 'executado', 'pasta_saida': str(OUT), 'graficos_png': 3, 'relatorio': 'docs/EMPREGO_SETORIAL_ANALISE.md'}, ensure_ascii=True))
