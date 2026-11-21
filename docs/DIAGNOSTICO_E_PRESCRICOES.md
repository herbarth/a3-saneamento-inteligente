# Diagnóstico e prescrições preliminares

## O que os dados sustentam agora

O problema imediato é a confiabilidade de valores extremos de despesa. A coleta seletiva e a recuperação aparecem associadas, mas boa parte dessa associação distingue municípios com zero e com valor positivo. Os dados transversais de 2024 não demonstram que aumentar cobertura cause determinada recuperação, economia ou contratação.

Fonte analisada: `data/processed/saneamento_municipios_2024_parcial.csv`, SHA256 `f2529c8660ff8df47664a2b850a6be7cfbcb5dcc44261dc781249fe5bf7530de`. Execução em UTC: 2026-11-21T02:10:16.746565+00:00. A base lida tem 5.570 linhas e 56 colunas. O script `scripts/diagnostico.py` leu os bytes uma única vez e calculou o hash dessa mesma versão. Resultados completos estão em `analises/diagnostico/`; o JSON `resumo_diagnostico.json` registra regras, versões e números.

## Amostra e decisões

Dos 5.570 municípios, 4.854 responderam ao SINISA e 716 não responderam. A amostra principal tem 4.852 municípios: respondentes com DEX e massa coletada positivas, recuperação entre 0% e 100% e sem os alertas de qualidade definidos pelo ETL. Os dois alertas de soma de massa ficam fora dessa análise, com os dados preservados. Nenhum não respondente foi transformado em zero.

Na amostra principal, 3.323 municípios (68,49%) têm recuperação declarada igual a zero; 3.438 (70,86%) têm cobertura seletiva igual a zero. A análise também foi repetida apenas nos 1.529 municípios com recuperação positiva. Essa segunda população responde a outra pergunta: intensidade entre quem já declara recuperação. Ela não substitui a amostra principal e pode selecionar municípios com melhor capacidade de registro.

As médias, medianas e correlações são municipais, sem ponderação, salvo quando o arquivo indica explicitamente “razão de somas”. Essas razões descrevem apenas os municípios da amostra, sem extrapolação para o Brasil inteiro. DEX é despesa operacional de manejo, inclui atividades além da coleta e não representa investimento. Recuperação inclui secos e orgânicos. O indicador oficial IFR2002 usa habitante **coberto**; o indicador analítico usa habitante **residente** do IBGE DOU 29/08/2024.

## 1. Custos extremos e sensibilidade

A mediana é R$ 69,17 por habitante. A média de R$ 232,35 é muito sensível à cauda superior. Para verificar essa dependência, foram conservados os municípios entre o percentil 1 (R$ 2,24) e o percentil 99 (R$ 609,66) da despesa por habitante. Os limites foram calculados na amostra principal, sem alterar o CSV original. O corte é uma ferramenta de diagnóstico, não uma prova de erro nem um padrão de custo aceitável.

| Amostra | n | Média R$/hab | Mediana R$/hab | Média R$/t | Mediana R$/t | Mediana recuperação % |
|---|---|---|---|---|---|---|
| base | 4.852 | 232,35 | 69,17 | 915,41 | 262,05 | 0,00 |
| corte_p1_p99_hab | 4.754 | 88,71 | 69,17 | 378,57 | 262,05 | 0,00 |
| corte_p1_p99_hab_e_t | 4.717 | 88,29 | 69,51 | 370,27 | 263,16 | 0,00 |
| recuperacao_positiva | 1.529 | 191,49 | 91,83 | 775,69 | 334,74 | 5,28 |
| corte_e_recuperacao_positiva | 1.509 | 105,36 | 91,37 | 414,91 | 332,95 | 5,28 |


No corte P1–P99, a média por habitante muda -61,82%, enquanto a mediana muda 0,00%. A igualdade exata da mediana também decorre de retirar o mesmo número de observações de cada cauda dessa variável; não é uma validação independente dos dados. O corte simultâneo por custo por tonelada mostra outra sensibilidade na tabela. Mediana e intervalo interquartil devem acompanhar a auditoria dos extremos. Os 49 municípios acima de P99 por habitante concentram 35,41% da DEX declarada da amostra, mas 0,89% de sua população. As somas de despesa também precisam dessa ressalva.

Exemplos para conferir documentos de origem, sem classificação de eficiência:

| Município | UF | População | DEX anual (R$) | DEX R$/hab |
|---|---|---|---|---|
| Várzea Grande | PI | 4.515 | 550.200.000,00 | 121.860,47 |
| Alto Piquiri | PR | 9.802 | 1.000.523.904,51 | 102.073,44 |
| São Mateus do Maranhão | MA | 40.160 | 3.796.140.372,30 | 94.525,41 |
| Barra de Guabiraba | PE | 12.616 | 900.072.438,29 | 71.343,73 |
| Pires Ferreira | CE | 10.952 | 720.889.440,00 | 65.822,63 |


A comparação dos 23 municípios distintos selecionados nas dez maiores e dez menores razões por habitante ou tonelada confirmou diferença máxima de R$ 0,00 entre a base e GFI2221 na planilha original. O máximo desvio da soma de componentes foi R$ 0,00. Os montantes extremos já estão no arquivo oficial e, em diversos casos, são dominados pelo campo de serviços de terceiros GFI2210. O ETL não gerou esses montantes ao converter números. Compatibilidade aritmética não comprova veracidade econômica. Valores de unidade, competência anual, escopo e contratos ainda exigem confirmação. Não foram divididos por mil, substituídos ou imputados.

O valor baixo também requer cuidado: Feira de Santana (BA) declara DEX de R$ 53.000,00, equivalente a R$ 0,08/habitante. Esses registros não justificam concluir que é um município mais eficiente. A lista completa de extremos e os componentes estão nos CSVs de auditoria.

## 2. Porte e região mudam a comparação

| Região | n | Mediana R$/hab | Municípios com recuperação >0 (%) |
|---|---|---|---|
| Norte | 387 | 44,26 | 7,75 |
| Nordeste | 1.341 | 46,26 | 8,72 |
| Sudeste | 1.557 | 74,82 | 41,36 |
| Sul | 1.143 | 92,17 | 54,68 |
| Centro-Oeste | 424 | 65,89 | 26,65 |


| Porte | n | Mediana R$/hab | Municípios com recuperação >0 (%) |
|---|---|---|---|
| até 20 mil | 3.265 | 62,98 | 25,73 |
| 20 a 50 mil | 946 | 69,67 | 34,46 |
| 50 a 100 mil | 308 | 90,45 | 49,03 |
| 100 a 500 mil | 285 | 97,35 | 59,65 |
| mais de 500 mil | 48 | 138,46 | 87,50 |


Os grupos apresentam composição, escala e distribuição de despesas diferentes. As tabelas completas `por_regiao_porte.csv` e `por_regiao_porte_corte_p1_p99.csv` permitem comparar dentro do mesmo porte e região, com o n de cada célula. A própria resposta à coleta SINISA é desigual: 74,75% no Nordeste e 96,05% no Sul. Esse contraste não foi corrigido por ponderação ou imputação e pode influenciar a comparação regional. Não se deve usar uma mediana regional como meta para todos os municípios. Células pequenas e valores extremos exigem leitura individual. Densidade urbana, distância de transporte, qualidade dos contratos, preço da disposição e nível do serviço não estão na base e continuam como explicações concorrentes.

## 3. Coleta seletiva e recuperação: presença versus intensidade

Spearman entre cobertura seletiva e recuperação é 0,888 na amostra completa (n=4.852). Entre municípios com recuperação positiva, passa a -0,056 (n=1.529). O contraste demonstra que a interpretação depende de incluir ou separar os zeros. Isso não torna nenhum dos resultados inválido; são perguntas diferentes.

Com cobertura seletiva positiva, 1.410 de 1.414 municípios têm recuperação positiva (99,72%). Com cobertura seletiva zero, 119 de 3.438 têm recuperação positiva (3,46%). Cobertura é população servida com frequência mínima semanal e recuperação é massa anual. Uma não substitui a outra. Os dois indicadores vêm da mesma cadeia operacional e da mesma fonte administrativa, o que também limita uma leitura causal independente.

As faixas de cobertura não apresentam intensidade estritamente crescente. O gráfico `03_cobertura_recuperacao.png` exibe essa diferença e o n de cada faixa. Há 4 municípios que declaram cobertura positiva e recuperação zero; a lista foi salva para conferir pesagem, destinação, rejeitos e período de funcionamento, sem presumir erro. Há ainda 119 com cobertura zero e recuperação positiva, que exigem entender frequência, rotas e registro institucional.

## 4. Controles estatísticos e o que não explicam

Os modelos lineares exploratórios relacionam a recuperação em pontos percentuais à cobertura (por dez pontos), ao logaritmo da despesa por habitante e ao logaritmo da população, com indicadores fixos para cada UF. Usam erros padrão agrupados por UF, correção para amostra finita e intervalos t com G−1 graus de liberdade. Eles comparam diferenças condicionais, sem eliminar seleção de respondentes, simultaneidade ou variáveis omitidas.

Na amostra completa, a associação ajustada de dez pontos adicionais de cobertura é 0,80 pp (IC descritivo de 95% 0,57 a 1,02; n=4.852). Apenas nos municípios com recuperação positiva, é -0,61 pp (IC descritivo de 95% -1,11 a -0,12; n=1.529). A figura `04_associacao_ajustada_sensibilidade.png` mostra as quatro amostras. Condicionar a análise a um resultado positivo muda a população e pode alterar a associação por seleção e composição. O sinal negativo dessa subamostra não demonstra que ampliar coleta reduza a recuperação. Não interpretar os coeficientes como o ganho esperado de uma política.

Dobrar a despesa por habitante está associado a -0,01 pp (IC descritivo de 95% -0,11 a 0,09; n=4.852) na amostra completa, mantendo os demais termos do modelo. No corte P1–P99, a associação é 0,00 pp (IC descritivo de 95% -0,10 a 0,11; n=4.754). O sinal e sua estabilidade devem ser lidos com os intervalos, sem concluir que mais despesa cause melhor desempenho ou que cortar despesa mantenha o mesmo serviço.

Ao acrescentar o contexto da densidade de vínculos formais de todos os setores, a associação ajustada de cobertura é 0,80 pp (IC descritivo de 95% 0,58 a 1,02; n=4.848). Quatro municípios de Mato Grosso com incompatibilidade territorial ficam sem a taxa RAIS; o modelo usa somente as observações disponíveis. Essa variável contextual não mede emprego verde.

OLS pode produzir valores ajustados fora de 0% a 100%: isso ocorre em 833 observações no modelo conjunto da amostra principal. `diagnosticos_modelos.csv` registra a quantidade por especificação. Por isso não foi usado como preditor operacional. Os intervalos refletem hipóteses do modelo, não corrigem erros administrativos nem garantem representação dos não respondentes. Os CSVs também registram Spearman por porte/região e correlações parciais nos postos com controles. Valores-p não foram usados para declarar sucesso de políticas.

Não foi usado “custo por tonelada versus recuperação” como evidência de efeito: ambos dividem pela massa coletada, podendo criar associação matemática por denominador comum. As comparações principais usam despesa por habitante e explicitam o papel da população.

## 5. Prescrições vinculadas às evidências

| Evidência executada | Ação proposta para o gestor | Como acompanhar e limite |
|---|---|---|
| Média de custo depende da cauda e 98 registros ficam fora de P1–P99; extremos conferem com a planilha bruta. | Priorizar conferência documental desses registros e dos dois alertas de massa. Conferir reais versus milhares, anual versus mensal, soma de componentes, escopo e terceirização. | Registrar cada confirmação ou retificação. Suspender metas de economia e comparações públicas de eficiência desses casos até a conferência. Percentis são prioridade de auditoria, não prova de erro. |
| Custos e recuperação variam por porte e região. | Escolher comparáveis do mesmo porte e região, validar escopo e usar mediana e quartis como referência de investigação. | Acrescentar distância de rotas, cobertura efetiva, toneladas pesadas e preço de destinação antes de avaliar contratos. Sem esses dados, não atribuir diferença a desperdício. |
| 3.323 municípios da amostra declaram recuperação zero; a associação de cobertura muda ao separar os zeros. | Conferir se o zero representa ausência real, rejeição total ou registro incompleto. Planejar piloto de coleta, triagem e destinação com medição de massa e rejeitos. | Medir secos e orgânicos separadamente, custo incremental, regularidade, contaminação e rejeitos. A análise não fornece uma previsão de recuperação nem um número de vagas a contratar. |
| 4 casos combinam cobertura seletiva positiva e recuperação zero. | Conferir primeiro a operação e o registro desses casos: frequência, início do serviço, pesagem e destino. | Resolver divergências de conceito antes de ampliar infraestrutura. Cobertura populacional isolada não prova recuperação de material. |
| O custo inclui manejo completo; recuperação mede secos e orgânicos. | Elaborar orçamento de um piloto com coleta, triagem, tratamento, transporte, disposição dos rejeitos e receita efetiva de materiais. | Comparar custos adicionais e qualidade de serviço ao cenário atual. Não prometer que a venda de materiais cobrirá a despesa nem impor redução de pessoal com base nesta correlação. |
| A RAIS usada nos controles deste diagnóstico é o total de todos os setores. No SINISA, catadores autônomos têm 4.245 ausências entre os 4.854 respondentes. | Interpretar o recorte CNAE 38 e seus grupos no estudo separado `docs/EMPREGO_SETORIAL_ANALISE.md`. Combinar o diagnóstico agregado com cadastro local de cooperativas e trabalhadores. | Não chamar vínculo total ou toda atividade da CNAE 38 de emprego verde, nem trabalhador SINISA de vínculo RAIS. Medir qualidade, formalização e renda em futuro piloto. Automatização e exigências de contratação podem excluir trabalhadores; prever qualificação e participação antes de mudanças. |

As propostas de piloto são decisões de gestão a testar, não intervenções com efeito estimado neste estudo. Custos de implantação, manutenção, demanda por material recuperado e possíveis mudanças no trabalho podem reduzir o benefício líquido. A base atual não quantifica essas parcelas nem a informalidade municipal completa.

## Hipóteses e perguntas para a próxima etapa

1. As despesas extremas correspondem a unidades, período, escopo ou contratos diferentes? A soma aritmética correta ainda precisa de confirmação documental.
2. Após verificar custos e comparar municípios semelhantes, o padrão de recuperação permanece? A sensibilidade já executada ajuda a delimitar, sem resolver, essa questão.
3. Em municípios com serviço seletivo declarado, perdas de triagem e frequência explicam a intensidade de recuperação? Essas variáveis operacionais precisam ser obtidas.
4. A distribuição de vínculos formais na CNAE 38 e seus grupos é examinada separadamente em `docs/EMPREGO_SETORIAL_ANALISE.md`. Associação municipal com recuperação não comprova criação líquida de empregos verdes.

Referências de definição: glossários de informações e indicadores do [SINISA 2025, ano de referência 2024](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025) e [estimativas municipais IBGE 2024](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/). Códigos e fórmulas utilizados estão no dicionário do projeto e nos scripts. As conclusões deste documento derivam dos arquivos efetivamente processados, não de percentuais nacionais de notícias.
