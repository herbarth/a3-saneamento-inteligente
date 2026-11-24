# Saneamento Inteligente — A3 UNIFACS

**Eficiência de Custos, Reciclagem e Oportunidades de Emprego Verde no Brasil**

Engenharia da Computação · Análise de Dados e Big Data  
Professor: Eduardo Sidney da Silva Xavier  
Referência dos dados: 2024 · Revisão numérica: 21/11/2026 · Revisão documental: 24/11/2026

## Acesso ao projeto

- **Repositório:** https://github.com/herbarth/a3-saneamento-inteligente
- **Dashboard online:** https://a3-saneamento-inteligente-brasil.streamlit.app/
- **Planilha Excel:** [abrir a planilha com cinco abas](planilhas/Planilha_A3_Saneamento_Inteligente.xlsx)
- **Relatório em Word:** [abrir a versão editável](relatorios/Relatorio_A3_Saneamento_Inteligente.docx)
- **Slides em PowerPoint:** [abrir os dez slides com transições](apresentacao/Slides_A3_Saneamento_Inteligente.pptx)
- **Vídeo:** gravação e publicação pendentes; o link final será incluído após a conferência.

A revisão numérica de 21/11/2026 permanece documentada. A revisão de 24/11/2026 incorpora o template do professor e torna os elementos exigidos visíveis no relatório. Permanecem pendentes os nomes e RAs/matrículas, a composição da equipe, o vídeo, seu link e a submissão final.

## Resultado executado

O projeto integra **SINISA, IBGE e RAIS** em uma base de **5.570 municípios e 56 colunas**. O recorte RAIS da divisão CNAE 38 foi obtido após a leitura integral de **13.186.059 estabelecimentos** e a conferência do estoque nacional e de todos os totais municipais com a divulgação oficial.

O conjunto municipal registra **265.143 vínculos formais** nas atividades de coleta, tratamento e recuperação de materiais. Essa contagem é uma aproximação setorial do emprego formal. Não certifica empregos verdes, não conta pessoas únicas e não inclui todo o trabalho informal.

Os custos declarados têm valores extremos que exigem auditoria. A análise usa medianas, comparáveis por porte/região, sensibilidades e controles, sem inferir economia ou criação causal de empregos. Os dados originais e os alertas são preservados.

## Arquivos principais

| Arquivo ou pasta | Conteúdo |
|---|---|
| `relatorios/Relatorio_A3_Saneamento_Inteligente.docx` | Relatório acadêmico em dez seções do template, com diagrama ETL, dicionário interno, estatísticas completas e prescrições priorizadas |
| `relatorios/Relatorio_A3_Saneamento_Inteligente.pdf` | Cópia de referência do relatório |
| `apresentacao/Slides_A3_Saneamento_Inteligente.pptx` | Dez slides editáveis, cinco gráficos com dados incorporados e transições suaves ao clique |
| `planilhas/Planilha_A3_Saneamento_Inteligente.xlsx` | Excel com resumo, despesas por porte, emprego por UF, base completa e dicionário/fontes |
| `data/processed/saneamento_municipios_2024_parcial.csv` | Base integrada de 5.570 × 56, com alertas preservados |
| `app.py` | Dashboard Streamlit com cinco abas, filtros e exportação CSV |
| `notebooks/01_primeira_execucao.ipynb` | Notebook didático com saídas executadas |
| `analises/diagnostico/` | Comparações, auditoria de extremos, sensibilidades e modelos associativos |
| `analises/emprego_setorial/` | Estoques por atividade e território, associações e sensibilidades |
| `docs/inventario_fontes.csv` | URLs oficiais, versões, cobertura, hashes e limitações |
| `docs/dicionario_dataset_completo.csv` | Todas as colunas, unidades e disponibilidade |
| `docs/acompanhamento_a3.csv` | Estado real de cada item do checklist |
| `evidencias/` | Validações, reconciliações e testes do dashboard |

## Fontes e recorte

- **SINISA 2025, referência 2024:** despesas operacionais, cobertura, massa coletada, recuperação e catadores.
- **IBGE 2024, DOU de 29/08/2024:** população residente e códigos municipais. As 5.570 populações coincidem com a base demográfica do SINISA. A revisão posterior foi auditada separadamente.
- **RAIS 2024:** estoque de vínculos em 31/12, total formal como contexto e divisão 38/grupos 38.1, 38.2 e 38.3 como recorte setorial. Microdados de estabelecimentos, com CNAE principal e município do estabelecimento.

A base mantém **716 não respondentes do SINISA**. A amostra inicial de despesas/recuperação tem **4.852 municípios**, após excluir dois alertas de soma de massa. Nas associações com taxas RAIS, quatro municípios de Mato Grosso ficam fora por compatibilidade territorial. Ausência não foi convertida em zero; os zeros RAIS setoriais foram atribuídos após leitura e validação do universo completo.

## Reprodução

Python 3.12 foi usado na execução. Na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
python scripts/preparar_dados.py --download
python scripts/eda_inicial.py
python scripts/diagnostico.py
python scripts/analisar_emprego_setorial.py
python scripts/gerar_relatorio.py
streamlit run app.py
```

Os nove cenários funcionais locais podem ser reproduzidos com `python scripts/testar_dashboard.py`. A validação do painel publicado está registrada em `evidencias/testes_publicacao_streamlit.json` e inclui a conferência do CSV baixado com a base local.

O repositório inclui os dados municipais processados, prontos para análise e para o dashboard. Os arquivos brutos ficam fora do Git; a opção `--download` obtém as fontes oficiais necessárias ao ETL. O ZIP local também inclui os arquivos SINISA e a estimativa IBGE. O `.7z` RAIS de 140,7 MB e o texto de 1,43 GB ficam fora do ZIP e do Git. Para reler os microdados oficiais:

```powershell
python scripts/preparar_dados.py --reprocessar-setorial
```

A opção baixa o arquivo se necessário, verifica o SHA256 e executa a agregação. Para renovar os demais arquivos: `python scripts/preparar_dados.py --download`. Revisões da fonte precisam de nova conferência de versões e hashes.

## Decisões da entrega

O relatório segue as **dez seções do Template_Relatório Final** do professor. A EDA apresenta no corpo do documento média, mediana, quartis Q1/Q3, desvio padrão amostral, mínimo e máximo, com indicação de unidades e amostras. O ETL inclui diagrama e dicionário das 56 variáveis. As prescrições explicitam responsáveis propostos, benefícios esperados e indicadores, acompanhados de matriz qualitativa de prioridade. Dashboard e storytelling têm capítulos próprios.

O edital Word fornecido em 24/11/2026 exige expressamente **GitHub com relatório e links do dashboard e do vídeo**, além da checklist. A aparência acadêmica formal segue a preferência do grupo; não são acrescentadas exigências de um manual de TCC. **A análise preditiva continua opcional e dispensada**, com a decisão registrada na seção 6.

A apresentação preserva dez slides editáveis em PowerPoint, com transições suaves e gráficos com dados incorporados. O vídeo fica por último e será narrado pelo próprio grupo. O roteiro de **744 palavras**, com meta estimada de **6min20s**, e o guia de leitura foram preparados no pacote privado para o usuário encaminhar. Eles ficam fora deste repositório; não houve envio automatizado a terceiros.

Faltam os **nomes completos e RAs/matrículas**, a confirmação da equipe de **3 a 5 alunos**, a gravação/edição e publicação no **YouTube**, a conferência da duração real de até **7 minutos**, a inclusão do link no GitHub e a submissão à disciplina até **03/12/2026**. Curso e professor já foram informados; o semestre é **2026.2**.

O dashboard está publicado. A conferência online de 23/11/2026 inspecionou cinco abas, filtro da Bahia e CSV de 417 linhas × 56 colunas; o serviço foi reativado após hibernação por inatividade. Esta revisão documental não repete nem substitui aquela conferência de disponibilidade.

## Revisão técnica final

Os **148 controles numéricos de 21/11/2026** permanecem como evidência histórica, incluindo estatísticas, amostras, junções e modelos recalculados por método independente. A base mantém o mesmo SHA256; esta revisão não releu os 13,2 milhões de estabelecimentos nem refez esses controles.

A revisão documental de **24/11/2026**, após considerar o template e os novos anexos Word, reorganizou o relatório e explicitou estatísticas, dicionário, fluxo de ETL e prescrições no próprio documento. Ela complementa a conclusão de conformidade anterior, que tinha outro conjunto de referências. Registros: `evidencias/revisao_final_tecnica.json` e `evidencias/revisao_template_20261124.json`. As hipóteses e novas questões continuam documentadas em `docs/HIPOTESES_E_QUESTOES.md`.

