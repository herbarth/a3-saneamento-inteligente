# IBGE população municipal 2024 — obtenção e inspeção

## Fontes oficiais obtidas

- Diretório: https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/
- Publicação DOU de 29/08/2024: `estimativa_dou_2024.ods` (199.222 bytes).
- Revisão TCU de 30/12/2024: `POP2024_20241230.ods` (191.994 bytes), além da cópia XLS de 822.272 bytes.
- Data de referência das estimativas: 01/07/2024.
- Explicação das revisões: https://www.ibge.gov.br/estatisticas/sociais/populacao/2038-np-estimativas-de-populacao/9103-estimativas-de-populacao.html?edicao=41105

Os arquivos foram baixados de domínio oficial. As planilhas ODS foram extraídas com a biblioteca padrão do Python, lendo `content.xml`. O script `extrair_ibge.py` pode baixar novamente e extrair ambas as versões. Ele preserva chamadas de notas em `notas_ibge`, sem substituir o valor da coluna de estimativa pelos valores judiciais citados em notas.

## Resultado efetivamente validado

| Validação | DOU original | TCU revisado |
|---|---:|---:|
| Registros / códigos únicos | 5.570 | 5.571 |
| UFs | 27 | 27 |
| Códigos com sete dígitos | Todos | Todos |
| Populações positivas e inteiras | Todas | Todas |
| Soma municipal | 212.583.750 | 212.583.750 |
| Igual à população Brasil da aba oficial | Sim | Sim |

CSV: `cod_ibge` (texto de sete dígitos), `municipio`, `uf`, `populacao_2024` (habitantes), `ano`, `notas_ibge`, `versao_ibge`. Metadados JSON registram URL, bytes, SHA256, momento de processamento e validações. As duas versões são alternativas da mesma fonte, não duas fontes independentes.

## Compatibilidade com SINISA

Foi comparado o arquivo `SINISA_RESIDUOS_Indicadores_2024.xlsx`, aba `Planilha_Indicadores_municipais`, código `Cod_IBGE` e população `DFE0001`. Cabeçalho na linha Excel 13 e dados a partir da 14 (`pandas.read_excel(header=12)`).

A versão DOU original pareia os 5.570 registros SINISA, sem duplicidade, sem código não pareado e sem diferença em `DFE0001`. A versão revisada pareia todos os 5.570 e deixa um registro extra do IBGE: Boa Esperança do Norte, código 5101837, 5.772 habitantes, município instalado em 01/01/2025. A revisão também muda seis populações em municípios que continuam pareados:

| Código | Município | DFE0001 SINISA / DOU | TCU revisado |
|---|---|---:|---:|
| 2801207 | Canindé de São Francisco (SE) | 27.885 | 33.491 |
| 2805406 | Poço Redondo (SE) | 34.723 | 29.117 |
| 5106240 | Nova Ubiratã (MT) | 12.108 | 9.589 |
| 5106307 | Paranatinga (MT) | 28.228 | 28.204 |
| 5107925 | Sorriso (MT) | 120.985 | 120.561 |
| 5108501 | Vera (MT) | 13.389 | 10.584 |

Recomendação para o recorte municipal de 2024: usar DOU original para taxas alinhadas ao território/população efetivamente presentes no SINISA. Preservar a revisão como evidência e explicitar a escolha. Usar apenas igualdade de ano, sem verificar território, geraria taxas divergentes nesses seis municípios. Não redistribuir automaticamente os dados de resíduos ou de emprego para o novo município.

As diferenças e não pareamentos estão salvos em `comparacao_versoes_ibge_2024.csv`, `comparacao_sinisa_ibge_diferencas.csv`, `comparacao_sinisa_ibge_nao_pareados.csv` e dois JSON de validações.

## Comandos reprodutíveis

```powershell
python extrair_ibge.py --versao dou --download
python extrair_ibge.py --versao tcu --download
```

Sem `--download`, o script usa o arquivo original já salvo no diretório. Sem dependências externas para extrair ODS. Não foi gerado gráfico, resultado de EDA nem inferência causal nesta etapa.
