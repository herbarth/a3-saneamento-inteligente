# Dashboard Streamlit — versão online

O painel lê diretamente `data/processed/saneamento_municipios_2024_parcial.csv`. Oferece filtros por região, UF, porte e município, cinco abas de consulta e download do recorte em CSV. A página mantém não respondentes e valores ausentes visíveis; despesas e recuperação usam por padrão a elegibilidade definida no ETL.

## Executar

Na pasta raiz do projeto, com Python disponível:

```console
python -m pip install -r requirements-dashboard.txt
python -m streamlit run app.py
```

Abrir o endereço local informado pelo Streamlit. A configuração visual fica em `.streamlit/config.toml`. O caminho dos dados é resolvido a partir de `app.py`, portanto o carregamento não depende da pasta de onde o processo foi iniciado.

## Leitura correta

- Panorama: municípios selecionados, resposta SINISA, não resposta e medianas de cobertura do serviço. Cobertura de respostas usa todos os municípios do filtro; medianas de serviço usam valores informados.
- Despesas: DEX de manejo por habitante residente IBGE, por habitante coberto SINISA e por tonelada coletada. Os três denominadores têm nomes distintos. A DEX não é investimento nem custo exclusivo da coleta.
- Recuperação: secos e orgânicos, apenas secos e apenas orgânicos conforme indicadores oficiais. A parcela orgânica segue a massa encaminhada por rota à compostagem. A razão agregada usa somente pares completos de massa e difere da mediana das taxas.
- Emprego formal: total de todos os setores exibido como contexto, sem classificação como emprego verde. O campo `vinculos_cnae38_3112`, quando disponível, apresenta o estoque da divisão 38 (coleta, tratamento, disposição e recuperação), incluindo resíduos perigosos e não perigosos. O painel mostra o total setorial e sua cobertura separadamente. As atividades selecionadas não certificam emprego verde ou qualidade do trabalho. Ausências não são preenchidas com zero.
- Qualidade e fontes: ausência por medida, alertas de qualidade e territoriais, evidências de validação, links oficiais e limitações. O filtro de qualidade não remove municípios do panorama de respostas.

Os gráficos mostram diferenças e associações observadas. Não há afirmação de economia causal, geração futura de empregos ou eficiência comprovada. O recorte de um ano não permite tendências temporais.

Com o detalhamento RAIS integrado, a aba Emprego também apresenta os grupos `vinculos_coleta_381_3112`, `vinculos_tratamento_382_3112` e `vinculos_recuperacao_383_3112`, além das medianas dos vínculos setoriais por mil residentes e da participação no total formal. As contagens são estoques de vínculos no município do estabelecimento, não pessoas únicas, admissões anuais ou ocupações exclusivamente verdes.

## Publicação

Painel público: https://a3-saneamento-inteligente-brasil.streamlit.app/

Repositório: https://github.com/herbarth/a3-saneamento-inteligente

Publicado no Streamlit Community Cloud, branch `main`, arquivo principal `app.py`, Python 3.12.16. O serviço instala `requirements.txt`; nenhuma credencial de dados é necessária. A configuração e os dados processados estão no repositório.

As cinco abas foram inspecionadas no endereço publicado. O filtro da Bahia apresentou 417 municípios e 310 respondentes. O CSV baixado contém 417 linhas e 56 colunas, comparadas com a base local. Uma sessão HTTP nova, sem credenciais, recebeu resposta 200 no endereço público. Evidências em `evidencias/testes_publicacao_streamlit.json`.

## Validação desta versão

O teste com `streamlit.testing.v1.AppTest` foi executado no processo principal e aprovado em nove cenários com o CSV real: abertura nacional, região, UF, porte, município individual, critério de qualidade, município não respondente, corte visual P1-P99 e controles de recuperação/escala. O resultado está em `evidencias/testes_dashboard.json`, com versões e contagens esperadas e exibidas. Não houve exceções nos cenários. O teste local foi complementado pela inspeção do painel publicado e pela validação do acesso e do download descritas acima.

A abertura do endereço local não havia sido autorizada na etapa anterior. A inspeção visual foi realizada posteriormente no endereço público do Streamlit. Ajustou-se o espaçamento superior para evitar que o cabeçalho cobrisse a identificação institucional; os filtros receberam textos em português. As limitações da base permanecem explícitas no painel.
