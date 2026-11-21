# RAIS 2024: resíduos e recuperação de materiais

**Estado: extração executada e validada**, com o arquivo oficial de estabelecimentos da RAIS ano-base 2024. O agregado é uma medida do emprego formal no setor selecionado, não uma certificação de empregos verdes ou trabalho decente.

## Fonte e obtenção

O MTE disponibiliza microdados não identificados no [FTP do PDET](ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/2024/RAIS_ESTAB_PUB.7z), indicado na [página oficial de microdados](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/microdados-rais-e-caged). Foi escolhido o arquivo de estabelecimentos, evitando baixar os arquivos individuais de vínculos das sete regiões.

| Item | Evidência |
|---|---|
| Arquivo remoto | `RAIS_ESTAB_PUB.7z` |
| Diretório oficial | `/pdet/microdados/RAIS/2024/` |
| Data na listagem FTP | 18/05/2026 |
| Tamanho compactado | 140.661.991 bytes |
| SHA256 compactado | `f5dbd564a8c9afa4242ecd48a9a112b184e0a1a3ffa2df0ff28051057ad1a267` |
| Arquivo interno | `RAIS_ESTAB_PUB.COMT` |
| Tamanho descompactado | 1.431.437.349 bytes |
| SHA256 descompactado | `f82da9507079ecd40cb221edac3fb6bf61edf8c318c7dab26fd3eae066f84c0d` |
| Formato efetivamente lido | CSV, vírgula, aspas duplas, codificação Windows-1252 |
| Registros lidos | 13.186.059 estabelecimentos declarantes |

O [comunicado oficial de mudança de layout](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/comunicados/comunicado-microdados-rais-2024) informa o segundo processamento, incluindo administração pública, e o uso de `.7z`/`.comt`. O [De-Para oficial](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1/de-para-microdados.xlsx) foi baixado e inspecionado, aba `ESTAB_PUB`; SHA256 `4be7a7421ce44e40c4b18ea044c624e16775a5d0e3429dac18acb6afd7545117`. O arquivo está preservado em `data/raw/rais_de_para_microdados_2024.xlsx`.

## Variáveis e decisão sobre a CNAE

Foram lidos quatro campos: `Município - Código`, `CNAE 2.0 Classe - Código`, `CNAE 2.0 Subclasse - Codigo` e `Qtd Vínculos Ativos`.

Foi constatado um problema de rotulagem: **a coluna chamada Classe contém códigos de sete dígitos, idênticos à Subclasse em todos os 13.186.059 registros**. O processamento usa a coluna expressamente chamada Subclasse. A classe é derivada dos cinco primeiros dígitos, o grupo dos três primeiros e a divisão dos dois primeiros. Espaços foram removidos, preservando zeros à esquerda.

A [estrutura oficial da CONCLA/IBGE](https://concla.ibge.gov.br/images/concla/documentacao/EstruturaDetalhadaCNAE_CNAEFiscal2_Atualizada.pdf) define a divisão 38 como coleta, tratamento e disposição de resíduos; recuperação de materiais. Foram conferidas as sete classes observadas: 38114, 38122, 38211, 38220, 38319, 38327 e 38394.

## O que foi produzido

`data/processed/rais_residuos_municipios_2024.csv` contém uma linha para cada um dos 5.570 códigos do IBGE DOU de agosto de 2024, com `cod_ibge`, `ano` e:

| Campo | Interpretação |
|---|---|
| `vinculos_cnae38_3112` | Estoque formal nos estabelecimentos da divisão 38 em 31/12 |
| `vinculos_coleta_381_3112` | Parte do estoque no grupo 38.1, coleta |
| `vinculos_tratamento_382_3112` | Parte do estoque no grupo 38.2, tratamento e disposição |
| `vinculos_recuperacao_383_3112` | Parte do estoque no grupo 38.3, recuperação de materiais |
| `estabelecimentos_cnae38_declarantes` | Registros de estabelecimentos declarantes com CNAE 38, incluindo os sem vínculos em 31/12 |
| `estabelecimentos_cnae38_com_vinculos_3112` | Registros de estabelecimentos CNAE 38 com estoque positivo em 31/12 |

Zeros de estoque setorial foram preenchidos somente após a leitura integral e validação da cobertura. Significam ausência de vínculo ativo registrado nesse recorte, não ausência de catadores, reciclagem ou atividade informal.

## Validações executadas

- Os 13.186.059 registros reconciliam com o número nacional de estabelecimentos declarantes da TABELA 1 da [divulgação complementar oficial](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1/rais-complementar-tabelas-2023x2024.xlsx).
- A soma de vínculos ativos, todos os setores, é 57.132.156, igual ao estoque Brasil da mesma TABELA 1.
- **Todos os 5.570 totais municipais**, antes do filtro CNAE, reconciliam exatamente com a TABELA 4 oficial. Não houve diferença municipal.
- Códigos municipais têm seis dígitos. A junção para códigos IBGE de sete dígitos usa prefixos únicos; não usa nomes. Os códigos extras são separados, sem redistribuição.
- Estoques foram validados como inteiros não negativos. Para cada município, CNAE 38 não excede o total e a soma dos três grupos é igual à divisão 38.

Os resultados calculados nesta extração, ainda sujeitos às limitações abaixo, são:

| Recorte | Divisão 38 | Coleta 38.1 | Tratamento 38.2 | Recuperação 38.3 |
|---|---:|---:|---:|---:|
| Brasil, incluindo município não identificado | 265.151 | 198.344 | 23.856 | 42.951 |
| 5.570 códigos do dataset principal | 265.143 | 198.344 | 23.856 | 42.943 |

Há 1.788 municípios com estoque positivo na divisão 38. O total nacional de registros de estabelecimentos CNAE 38 é 19.275; 8.679 têm vínculos ativos em 31/12. No universo municipal principal, os números são 19.269 e 8.676, respectivamente.

Oito vínculos da divisão 38, todos no grupo de recuperação, possuem município não identificado (999999) e ficam fora da junção. Boa Esperança do Norte (510183) possui 945 vínculos totais e zero na divisão 38, permanecendo separado por não pertencer ao universo IBGE DOU usado no projeto. As taxas per capita nos municípios que cederam território exigem cautela; não houve redistribuição de vínculos ou população.

## Limitações para interpretar emprego verde

A CNAE descreve a atividade principal do estabelecimento; não informa a tarefa ambiental exercida por cada trabalhador. O setor 38 inclui resíduos industriais e perigosos, além dos urbanos; o grupo de recuperação não equivale apenas à coleta seletiva municipal. A divisão não compreende fabricação de produtos novos a partir de matéria-prima secundária nem simples revenda de sucata sem tratamento, conforme as [notas da CONCLA](https://concla.ibge.gov.br/images/concla/documentacao/CNAE20_NotasExplicativas.pdf).

Catadores informais, trabalhadores fora de estabelecimentos declarantes e postos em prefeituras classificados em administração pública podem ficar fora do recorte CNAE 38. Um trabalhador pode ter mais de um vínculo. O município é o do estabelecimento, não necessariamente o de residência ou toda a área atendida por prestadores regionais. As contagens não medem segurança ocupacional, remuneração, precariedade, qualidade ambiental nem número de novas vagas geradas. Não permitem afirmar que automatização, redução de custos ou reciclagem causam aumento do emprego.

Em prescrições, avaliar ganhos operacionais junto com os custos de implantação, capacitação, inclusão de cooperativas, exposição a resíduos perigosos e possível substituição de tarefas por automação. São aspectos do diagnóstico, sem converter o estoque observado em previsão de vagas.

## Reprodução e arquivos de evidência

`scripts/extrair_rais_setorial.py` lê o `.COMT` em blocos de 250 mil linhas, confere totais, documenta o problema da coluna Classe e publica o CSV somente após validar o arquivo completo. A execução realizada terminou em aproximadamente 26 segundos neste ambiente.

Para reproduzir, baixar o `.7z` pelo FTP indicado, descompactá-lo e executar o script com: caminho do `.COMT`, CSV IBGE, diretório de saída e diretório de evidências. O argumento opcional `--total-csv` recebe o agregado de todos os setores extraído da TABELA 4, ativando a comparação municipal. A biblioteca `pandas` está nas dependências do projeto. O `.COMT` de 1,43 GB permanece fora do pacote e do Git; o arquivo compactado pode ser obtido novamente pela URL e conferido pelo SHA256.

As evidências próprias são `evidencias/rais_setorial_metadados_validacoes.json`, `rais_setorial_download.json`, `rais_setorial_listagem_ftp.txt` e `rais_setorial_de_para_estab.json`. A análise da divergência de soma dos cinco grandes setores da planilha agregada é independente: esta extração confirmou todos os totais municipais, mas não determinou a causa daquela divergência.
