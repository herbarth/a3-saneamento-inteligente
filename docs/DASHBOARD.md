# Dashboard Streamlit - versão local

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

Esta entrega contém o aplicativo local. A publicação em Streamlit Community Cloud ainda depende de repositório e conta disponíveis; não foi executada nem foi criado um endereço público. Ao publicar, usar `app.py` como arquivo principal; `requirements.txt` já inclui as dependências do painel. Validar o acesso público e os filtros após o deploy.

## Validação desta versão

O teste com `streamlit.testing.v1.AppTest` foi executado no processo principal e aprovado em nove cenários com o CSV real: abertura nacional, região, UF, porte, município individual, critério de qualidade, município não respondente, corte visual P1-P99 e controles de recuperação/escala. O resultado está em `evidencias/testes_dashboard.json`, com versões e contagens esperadas e exibidas. Não houve exceções nos cenários. Esse teste funcional não substitui inspeção visual ou validação de acesso público; a publicação ainda não foi executada.

A inspeção visual pelo navegador não foi concluída: a abertura do endereço local foi recusada pela autorização de acesso. Os testes funcionais AppTest foram executados e aprovados; acesso público permanece pendente.
