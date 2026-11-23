# Saneamento Inteligente — A3 UNIFACS

**Eficiência de Custos, Reciclagem e Oportunidades de Emprego Verde no Brasil**

Engenharia da Computação · Análise de Dados e Big Data  
Professor: Eduardo Sidney da Silva Xavier  
Referência dos dados: 2024 · Revisão técnica: 21/11/2026

## Acesso ao projeto

- **Repositório:** https://github.com/herbarth/a3-saneamento-inteligente
- **Dashboard online:** https://a3-saneamento-inteligente-brasil.streamlit.app/
- **Planilha Excel:** [abrir a planilha com cinco abas](planilhas/Planilha_A3_Saneamento_Inteligente.xlsx)
- **Relatório em Word:** [abrir a versão editável](relatorios/Relatorio_A3_Saneamento_Inteligente.docx)
- **Slides em PowerPoint:** [abrir os dez slides com transições](apresentacao/Slides_A3_Saneamento_Inteligente.pptx)
- **Vídeo:** gravação e publicação pendentes; o link final será incluído após a conferência.

Dados, métodos e arquivos passaram pela revisão técnica documentada. Permanecem pendentes a identificação dos integrantes e o vídeo final do grupo.

## Resultado executado

O projeto integra **SINISA, IBGE e RAIS** em uma base de **5.570 municípios e 56 colunas**. O recorte RAIS da divisão CNAE 38 foi obtido após a leitura integral de **13.186.059 estabelecimentos** e a conferência do estoque nacional e de todos os totais municipais com a divulgação oficial.

O conjunto municipal registra **265.143 vínculos formais** nas atividades de coleta, tratamento e recuperação de materiais. Essa contagem é uma aproximação setorial do emprego formal. Não certifica empregos verdes, não conta pessoas únicas e não inclui todo o trabalho informal.

Os custos declarados têm valores extremos que exigem auditoria. A análise usa medianas, comparáveis por porte/região, sensibilidades e controles, sem inferir economia ou criação causal de empregos. Os dados originais e os alertas são preservados.

## Arquivos principais

| Arquivo ou pasta | Conteúdo |
|---|---|
| `relatorios/Relatorio_A3_Saneamento_Inteligente.docx` | Relatório acadêmico editável em Word, com sumário, ETL, EDA, diagnóstico e prescrições |
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

O projeto segue o edital e os 20 itens do checklist. **A análise preditiva opcional foi dispensada pelo grupo.** Os modelos executados são associativos e servem ao diagnóstico, sem previsão de resultados futuros.

O **vídeo fica por último**, após o fechamento dos dados, das análises, do relatório e do dashboard. A apresentação tem dez slides editáveis em PowerPoint, com transições suaves ao clique e gráficos com dados incorporados. O dashboard passou por nove cenários funcionais locais. O repositório está público, com código, base, notebook, relatório e análises; os 104 arquivos da primeira publicação tiveram seus hashes conferidos com a cópia local. O dashboard Streamlit está publicado, com cinco abas inspecionadas, recorte da Bahia e download de 417 linhas × 56 colunas conferidos com a base local. O endereço respondeu em uma sessão nova sem credenciais. O grupo gravará a própria fala. A gravação, a edição e a publicação no YouTube permanecem pendentes; o limite de sete minutos deve ser conferido no arquivo final.

Os nomes completos dos integrantes ainda precisam completar a identificação acadêmica. Curso e professor já foram inseridos. Edital e checklist são as referências obrigatórias; a apresentação formal não impõe exigências adicionais de TCC. A revisão técnica e a conferência dos links foram executadas. Falta completar a identificação e inserir o vídeo final antes da entrega de 03/12/2026.

## Revisão técnica final

A conferência independente aprovou 148 controles numéricos, incluindo estatísticas, amostras, junções e modelos principais recalculados por método independente. Arquivos, notebook, Excel, relatório, apresentação e acesso aos links foram conferidos. Evidências e limites da revisão estão em `evidencias/revisao_final_tecnica.json`. As hipóteses e novas questões estão consolidadas em `docs/HIPOTESES_E_QUESTOES.md`.
