# Saneamento Inteligente — A3 UNIFACS

**Eficiência de Custos, Reciclagem e Oportunidades de Emprego Verde no Brasil**

Engenharia da Computação · Análise de Dados e Big Data  
Professor: Eduardo Sidney da Silva Xavier  
Referência dos dados: 2024 · Versão de trabalho: 20/11/2026

## Acesso ao projeto

- **Repositório:** https://github.com/herbarth/a3-saneamento-inteligente
- **Dashboard online:** publicação em andamento; o endereço será inserido após validação.
- **Vídeo:** etapa final, ainda não produzido.

Esta é uma versão para revisão do grupo. A identificação dos integrantes e a conferência final das entregas permanecem pendentes.

## Resultado executado

O projeto integra **SINISA, IBGE e RAIS** em uma base de **5.570 municípios e 56 colunas**. O recorte RAIS da divisão CNAE 38 foi obtido após a leitura integral de **13.186.059 estabelecimentos** e a conferência do estoque nacional e de todos os totais municipais com a divulgação oficial.

O conjunto municipal registra **265.143 vínculos formais** nas atividades de coleta, tratamento e recuperação de materiais. Essa contagem é uma aproximação setorial do emprego formal. Não certifica empregos verdes, não conta pessoas únicas e não inclui todo o trabalho informal.

Os custos declarados têm valores extremos que exigem auditoria. A análise usa medianas, comparáveis por porte/região, sensibilidades e controles, sem inferir economia ou criação causal de empregos. Os dados originais e os alertas são preservados.

## Arquivos principais

| Arquivo ou pasta | Conteúdo |
|---|---|
| `relatorios/Relatorio_A3_Saneamento_Inteligente.pdf` | Relatório acadêmico formal, com apresentação, ETL, EDA, diagnóstico e prescrições |
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

O repositório inclui os dados municipais processados, prontos para análise e para o dashboard. Os arquivos brutos ficam fora do Git; a opção `--download` obtém as fontes oficiais necessárias ao ETL. O ZIP local também inclui os arquivos SINISA e a estimativa IBGE. O `.7z` RAIS de 140,7 MB e o texto de 1,43 GB ficam fora do ZIP e do Git. Para reler os microdados oficiais:

```powershell
python scripts/preparar_dados.py --reprocessar-setorial
```

A opção baixa o arquivo se necessário, verifica o SHA256 e executa a agregação. Para renovar os demais arquivos: `python scripts/preparar_dados.py --download`. Revisões da fonte precisam de nova conferência de versões e hashes.

## Decisões da entrega

O projeto segue o edital e os 20 itens do checklist. **A análise preditiva opcional foi dispensada pelo grupo.** Os modelos executados são associativos e servem ao diagnóstico, sem previsão de resultados futuros.

O **vídeo fica por último**, após o fechamento dos dados, das análises, do relatório e do dashboard. A apresentação tem dez slides em uma versão editável no Spaces. O dashboard passou por nove cenários funcionais locais. O repositório foi criado na conta do grupo; o envio dos arquivos e a publicação Streamlit estão em andamento. O endereço público do dashboard e o vídeo YouTube ainda não foram validados.

Os nomes completos dos integrantes ainda precisam completar a identificação acadêmica. Curso e professor já foram inseridos. Edital e checklist são as referências obrigatórias; a apresentação formal não impõe exigências adicionais de TCC. A revisão do grupo e a conferência de links continuam necessárias antes da entrega de 03/12/2026.
