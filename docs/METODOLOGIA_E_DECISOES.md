# Registro de metodologia e decisões — execução e consolidação

Data de trabalho: 20/11/2026, horário de Brasília. Horários automáticos nos registros técnicos estão em UTC.

## Pergunta e recorte

Como despesas de manejo, recuperação de resíduos e vínculos formais em atividades de resíduos se relacionam entre municípios brasileiros, e quais decisões podem ser investigadas a partir dessas diferenças?

Unidade: município × ano, referência 2024. Tema aprovado informado pelo grupo: **Saneamento Inteligente: Eficiência de Custos, Reciclagem e Oportunidades de Emprego Verde no Brasil**. Público: gestores municipais. O estudo transversal permite examinar associações; não identifica sozinho efeitos causais nem tendências ao longo do tempo.

## Extração e integração executadas

1. Recuperamos os anexos originais do edital e do checklist, preservando cópias e hashes.
2. Localizamos a página oficial de resultados SINISA 2025 e baixamos o ZIP de resíduos sólidos com referência 2024 e os dois glossários. Inspecionamos as nove planilhas do pacote; o ETL municipal inicial utiliza Indicadores, Despesas, Manejo e Cobertura. As planilhas de unidades e entradas têm outra granularidade e não foram somadas indiscriminadamente.
3. Lemos as primeiras 13 linhas de cada planilha para identificar códigos, unidades e descrições. Indicadores trazem códigos na linha 11; informações na linha 13. Dados municipais começam na linha 14. O formulário Manejo tinha 372 linhas adicionais sem código municipal válido, removidas e contabilizadas; não eram 372 municípios excluídos.
4. Extraímos o ODS oficial do IBGE por XML, preservando códigos e notas. Comparamos as versões DOU de 29/08/2024 e TCU revisada de 30/12/2024 com toda a população DFE0001 do SINISA. A versão DOU coincide nos 5.570 registros, sem diferenças. Ela é o denominador da base principal. A revisada inclui Boa Esperança do Norte e altera seis populações; foi preservada para auditoria, sem redistribuição automática de resíduos ou despesas.
5. Integramos por código IBGE de sete dígitos, com junções `one_to_one`. Não juntamos por nomes. Todas as UFs foram comparadas. Mantemos os 5.570 municípios e distinguimos os 4.854 respondentes dos 716 não respondentes do SINISA.
6. Exportamos CSV UTF-8 com BOM, dicionários, relatório JSON de verificações e alertas por município. As células vazias continuam ausentes. Zero só permanece quando consta numericamente na fonte; não imputamos zeros aos não respondentes.
7. Baixamos a divulgação complementar oficial RAIS 2024 e extraímos a TABELA 4, coluna Z: estoque de vínculos formais em 31/12/2024, todos os setores. O código municipal de seis dígitos foi convertido por correspondência com o prefixo único dos códigos IBGE; verificamos UF e cobertura. Essa variável dá contexto à estrutura do mercado de trabalho municipal e permite posteriormente comparar o peso do setor de resíduos na economia formal. Ela não mede empregos verdes. O recorte CNAE 38 foi obtido por leitura integral dos microdados de estabelecimentos, com resultados e reconciliações em RAIS_SETORIAL.md.

A RAIS já inclui Boa Esperança do Norte (código 510183; 945 vínculos), que não está no universo SINISA/IBGE DOU selecionado. Preservamos esse registro em evidência separada, além dos 10.899 vínculos com município não identificado, sem redistribuí-los. A soma dos 5.570 municípios da base, mais esses dois grupos, reconcilia com 57.132.156 vínculos da TABELA 1. Nos quatro municípios doadores de Mato Grosso, preservamos o estoque original e suspendemos a razão por população até harmonizar o território: Nova Ubiratã, Paranatinga, Sorriso e Vera.

A própria planilha RAIS tem 13 linhas em que o Total 2024 difere da soma de cinco grandes grupos econômicos. Preservamos o Total oficial que reconcilia com o Brasil e registramos as divergências, sem atribuir causa não confirmada. O detalhe está em `evidencias/rais_metadados_validacoes.json`.

## Indicadores e escopos

| Indicador | Cálculo | Interpretação e cuidado |
|---|---|---|
| Despesa de manejo por habitante | GFI2221 / população IBGE 2024 | Despesa de exploração, em R$/habitante.ano. Não é investimento nem despesa exclusiva da coleta. |
| Despesa de manejo por tonelada RSU | GFI2221 / GTR1028 | Razão analítica do manejo como um todo pela massa coletada. Não é tarifa nem custo marginal de coleta; avaliar escopo dos serviços antes de comparar. |
| Recuperação total | 100 × GTR1029 / GTR1028 | Inclui secos e orgânicos conforme definição SINISA. A parcela orgânica usa massa de rota de coleta, não rendimento efetivo após compostagem. |
| Cobertura seletiva | 100 × GTR0205 / população IBGE | Cobertura declarada com frequência mínima semanal, não percentual de massa reciclada. |
| Vínculos setoriais por mil habitantes | 1.000 × estoque ativo RAIS setorial / população IBGE | A calcular quando a extração municipal por atividade estiver validada. É estoque de vínculos, não pessoas únicas, vagas ou criação anual de empregos. |

Os indicadores oficiais SINISA são preservados em colunas com sufixo `sinisa_oficial`; os recalculados têm nomes próprios. Só há divisão quando o denominador é estritamente positivo. Não produzimos infinito e não limitamos percentuais artificialmente a 100%.

O indicador oficial IFR2002 divide GFI2221 pela população **coberta pela coleta** (GTR0201). Nossa despesa por habitante IBGE divide pela população **residente total**. Os dois não devem ser tratados como iguais; a diferença de denominador foi conferida numericamente e é mantida no nome e no dicionário.

GFI2233 (despesa total de serviços) apresenta somente 417 valores não ausentes. Por isso não é nossa variável principal de despesas. GFI2221 (DEX do manejo) tem 4.854 valores. Os campos de pessoal SINISA não substituem RAIS: são declarações do prestador, com universo e vínculo diferentes.

## Validações e alertas

O ETL verifica chaves únicas, número de municípios, UF consistente, ano, campos numéricos, não respondentes, ausência de infinito, denominadores positivos, limites percentuais e identidade GTR1028 = GTR1025 + GTR1027. Compara também a recuperação recalculada com IRS3010, tolerância 0,02 ponto percentual para arredondamento.

Duas divergências foram localizadas na soma de massas: São José de Ubá/RJ (3305133) e Irineópolis/SC (4207908). Os valores originais permanecem no CSV e nos alertas. A amostra inicial de custo/recuperação as exclui por precaução, ficando com 4.852 municípios. Os 716 não respondentes também ficam fora dessa análise, mas continuam no universo para estudar cobertura de respostas.

Os alertas iniciais não certificam todos os demais valores: despesas extremamente altas ou baixas ainda precisam de investigação contextual. Não removemos pontos extremos por conveniência e não os chamamos automaticamente de erros.

## Hipóteses investigadas

- Municípios de maior porte apresentam menor despesa de manejo por tonelada? Comparar portes e regiões, com análise de sensibilidade a valores extremos e escopo dos serviços.
- Maior cobertura seletiva está associada a maior recuperação? Distinguir secos, orgânicos e massa coletada seletivamente.
- Maior recuperação está associada a mais vínculos formais setoriais por habitante? A extração municipal setorial foi validada; as associações e sensibilidades estão no estudo de emprego. Controlar porte e região; vínculo formal não mede toda a cadeia informal.
- Há grupos com despesas elevadas e baixa cobertura? Investigar qualidade, distância de destinação, terceirização e condições de serviço antes de chamar isso de ineficiência.

## Limitações e aspectos negativos dentro do tema

- Respostas SINISA são autodeclaradas, com não resposta e possível erro; cobertura municipal não equivale a representatividade estatística nacional.
- Somar recuperação municipal e dividir pela massa total é diferente de calcular a média das taxas municipais. Toda estatística deve informar qual agregação usa.
- RAIS cobre trabalho formal, vinculado ao estabelecimento; catadores autônomos e parte das cooperativas podem ficar fora. CNAE de resíduos não certifica qualidade do trabalho nem benefício ambiental de toda ocupação.
- A RAIS integrada inclui o total formal como contexto e a divisão CNAE 38 e seus grupos como aproximação setorial. Nenhuma dessas contagens certifica empregos verdes. Vínculos por mil residentes também não são taxa de ocupação: há múltiplos vínculos por pessoa e deslocamentos entre municípios de residência e trabalho.
- Custos baixos podem coexistir com cobertura insuficiente, precariedade ou destino inadequado. Custos elevados podem refletir maior cobertura, qualidade ou distâncias, além de ineficiências.
- Coleta seletiva e automação exigem investimento, podem ampliar custos ou deslocar trabalhadores e dependem do mercado de materiais. Esses efeitos são questões a investigar, não resultados demonstrados por esta base inicial.
- Não estimamos geração futura de empregos, economia causal, retorno de investimento ou redução de emissões nesta etapa.

## Próximas entregas e critério de conclusão

As três fontes, inclusive o recorte setorial da RAIS, foram integradas. EDA, diagnóstico com sensibilidades e prescrições foram executados; relatório e apresentação estão em revisão. O dashboard passou por testes funcionais locais. Restam a publicação e validação dos links GitHub e Streamlit, a identificação completa do grupo e, por último, o vídeo de até sete minutos. A análise preditiva opcional foi dispensada por decisão do usuário. Edital e checklist são as referências obrigatórias; a aparência acadêmica não implica exigências adicionais de TCC.
