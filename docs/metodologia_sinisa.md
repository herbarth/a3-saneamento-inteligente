# Auditoria semântica SINISA - resíduos sólidos, referência 2024

Leitura dos glossários oficiais já baixados em `work/sinisa_investigacao`, com extrações por página preservadas nesta pasta. Nenhum novo download é necessário para aplicar estas notas. A Nota Técnica citada abaixo foi consultada pela ferramenta de navegação; a tentativa posterior de preservar cópia local não foi concluída e não integra o inventário de arquivos obtidos.

## Variáveis e interpretações

| Código | Definição e unidade | Página do glossário de informações |
|---|---|---|
| GFI2221 | Despesas totais anuais de exploração (DEX) do serviço de manejo de resíduos sólidos; soma automática de pessoal próprio GFI2209, terceiros GFI2210, tributos GFI2219 e outras despesas GFI2220. Valores por competência ou liquidados, em R$/ano. | 20 |
| GFI2208 | DEX do serviço de limpeza urbana. Tem escopo distinto de GFI2221. Não tratar os dois como sinônimos. | 16 |
| GFI2210 | Despesas com manejo executado por terceiros, incluindo coleta, transbordo, tratamento e disposição final. | 16-17 |
| GFI2211 | Despesa terceirizada com coleta indiferenciada domiciliar, já incluída em GFI2210. Não somar novamente ao total. | 17 |
| GFI2212 | Despesa terceirizada com coleta seletiva domiciliar, incluindo cooperativas/associações; já incluída em GFI2210. Não representa toda a despesa de coleta quando existe execução própria. | 17 |
| GTR1028 | Massa total anual de RSU coletada no município, em t/ano; soma automática de GTR1025 (rotas domiciliares) e GTR1027 (rotas de limpeza urbana). | 43-44 |
| GTR1029 | Massa anual denominada recuperada de resíduos domiciliares secos e orgânicos, em t/ano; soma dos materiais recicláveis recuperados das rotas GTR1023 e da massa total coletada GTR1008 em rotas de domiciliares recicláveis orgânicos. | 44 |
| GTR1034 | Massa recuperada de domiciliares secos; soma de GTR1023 nas rotas cujo destino é unidade de triagem. | 45 |
| GTR1035 | Massa denominada recuperada de domiciliares orgânicos; soma da massa coletada GTR1008 nas rotas cujo destino é unidade de compostagem. | 45 |
| GTR0201 | População total coberta por coleta indiferenciada direta ou indireta, com frequência mínima semanal. É população coberta pelo serviço, diferente da população residente total. | 39 |
| GTR0205 | População total coberta por coleta seletiva, com frequência mínima semanal. | 40 |
| DFE0001 | População total (IBGE), usada nos indicadores SINISA. | 36 |

**Parcela orgânica:** GTR1029/GTR1035 usam a massa da rota encaminhada à compostagem, conforme o glossário. Essa informação não comprova a quantidade final de composto vendida, redução de rejeitos ou rendimento efetivo do tratamento. Nomear a variável segundo o SINISA e explicar a regra; evitar apresentá-la como reciclagem industrial final aferida. É possível usar a expressão "recuperação declarada segundo a definição SINISA".

**Despesa e investimento:** GFI2221 mede operação (DEX); não é investimento nem valor total de todo o saneamento. Sua divisão por toneladas de RSU deve ser chamada "DEX de manejo por tonelada coletada", e não "custo exclusivo da coleta" ou custo de reciclagem. A relação é uma variável analítica do projeto, não uma medida causal de eficiência técnica.

## Indicadores oficiais e denominadores

| Código | Cálculo | Página do glossário de indicadores |
|---|---|---|
| IRS0001 | GTR0201 / DFE0001 × 100: cobertura total por coleta de resíduos domiciliares. | 1 |
| IRS0005 | GTR0205 / DFE0001 × 100: cobertura total por coleta seletiva. | 1 |
| IRS3010 | GTR1029 / GTR1028 × 100: recuperação de secos e orgânicos em relação ao total coletado. | 3 |
| IRS3011 | GTR1034 / GTR1028 × 100: recuperação de secos em relação ao total coletado. | 3 |
| IRS3012 | GTR1035 / GTR1028 × 100: recuperação de orgânicos em relação ao total coletado. | 3 |
| IFR2002 | GFI2221 / GTR0201: DEX de manejo por habitante coberto, em R$/habitante.ano. | 4 |

Para IRS3010, o glossário exige GTR1028 para o cálculo e não lista condição adicional no campo liberador. Isso não autoriza transformar numerador ausente em zero nem dividir por denominador zero. Na reprodução analítica, calcular apenas com numerador informado e denominador estritamente positivo; preservar o indicador publicado separadamente quando necessário.

IFR2002 usa a população **coberta**, não DFE0001 e não a população IBGE residente. A variável derivada GFI2221/população_IBGE é válida para outra pergunta, desde que nomeada "DEX por habitante residente" e não identificada como reprodução de IFR2002.

## População SINISA e IBGE

A Nota Técnica nº 8/2025, itens 4.2.1-4.2.3 e 6.1 (pp. 1-2), define DFE0001 como estimativa IBGE para 1º de julho de 2024 atualizada e enviada ao TCU; DFE0002 deriva de DFE0001 multiplicada pela taxa de urbanização do Censo 2022; DFE0003 é a diferença total menos urbana. Assim, DFE0002/DFE0003 são estimativas do SINISA apoiadas em parâmetros censitários, não uma nova observação censitária em 2024.

Fonte consultada: [Nota Técnica oficial de estimativas SINISA 2025](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/area-do-prestador/arquivos/Nota_Tecnica_Estimativas_Populacao_e_Domicilios_SINISA_2025_v01.pdf), disponibilizada na [página de regulamentação SINISA](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/sinisa-1/portaria-sinisa).

Não inferir incompatibilidade pelo valor isolado de Alta Floresta D'Oeste: 22.853 também foi confirmado na estimativa IBGE 2024 pelos agentes responsáveis pela extração. Manter DFE0001 e a população IBGE obtida diretamente em colunas distintas para registrar origem, versão e comparação. O ETL executado pela equipe informou coincidência dos 5.570 municípios SINISA com a versão DOU de 29/08/2024; a revisão TCU contém ainda Boa Esperança do Norte e deve ser documentada separadamente se adotada.

## Zeros, ausência e unidade de análise

- A legenda das planilhas diferencia não declaração pelo respondente, campo de somatório automático e `null` para município não respondente. Ausência não é evidência de coleta, emprego ou recuperação igual a zero.
- Preservar o indicador de resposta ao módulo. Os 5.570 registros cadastrais não equivalem a 5.570 respostas de qualidade completa.
- Usar abas municipais de resumo para uma linha por código IBGE e ano. Rotas e unidades de infraestrutura podem repetir município; uni-las diretamente à tabela municipal multiplicaria despesas e população.
- Não somar componentes de despesa ao total que já os contém. Não somar entrada em transbordo, triagem e disposição final como se fossem massas independentes coletadas: o mesmo resíduo pode passar por mais de uma unidade.
- Verificar GTR1028 versus GTR1025+GTR1027, sem corrigir divergências silenciosamente. O ETL da equipe relatou duas divergências, em São José de Ubá (3305133) e Irineópolis (4207908); manter campos originais e alertas. Esta nota semântica não substitui o relatório automático de validação.
- Valores negativos ou recuperação maior que massa coletada precisam ser sinalizados e investigados. Preservar a base bruta e definir explicitamente a amostra elegível para cada análise.
- Uma baixa DEX pode coexistir com serviço incompleto, execução não registrada ou menor cobertura. Comparações de eficiência devem considerar porte, cobertura, região e qualidade da declaração, sem tratar menor gasto como melhor resultado por definição.

Glossários oficiais: [informações](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/Glossario_Informacoes_SINISA_2024.pdf) e [indicadores](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/Glossario_Indicadores_SINISA_2024.pdf).
