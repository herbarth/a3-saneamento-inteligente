from pathlib import Path
import contextlib
import io
import json
import traceback

ROOT = Path(__file__).resolve().parents[1]
cells = []

def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})

env = {"__name__": "__notebook__"}
count = 0

def code(text):
    global count
    count += 1
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        exec(compile(text, f"notebook_cell_{count}", "exec"), env)
    cells.append({"cell_type": "code", "execution_count": count, "metadata": {}, "source": text.splitlines(True), "outputs": [{"output_type": "stream", "name": "stdout", "text": stream.getvalue().splitlines(True)}]})

md("""# A3 — Saneamento Inteligente: inspeção da base integrada

**Base integrada, referência 2024.** Este notebook reúne a inspeção dos dados, validações e descritivas iniciais. O diagnóstico, as hipóteses e as prescrições estão consolidados no relatório e nas análises do projeto.

O tema foi informado como aprovado pelo professor. Os requisitos conferidos estão em `docs/REQUISITOS_VERIFICADOS.md`; os anexos originais foram preservados no pacote local.

Para reproduzir da raiz do projeto: `python scripts/preparar_dados.py --download` e `python scripts/eda_inicial.py`. A opção `--download` busca os arquivos oficiais SINISA, IBGE e as tabelas RAIS. O agregado setorial RAIS validado acompanha o projeto; para reler seus microdados, use também `--reprocessar-setorial`, conforme `docs/RAIS_SETORIAL.md`.

Não é necessário abrir as planilhas manualmente nem alterar seus cabeçalhos.
""")
code("""from pathlib import Path
import json
import pandas as pd

# Funciona quando o notebook é aberto na raiz do projeto ou na pasta notebooks.
candidates = [Path.cwd(), Path.cwd().parent, Path.cwd() / 'outputs/saneamento-inteligente-a3']
ROOT = next(p for p in candidates if (p / 'data/processed/saneamento_municipios_2024_parcial.csv').exists())
df = pd.read_csv(ROOT / 'data/processed/saneamento_municipios_2024_parcial.csv', dtype={'cod_ibge': str})
validation = json.loads((ROOT / 'evidencias/validacoes_etl.json').read_text(encoding='utf-8'))
print('Linhas e colunas:', df.shape)
print('Fontes efetivamente integradas:', validation['fontes_realmente_integradas'])
print('Uma linha por município e ano:', not df[['cod_ibge', 'ano']].duplicated().any())
""")
md("""## 1. O que significa integrar as fontes

O código IBGE de sete dígitos identifica o município. O ETL verifica correspondência um a um e UF. Uma terceira fonte apenas localizada na internet não conta como integrada. O campo `fontes_integradas` informa disponibilidade por linha; ausência de resposta no SINISA continua indicada em coluna própria.

SINISA 2025 descreve o ano 2024. Para IBGE, usamos a publicação DOU de 29/08/2024: suas 5.570 populações coincidem com a base demográfica do SINISA. A revisão posterior está preservada, mas altera o recorte territorial.
""")
code("""columns = ['cod_ibge', 'municipio', 'uf', 'ano', 'populacao_ibge_2024',
           'respondeu_sinisa', 'despesa_exploracao_manejo_rs_ano',
           'massa_rsu_coletada_t_ano', 'massa_recuperada_secos_organicos_t_ano',
           'status_rais']
print(df[columns].head(8).to_string(index=False))
""")
md("""## 2. Ausente não é zero

Os não respondentes não foram eliminados do universo nem receberam valores zero. Para analisar despesas e recuperação, usamos inicialmente respondentes com denominadores positivos e sem os alertas já detectados. Outras verificações contextuais ainda são necessárias.
""")
code("""print('Respostas ao SINISA:')
print(df['respondeu_sinisa'].value_counts(dropna=False).to_string())
print('\u005cnAusências nas variáveis selecionadas:')
print(df[columns].isna().sum().to_string())
print('\u005cnNúmero de diferenças de população SINISA x IBGE:', validation['diferencas_populacao_sinisa_ibge'])
""")
md("""## 3. Verificações e decisões

Preservamos os registros com problemas e os marcamos. Não corrigimos automaticamente valores oficiais sem evidência. Compare GTR1028 com GTR1025 + GTR1027, percentuais, denominadores e o indicador oficial IRS3010.
""")
code("""print('Alertas por regra:')
print(pd.Series(validation['alertas_por_regra']).to_string())
print('\u005cnMunicípios sinalizados:')
show = ['cod_ibge', 'municipio', 'uf', 'massa_rsu_coletada_t_ano',
        'massa_domiciliar_coletada_t_ano', 'massa_limpeza_urbana_t_ano']
print(df.loc[df.flag_qualidade, show].to_string(index=False))
""")
md("""## 4. Primeiras estatísticas — leitura cautelosa

A despesa abaixo é GFI2221 por população **residente**, enquanto IFR2002 oficial usa população **coberta pela coleta**. Recuperação inclui secos e orgânicos, segundo a definição SINISA. Medianas municipais não são taxas nacionais ponderadas.

Despesa por tonelada abrange o manejo e não representa o preço exclusivo da coleta. Não chamamos menor despesa automaticamente de maior eficiência.
""")
code("""sample = df.loc[df.apta_analise_custo_recuperacao].copy()
metrics = ['despesa_manejo_por_hab_ibge2024', 'despesa_manejo_por_t_rsu',
           'recuperacao_total_calculada_pct', 'cobertura_seletiva_sinisa_oficial_pct']
if 'vinculos_formais_totais_por_1000_hab' in sample:
    metrics.append('vinculos_formais_totais_por_1000_hab')
print('Amostra municipal preliminar:', len(sample))
print(sample[metrics].describe().T.to_string())
print('\u005cnPor região — cobertura de resposta:')
coverage = df.groupby('regiao').respondeu_sinisa.agg(municipios='size', respondentes=lambda x: x.eq('Sim').sum())
print(coverage.to_string())
""")
md("""![Gráficos preliminares](../analises/eda_preliminar.png)

O histograma e a dispersão usam escala log para tornar a distribuição legível. O box plot oculta somente a exibição de pontos extremos; eles permanecem no dataset. Os gráficos e as tabelas são gerados por `scripts/eda_inicial.py`.

## 5. Questões examinadas e continuidade

- A diferença de despesas permanece quando comparamos portes e regiões semelhantes?
- Os maiores valores são explicados por escopo dos serviços, distâncias, erros ou condições locais?
- A cobertura seletiva está associada à recuperação? A conclusão muda ao separar secos e orgânicos?
- Com a RAIS setorial validada, há associação com vínculos formais? Catadores informais não são medidos por essa fonte.

Correlação não demonstra causalidade. Um único ano não permite afirmar tendência ou criação de empregos.

## Fontes oficiais e rastreabilidade

- [SINISA 2025, referência 2024](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025)
- [IBGE — arquivos 2024](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/)
- [MTE — RAIS 2024](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/rais/rais-2024)

Consulte o inventário de fontes, os dicionários e o registro de metodologia em `docs/`. Consulte `evidencias/validacoes_etl.json` para a execução efetiva. O diagnóstico, as prescrições e os materiais de apresentação estão nas pastas próprias do projeto. Os resultados das hipóteses estão em `docs/HIPOTESES_E_QUESTOES.md`. O [painel online](https://a3-saneamento-inteligente-brasil.streamlit.app/) e o [repositório](https://github.com/herbarth/a3-saneamento-inteligente) foram publicados e validados. Identificação dos integrantes e vídeo final permanecem pendentes no acompanhamento da A3.
""")

notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}}, "nbformat": 4, "nbformat_minor": 5}
for i, cell in enumerate(cells):
    cell['id'] = f'a3-{i:03}'
target = ROOT / 'notebooks/01_primeira_execucao.ipynb'
target.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding='utf-8')
print(target, 'células de código executadas:', count)
