# Revisão somente leitura do ETL

Arquivos revistos: `outputs/saneamento-inteligente-a3/scripts/etl.py` e `preparar_dados.py`. Nenhum arquivo em `outputs` foi alterado nesta revisão. Inspeção do código, dos glossários SINISA já baixados e da base parcial executada com IBGE DOU original.

## Achado acionável antes de integrar RAIS

Localização: `etl.py`, linhas 157–167 (ramo e status), com consequência no resumo da linha 189.

O ramo `if rais_file.exists()` aceita um CSV com as colunas obrigatórias e zero registros. Os testes `.all()` em séries vazias passam. Também aceita códigos de seis dígitos sem correspondência com o universo SINISA. Depois do `left merge`, define `rais_integrada = True` mesmo que nenhum vínculo tenha sido integrado. As colunas `fontes_integradas` e `status_rais` são preenchidas globalmente. Isso pode declarar uma terceira fonte integrada sem dados realmente combinados, além de ocultar municípios sem cobertura em um agregado parcial. O ramo ainda não está ativo na base atual.

Correção sugerida: validar código municipal com sete dígitos; validar vínculos não ausentes, finitos, não negativos e inteiros nos registros efetivamente fornecidos; rejeitar arquivo vazio; registrar anti-joins e contagens de correspondência com `indicator`; exigir ao menos uma correspondência antes de marcar a RAIS como integrada; registrar por município se o agregado o cobre. Um agregado de apenas alguns estados não permite interpretar ausência como zero nos demais. Se o agregado trouxer apenas municípios com estoque positivo, a extração precisa fornecer o universo/cobertura comprovado antes de completar zeros.

## Denominadores verificados e mantidos distintos

`IFR2002` usa `GFI2221 / GTR0201`, ou seja, DEX de manejo por habitante coberto por coleta. A coluna derivada `despesa_manejo_por_hab_ibge2024` usa a população residente total do IBGE. Ambas são úteis, mas não são equivalentes. A inspeção da base achou 3.350 municípios com diferença superior a R$ 0,02 entre essas duas colunas. Isso é consequência do denominador escolhido, não erro de cálculo. A versão oficial confere com `GFI2221/GTR0201` com diferença máxima de aproximadamente R$ 0,005 por arredondamento. Sugestão de apresentação: nomear a oficial como “por habitante coberto” e a calculada como “por habitante residente”.

O quociente `GFI2221/GTR1028` foi nomeado “despesa de manejo por tonelada de RSU” e o comentário evita chamá-lo de preço da coleta. O escopo da despesa abrange manejo, inclusive tratamento e disposição. Mantê-lo como indicador exploratório, sem inferir eficiência técnica apenas pelo menor valor.

## Validações confirmadas

- `preparar_dados.py` chama `extract(RAW, "dou")` e copia o resultado correto para a entrada esperada por `run()`.
- A versão DOU 29/08/2024 traz 5.570 registros únicos, 27 UFs e população somada de 212.583.750. Todos os códigos e populações coincidem com `DFE0001` da planilha SINISA.
- Os quatro formulários SINISA usam o mesmo universo municipal e preservam os não respondentes.
- Indicadores leem seus códigos na linha Excel 11, descrições na 12 e unidades na 13, começando os dados na 14. Informações leem códigos na 13 e dados na 14. O consumo inicial de 13 linhas não perde a primeira observação.
- Os campos de massa `GTR1025`, `GTR1027`, `GTR1028` e `GTR1029` foram usados conforme o glossário. A recuperação calculada `100*GTR1029/GTR1028` coincide com a oficial até aproximadamente 0,005 ponto percentual, compatível com arredondamento.
- A cobertura calculada com IBGE DOU também coincide com a oficial até aproximadamente 0,005 ponto percentual.
- Nos 716 não respondentes, despesas e massa não receberam valores numéricos artificiais.
- Divisões com denominador ausente ou não positivo permanecem indisponíveis.
- Os dois alertas da identidade de massa correspondem a dados de origem, sem correção inventada: São José de Ubá (3305133), 17.653 versus 13.153 + 450 toneladas; Irineópolis (4207908), 4.839 versus 480 + 39 toneladas.

## Observação de reprodutibilidade

A coleta por `--download` depende de acesso aos domínios oficiais. A validação estrutural dos arquivos acontece no processamento posterior. O pacote preserva os originais e os hashes, permitindo auditar uma eventual revisão da fonte. Não executei novamente `run()` porque isso sobrescreveria entregáveis; consultei os resultados já executados e fiz comparações somente leitura.

## Correção revisada

Após a revisão inicial, o ramo RAIS foi corrigido e reinspecionado: agora rejeita arquivo vazio, verifica código de sete dígitos e duplicidade, converte vínculos com erro explícito, exige valores inteiros não negativos, rejeita municípios fora do universo, exige ao menos uma correspondência com valor e registra fonte/status por município. O resumo inclui arquivo, variável, quantidade pareada e SHA256 de cada agregado. A checagem de integralidade com `mod(1).eq(0)` também rejeita `inf` e `-inf`, conforme verificação isolada executada. O código distingue o agregado setorial de resíduos do agregado de vínculos de todos os setores. O achado de falso status de integração está resolvido no código atual.

A coluna oficial IFR2002 foi renomeada para indicar habitante coberto, eliminando a ambiguidade de apresentação apontada. A inspeção final não identificou novo bloqueio nas alterações. O ramo RAIS precisará ser executado com o agregado real para confirmar a cobertura efetiva; esta revisão não declara essa execução concluída.
