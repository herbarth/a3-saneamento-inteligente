# RAIS 2024: extração executada

A fonte obtida é a **RAIS 2024 complementar**, publicada pelo Ministério do Trabalho e Emprego, tabela oficial `RAIS Complementar - Tabelas 2023x2024.xlsx` (2.544.043 bytes). A planilha identifica a divulgação como dezembro de 2025. Página consultada em 20/11/2026. O total da TABELA 1 é expressamente rotulado **Estoque**.

- [Página oficial RAIS 2024](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1).
- [Arquivo oficial XLSX](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1/rais-complementar-tabelas-2023x2024.xlsx).
- SHA256: `175c696341bb2821dc6a210367ccd20ba8e9e5f9d790daef195b76b3ee90ab38`.

## Variável efetivamente extraída

`vinculos_formais_totais_3112`: estoque de vínculos formais em 31/12/2024, **todos os setores**, por município do estabelecimento. Conta vínculos, não pessoas únicas; não cobre trabalho informal e não representa quantidade de empregos verdes, reciclagem ou serviços municipais de resíduos.

O arquivo tem TABELA 4 com código municipal de seis dígitos na coluna C, UF na B, nome na D e total de 2024 na Z. Os cabeçalhos estão nas linhas 13 e 14. A junção utiliza código, após conferir que o prefixo de seis dígitos de cada código IBGE de sete dígitos é único. A UF também é conferida; nomes não são usados para ligar fontes. `linha_origem_rais` preserva o número da linha Excel para auditoria.

## Resultados das validações

Foram geradas duas extrações: a integral compatível com o IBGE TCU de dezembro (5.571 unidades) e a do universo DOU de agosto (5.570 unidades) usado no dataset principal. Ambas são reais e preservam o estoque oficial.

Para o universo DOU:

- 5.570 códigos únicos, todas as 27 UFs, cobertura integral dos códigos IBGE fornecidos.
- Soma nos municípios do recorte: **57.120.312 vínculos**.
- Boa Esperança do Norte, código RAIS 510183: **945 vínculos**, separado como fora do universo DOU. Não foi distribuído entre outros municípios.
- Não identificado, código RAIS 999999: **10.899 vínculos**, separado sem atribuição territorial.
- Reconciliação: 57.120.312 + 945 + 10.899 = **57.132.156**, igual ao estoque Brasil da TABELA 1.
- Valores não negativos e inteiros e chave sem duplicação foram conferidos.
- Em 13 linhas, o total oficial da coluna Z excede a soma dos cinco grandes grupos exibidos; diferença total de 3.245 vínculos, dos quais 3.223 em Brasília. O total oficial foi mantido e as diferenças foram registradas, sem atribuir causa não confirmada.

A diferença territorial entre as versões IBGE/RAIS merece cuidado em taxas per capita. Municípios que cederam território para Boa Esperança do Norte podem ter numerador e denominador com delimitações distintas. A eventual comparação com SINISA deve mostrar essa limitação explicitamente. O estoque total não deve entrar como substituto de estoque de resíduos.

## Execução reproduzível

`extrair_rais_tabelas.py` contém `extract(raw_path, ibge_csv, output_dir)` e interface de linha de comando. Apenas lê arquivos locais, não depende de credenciais ou rede. Produz CSV e metadados/validações JSON, incluindo a reconciliação nacional e registros excluídos do universo. A execução com DOU foi concluída em `dou/`.

## Recorte setorial atual

A extração setorial dos microdados de estabelecimentos foi concluída e validada. Consulte RAIS_SETORIAL.md para as variáveis, as reconciliações e os limites da divisão CNAE 38. Esta nota descreve a tabela complementar de emprego formal total usada como contexto e verificação.
