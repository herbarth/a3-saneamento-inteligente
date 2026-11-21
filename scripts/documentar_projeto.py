from pathlib import Path
import csv
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
raw = ROOT / 'data/raw'
processed = ROOT / 'data/processed'
docs = ROOT / 'docs'
df = pd.read_csv(processed / 'saneamento_municipios_2024_parcial.csv', dtype={'cod_ibge': str})
v = json.loads((ROOT / 'evidencias/validacoes_etl.json').read_text(encoding='utf-8'))

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ''

sources = [
    dict(fonte='SINISA', orgao='Ministério das Cidades / SNSA', edicao='SINISA 2025', ano_referencia=2024,
         pagina='https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025',
         url_arquivo='https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/SINISA_RESIDUOS_planilhas_2024.zip',
         arquivo='SINISA_RESIDUOS_planilhas_2024.zip', formato='ZIP com 9 XLSX', unidade='município; unidades em outras abas', chave='Cod_IBGE 7 dígitos',
         variaveis='GFI2221;GFI2208;GFI2233;GFI2237;GTR1025-1029;GTR0201;GTR0205;GTR1309-1311;IFR2002;IRS0001;IRS0005;IRS3002;IRS3010-3012',
         status='baixada, inspecionada e integrada', cobertura='5570 municípios;4854 respondentes;716 não respondentes',
         limitacao='autodeclaração; não resposta; massa orgânica segundo rota; dois alertas de identidade de massa'),
    dict(fonte='IBGE', orgao='IBGE / DPE / COPIS', edicao='DOU 29/08/2024; referência 01/07/2024', ano_referencia=2024,
         pagina='https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/',
         url_arquivo='https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/estimativa_dou_2024.ods',
         arquivo='estimativa_dou_2024.ods', formato='ODS', unidade='município', chave='COD. UF + COD. MUNIC 7 dígitos',
         variaveis='população estimada;nome;UF;código;notas;versão', status='baixada, inspecionada e integrada',
         cobertura='5570 municípios;27UF;212583750 habitantes;coincide DFE0001 em5570 registros',
         limitacao='estimativa 1julho; DOU escolhido por compatibilidade; revisão30dez preservada separadamente'),
    dict(fonte='RAIS', orgao='Ministério do Trabalho e Emprego / PDET', edicao='RAIS 2024 complementar', ano_referencia=2024,
         pagina='https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/rais/rais-2024',
         url_arquivo='https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1/rais-complementar-tabelas-2023x2024.xlsx',
         arquivo='rais-complementar-tabelas-2023x2024.xlsx', formato='XLSX agregado; microdados .7z/.comt',
         unidade='vínculo formal / estabelecimento; agregar por município', chave='código municipal a auditar; microdados normalmente6 dígitos',
         variaveis='estoque em31dez; município; CNAE; situação do vínculo no recorte setorial',
         status='localizada; extração municipal pendente', cobertura='não integrada nesta versão' if 'RAIS' not in v['fontes_realmente_integradas'] else 'consultar relatório de integração RAIS',
         limitacao='totais de todos setores não são empregos verdes; informalidade fora; layout2024 mudou; geografia do estabelecimento'),
]
if 'RAIS' in v['fontes_realmente_integradas']:
    sources[2]['status'] = 'baixada, inspecionada e integrada como contexto municipal; recorte setorial pendente'
    sources[2]['unidade'] = 'município, estoque de vínculos formais ativos em 31/12/2024'
    sources[2]['chave'] = 'código RAIS municipal de 6 dígitos convertido via prefixo único da tabela IBGE de 7 dígitos'
    sources[2]['variaveis'] = 'TABELA 4: Total 2024, todos os setores; UF; município; código municipal'
    sources[2]['cobertura'] = str(v['rais_agregados'][0]['municipios_com_valor_pareado']) + ' municípios com estoque total pareado; não identificados preservados separadamente'
if 'vinculos_cnae38_3112' in df:
    sources[2].update(status='microdados setoriais lidos integralmente, reconciliados e integrados',
        arquivo='RAIS_ESTAB_PUB_2024.7z', formato='7z com CSV .COMT, vírgula, Windows-1252',
        url_arquivo='ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/2024/RAIS_ESTAB_PUB.7z',
        unidade='estabelecimento declarante; agregação de vínculos ativos por município e CNAE',
        variaveis='Município - Código; CNAE 2.0 Subclasse - Codigo; Qtd Vínculos Ativos; grupos 381/382/383',
        cobertura='13.186.059 estabelecimentos lidos; 5570 municípios integrados; 265143 vínculos CNAE38 no recorte; 8 sem município separados',
        limitacao='CNAE38 é aproximação setorial; inclui resíduos perigosos e industriais; exclui informais e trabalhadores em outros CNAEs; não certifica emprego verde',
        arquivo_auxiliar='rais-complementar-tabelas-2023x2024.xlsx;rais_de_para_microdados_2024.xlsx')
for item in sources:
    p = raw / item['arquivo']
    item['bytes'] = p.stat().st_size if p.exists() else ''
    item['sha256'] = sha(p)
    item['verificado_em_data_local'] = '2026-11-20'
pd.DataFrame(sources).to_csv(docs / 'inventario_fontes.csv', index=False, encoding='utf-8-sig')
(docs / 'inventario_fontes.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf-8')

original = pd.read_csv(docs / 'dicionario_sinisa.csv').set_index('coluna').to_dict('index')
extra = {
    'cod_ibge': ('IBGE/SINISA', 'Código municipal de sete dígitos; chave textual.', 'código'),
    'ano': ('recorte', 'Ano de referência;2024.', 'ano'),
    'municipio_sinisa': ('SINISA', 'Nome como publicado SINISA; não usado como chave.', 'texto'),
    'municipio': ('IBGE', 'Nome como publicado pelo IBGE.', 'texto'),
    'uf': ('IBGE', 'Sigla da unidade da federação.', 'sigla'),
    'regiao': ('SINISA', 'Macrorregião do município.', 'texto'),
    'respondeu_sinisa': ('SINISA', 'Sim ou Não; Não é não resposta, nunca despesa zero.', 'categoria'),
    'populacao_base_sinisa': ('SINISA', 'DFE0001; comparada integralmente com IBGE DOU2024.', 'habitantes'),
    'populacao_ibge_2024': ('IBGE', 'População estimada em1julho2024; DOU29agosto2024.', 'habitantes'),
    'notas_ibge': ('IBGE', 'Chamadas de notas da linha da estimativa; textos originais preservados à parte.', 'texto'),
    'versao_ibge': ('IBGE', 'Data da edição usada;2024-08-29.', 'data'),
    'diferenca_populacao_sinisa_ibge': ('calculada', 'DFE0001 menos população IBGE escolhida.', 'habitantes'),
    'despesa_manejo_por_hab_ibge2024': ('calculada', 'GFI2221/população residente IBGE; diferente do denominador coberto do IFR2002.', 'R$/hab.ano'),
    'despesa_manejo_por_t_rsu': ('calculada', 'GFI2221/GTR1028; manejo total por massa RSU, não custo exclusivo da coleta.', 'R$/t'),
    'recuperacao_total_calculada_pct': ('calculada', '100*GTR1029/GTR1028; secos+orgânicos conforme SINISA.', '%'),
    'cobertura_coleta_ibge2024_pct': ('calculada', '100*GTR0201/população IBGE.', '%'),
    'cobertura_seletiva_ibge2024_pct': ('calculada', '100*GTR0205/população IBGE.', '%'),
    'porte_populacional': ('calculada', 'Cortes(0,20mil],(20mil,50mil],(50mil,100mil],(100mil,500mil],>500mil habitantes.', 'categoria'),
    'status_rais': ('controle', 'Estado real da disponibilidade RAIS por município; total não equivale ao setorial.', 'texto'),
    'fontes_integradas': ('controle', 'Fontes no registro; verificar a resposta SINISA e disponibilidade de cada variável.', 'texto'),
    'flag_qualidade': ('controle', 'Ao menos uma regra de consistência sinalizada; não é certificação dos demais valores.', 'booleano'),
    'apta_analise_custo_recuperacao': ('controle', 'Respondente,despesa e massa>0,recuperação entre0e100,sem alertas iniciais.', 'booleano'),
    'vinculos_formais_totais_3112': ('RAIS', 'Estoque vínculos formais ativos em31dez2024 em TODOS os setores; não empregos verdes.', 'vínculos'),
    'vinculos_formais_totais_por_1000_hab': ('calculada', '1000*vínculos formais totais/população IBGE.', 'vínculos/mil habitantes'),
    'flag_compatibilidade_territorial_rais': ('controle', 'Quatro municípios doadores de Boa Esperança do Norte; dados RAIS e IBGE DOU/SINISA requerem harmonização territorial. Estoque preservado; razão por população indisponível.', 'booleano'),
    'vinculos_residuos_ativos_3112': ('RAIS', 'Estoque ativo no recorte CNAE de resíduos validado; não representa todos empregos verdes.', 'vínculos'),
    'vinculos_residuos_por_1000_hab': ('calculada', '1000*vínculos setoriais/população IBGE.', 'vínculos/mil habitantes'),
    'vinculos_cnae38_3112': ('RAIS', 'Estoque ativo em estabelecimentos da divisão CNAE38, atividade principal; aproximação setorial, não certifica emprego verde.', 'vínculos'),
    'vinculos_coleta_381_3112': ('RAIS', 'Estoque ativo do grupo CNAE38.1, coleta de resíduos.', 'vínculos'),
    'vinculos_tratamento_382_3112': ('RAIS', 'Estoque ativo do grupo CNAE38.2, tratamento e disposição de resíduos.', 'vínculos'),
    'vinculos_recuperacao_383_3112': ('RAIS', 'Estoque ativo do grupo CNAE38.3, recuperação de materiais.', 'vínculos'),
    'estabelecimentos_cnae38_declarantes': ('RAIS', 'Registros declarantes da divisão38, incluindo estoque zero em31/12.', 'estabelecimentos'),
    'estabelecimentos_cnae38_com_vinculos_3112': ('RAIS', 'Registros da divisão38 com estoque positivo em31/12.', 'estabelecimentos'),
    'vinculos_recuperacao_383_por_1000_hab': ('calculada', '1000*vínculos grupo38.3/população residente; suspenso nos quatro municípios com alerta territorial.', 'vínculos/mil habitantes'),
    'participacao_cnae38_no_emprego_formal_pct': ('calculada', '100*estoque CNAE38/estoque formal de todos os setores no mesmo município; população não participa do denominador.', '%'),
}
dictionary = []
for col in df:
    if col in original:
        r = dict(original[col])
    else:
        assert col in extra, col
        source, description, unit = extra[col]
        r = dict(fonte=source, codigo_original='', descricao=description, unidade=unit, arquivo='', aba='')
    r.update(coluna=col, tipo_lido_csv=str(df[col].dtype), valores_nao_ausentes=int(df[col].notna().sum()), valores_ausentes=int(df[col].isna().sum()))
    dictionary.append(r)
pd.DataFrame(dictionary).to_csv(docs / 'dicionario_dataset_completo.csv', index=False, encoding='utf-8-sig')

checklist = pd.read_csv(docs / 'checklist_extraido.csv')
status = {
    't1': ('a confirmar', 'Nomes e composição do grupo ainda não informados.'),
    't2': ('definida', 'Indicadores Socioeconômicos; aderência conferida nos anexos.'),
    't3': ('aprovada segundo usuário', 'Tema e aprovação relatados na conversa.'),
    't4': ('definidas', 'SINISA, RAIS e IBGE oficiais; três fontes obtidas e integradas.'),
    't5': ('executada', 'Três fontes extraídas; microdados RAIS setoriais lidos integralmente e reconciliados.'),
    't6': ('executada com limitações registradas', 'ETL das três fontes e grupos CNAE38.1/38.2/38.3; ausências e alertas preservados.'),
    't7': ('executada com alertas preservados', 'Base integrada 5570x56 e validações gravadas; extremos administrativos exigem conferência contextual.'),
    't8': ('documentada nesta versão', 'Código, inventário, dicionário, decisões e evidências disponíveis.'),
    't9': ('executada', 'Descritivas, quartis, medianas e sensibilidades em analises/.'),
    't10': ('executada', 'Histogramas, box plots e dispersões com dados reais.'),
    't11': ('executada para o recorte transversal', 'Padrões por porte e região; um único ano não permite tendências temporais.'),
    't12': ('executada; revisão final pendente', 'Associações, controles e sensibilidade a extremos e zeros; desenho não causal.'),
    't13': ('iniciada', 'Hipóteses e limitações documentadas; precisam confronto final.'),
    't14': ('dispensada conforme decisão do usuário', 'Análise preditiva opcional não será realizada; manter foco nas entregas obrigatórias.'),
    't15': ('executada; revisão final pendente', 'Prescrições vinculadas a auditoria de custos, comparáveis, pilotos e inclusão dos trabalhadores.'),
    't16': ('versão para revisão gerada', 'Relatório formal consolida apresentação, ETL e análises; completar integrantes e revisão do grupo.'),
    't17': ('aplicativo local testado; publicação pendente', 'Nove cenários funcionais aprovados. Falta endereço público e validação de acesso.'),
    't18': ('pendente; realizar por último conforme usuário', 'Produção e publicação YouTube até7min após fechamento de dados, análises, relatório e dashboard.'),
    't19': ('iniciada', 'Verificações e revisão independente executadas; revisão final pendente.'),
    't20': ('pendente', 'Pacote local; repositório público ainda não publicado.'),
}
publication_path = docs / 'publicacao.json'
if publication_path.exists():
    publication = json.loads(publication_path.read_text(encoding='utf-8'))
    github_url = publication.get('github_url')
    dashboard_url = publication.get('dashboard_url')
    roteiro_video = publication.get('roteiro_video')
    if roteiro_video and (ROOT / roteiro_video).is_file():
        status['t18'] = (
            'roteiro preparado; gravação, edição e YouTube pendentes',
            f'{roteiro_video} — falas do grupo e demonstração, com duração estimada a confirmar na gravação.'
        )
    if github_url and publication.get('github_status', '').startswith('publicado'):
        status['t20'] = (
            'repositório público; completar links finais da entrega',
            f'{github_url} — código, base, relatório e análises disponíveis; conferir dashboard e vídeo no README.'
        )
    if dashboard_url and publication.get('dashboard_status', '').startswith('publicado e validado'):
        status['t17'] = (
            'publicado e validado',
            f'{dashboard_url} — evidências em evidencias/testes_publicacao_streamlit.json.'
        )
        if github_url:
            status['t20'] = (
                'repositório público com link do dashboard; vídeo pendente',
                f'{github_url} — dashboard validado; completar link do vídeo após a última etapa.'
            )
checklist['status_real'] = checklist.id.map(lambda k: status[k][0])
checklist['evidencia_ou_pendencia'] = checklist.id.map(lambda k: status[k][1])
checklist.to_csv(docs / 'acompanhamento_a3.csv', index=False, encoding='utf-8-sig')
print('Fontes documentadas:', len(sources), '| fontes integradas:', v['fontes_realmente_integradas'], '| colunas no dicionário:', len(dictionary))
