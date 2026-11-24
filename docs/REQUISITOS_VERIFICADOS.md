<!-- A3_REVISAO_DOCUMENTAL_20261124_INICIO -->
# Requisitos atuais após os novos anexos de 24 de novembro de 2026

Revisão documental de 24/11/2026 com o edital Word, o template de relatório e a sugestão de storytelling fornecidos nesta rodada. A conclusão anterior de ausência de lacunas de apresentação se baseava no edital PDF e na checklist então disponíveis; ela não certificava a aderência ao template que ainda não havia sido considerado. A revisão atual complementa e substitui essa conclusão documental, sem apagar os registros históricos ou refazer a extração RAIS.

Foram considerados os três documentos Word fornecidos: **Enunciado Avaliação A3 - Alunos de TI**, **Template_Relatório Final** e **Sugestão_Roteiro_Video_Projeto_A3_Storytelling**. Os originais foram preservados fora do repositório público. Esta documentação resume os requisitos aplicáveis, sem reproduzir os anexos ou impor regras de um manual de TCC.

- O edital Word exige expressamente a entrega final por **repositório GitHub**, contendo apresentação do projeto, relatório de ETL e análises, link do dashboard e link do vídeo. Isso atualiza a observação histórica abaixo, relativa ao PDF anterior.
- O template organiza o relatório em **dez seções principais**: apresentação, fontes, ETL, EDA, diagnóstico, predição opcional, prescrições, dashboard, storytelling e conclusões.
- A identificação inicial inclui **semestre 2026.2, repositório, nomes completos e RA/matrícula**. Quantidade de linhas vazias no exemplo não define a composição real da equipe; permanece a regra de 3 a 5 integrantes ou exceção previamente autorizada.
- O capítulo 3 deve tornar visíveis o diagrama do ETL, métodos e decisões, enriquecimento, carga e **dicionário interno das 56 variáveis**.
- O capítulo 4 apresenta estatísticas descritivas no próprio relatório, incluindo média, mediana, Q1, Q3, **desvio padrão**, mínimo/máximo, unidades e amostras; mantém hipóteses e novas questões documentadas. A existência prévia dos cálculos nos CSVs não substituía sua exposição no corpo do relatório.
- O capítulo 5 organiza o diagnóstico e distingue associação observada de causalidade. O corte de 2024 não é apresentado como série histórica.
- O capítulo 7 explicita problema, evidência, ação, benefício esperado, responsável proposto e indicador, além da matriz qualitativa de impacto, viabilidade e prioridade. Os benefícios são propostas a verificar, sem economia ou empregos futuros fabricados.
- O capítulo 8 descreve a ferramenta, os insights e o link público do painel. O capítulo 9 separa a narrativa planejada da **URL e duração real do vídeo ainda pendentes**. O capítulo 10 confronta objetivos, resultados, contribuições, limites e trabalhos futuros.
- A predição permanece **opcional e dispensada**. Os oito blocos e tempos da sugestão de vídeo são orientações de comunicação; não obrigam oito slides, divisão igual da fala ou narração automática. O grupo optou por gravar sua própria fala.

Revisão estrutural: `evidencias/revisao_template_20261124.json`. Atualização da identificação: `evidencias/identificacao_equipe_20261124.json`. Foram informados cinco integrantes e suas matrículas. Pendências atuais: conferir a matrícula de Pedro, produzir e publicar o vídeo YouTube de até 7 minutos, incluir o link e submeter até **03/12/2026**.

## Registro histórico dos anexos anteriores

O conteúdo abaixo documenta a leitura efetuada antes dos novos anexos. Observações sobre ausência do GitHub no PDF ou falta de uma estrutura fixa não prevalecem sobre o edital Word e o template agora considerados.
<!-- A3_REVISAO_DOCUMENTAL_20261124_FIM -->

# A3 - Requisitos conferidos nos anexos reais

Verificação executada em 20/11/2026 (data de contexto do usuário). Originais recuperados do anexo da conversa anterior, copiados sem alteração para esta pasta. Leitura textual de todas as seis páginas do PDF; inspeção visual das páginas 3, 5 e 6. O HTML foi lido como texto, sem executar seus scripts. `extrair_requisitos.py` gera extração tabular e hashes dos originais.

## Requisitos do edital e evidência

| Requisito | Evidência no edital |
|---|---|
| Equipe com 3 a 5 alunos | p. 1, Estrutura da Equipe. Outra configuração exige negociação prévia e confirmação por mensagens comprovadas; irregularidade implica desconto de 50% na pontuação final. |
| Área temática e tema aprovados | p. 2: Mobilidade Urbana, Energia, Clima ou Indicadores Socioeconômicos. O tema deve ser submetido à aprovação do professor. |
| Ao menos 3 fontes públicas confiáveis | p. 3, A Fase de ETL: "pelo menos 3 fontes". APIs, arquivos oficiais e bancos são admitidos. |
| Ao menos 6 colunas distintas e linhas compatíveis | p. 3, A Fase de ETL. Não há mínimo numérico de linhas. |
| ETL documentado | p. 3: fontes, métodos de extração, limpeza e transformação, códigos-fonte, carga, enriquecimento, novas variáveis e justificativas das decisões. |
| EDA com rigor estatístico | pp. 3-4: médias, medianas, quartis, desvio padrão; histogramas, box plots e dispersão; investigar padrões, documentando como foram obtidos. Validar hipóteses e registrar novas perguntas. |
| Diagnóstico | pp. 1-2: analisar razões dos indicadores, correlação e possível causalidade. A exigência de discutir causalidade não torna um desenho transversal capaz de prová-la. |
| Prescrição obrigatória | p. 4: aconselhamento para usuário dos dados baseado em hipóteses e questões surgidas na EDA. |
| Predição opcional | pp. 2 e 4: se houver, documentar como as demais análises. A lista de entregas p. 5 menciona predições, mas não revoga a opcionalidade explícita p. 4. |
| Dashboard interativo online | p. 4: ferramenta livre (cita Power BI, Streamlit e Colab); link acessível para consulta. |
| Vídeo online no YouTube até 7 minutos | p. 5: narrativa lógica para público não técnico, resultados, foco em gestores e stakeholders não tecnológicos; entregar o link. |
| Recomendações acionáveis com evidências | p. 5, Resultado Final. |
| Entrega final em 03/12/2026 | p. 5: apresentação do projeto; relatório ETL; relatório EDA, prescrições e predições; link dashboard; link vídeo. |

## Pesos conferidos visualmente na página 6

- Apresentação do projeto e relatórios: 16 pontos (40%): precisão das informações, técnicas aplicadas e qualidade final dos dados.
- Dashboard e insights: 8 pontos (20%): clareza, objetividade, facilidade de interação e relevância.
- Vídeo: 16 pontos (40%): qualidade do storytelling e domínio do tema.
- Total: 40 pontos.

## Checklist HTML: itens 1-20

| ID | Atividade | Obrigatório |
|---|---|---|
| 1 | Formar equipe com 3 a 5 integrantes | Sim |
| 2 | Escolher uma área temática | Sim |
| 3 | Definir e validar o tema da análise | Sim |
| 4 | Definir as fontes de dados | Sim |
| 5 | Realizar a extração dos dados | Sim |
| 6 | Executar limpeza e transformação | Sim |
| 7 | Realizar a carga e validar a base final | Sim |
| 8 | Documentar todo o processo de ETL | Sim |
| 9 | Calcular estatísticas descritivas | Sim |
| 10 | Produzir visualizações iniciais | Sim |
| 11 | Identificar padrões, tendências e agrupamentos | Sim |
| 12 | Desenvolver análises diagnósticas | Sim |
| 13 | Documentar hipóteses e novos questionamentos | Sim |
| 14 | Definir se haverá análise preditiva | Não; preditiva opcional |
| 15 | Elaborar análise prescritiva | Sim |
| 16 | Consolidar relatório final | Sim |
| 17 | Publicar dashboard interativo online | Sim |
| 18 | Produzir e publicar vídeo de storytelling | Sim |
| 19 | Revisar qualidade dos dados e técnicas aplicadas | Sim |
| 20 | Enviar link para o repositório GitHub | Sim |

O item 20 exige que o repositório contenha relatório final, link do dashboard web e link do vídeo YouTube, com acesso público validado. Esse item complementa o edital PDF: GitHub não aparece no PDF. O checklist marca itens 16-20 como entregas finais.

## Decisões e cuidados de escopo

- O tema aprovado informado pelo usuário, "Saneamento Inteligente: Eficiência de Custos, Reciclagem e Oportunidades de Emprego Verde no Brasil", é compatível com Indicadores Socioeconômicos. A aprovação é relato do usuário, não informação presente nos anexos.
- Streamlit, Python e GitHub estão definidos na solicitação atual; o edital admite liberdade de ferramentas.
- Slides não constam como entrega obrigatória nos anexos, mas foram solicitados pelo usuário e devem integrar o projeto.
- ABNT, número de páginas, quantidade fixa de gráficos, testes estatísticos específicos, modelo preditivo e exigência de banco distribuído não são prescritos nos anexos.
- Um recorte exclusivamente 2024 não permite tendências temporais. É possível documentar essa limitação e investigar padrões transversais sem inventar séries.
- Vínculos formais da RAIS em atividades selecionadas não medem todo o emprego verde nem catadores informais; isso deve aparecer no dicionário e nas limitações.
- Despesa não é sinônimo de investimento. Custo por habitante e por tonelada exigem denominadores de escopo compatível; não deve ser prometida economia causal antes de analisar os dados.
- O HTML usa armazenamento local do navegador para marcar progresso. O arquivo original não comprova tarefas já concluídas; não se deve marcar ETL completo antes de integrar e validar as três fontes.
- O HTML tem cinco itens com `data-final=true` (16, 17, 18, 19 e 20). A fórmula de percentual considera todos os 20 itens, incluindo o opcional; para acompanhamento, preferir relatar estados por item e separar os 19 obrigatórios.
- Há erro tipográfico "20026-2" na p. 1 do PDF; o restante dos documentos e as datas indicam 2026-2. Preservar original e registrar em vez de alterar.

## Identificação e entregas pendentes

Curso e professor já foram informados e inseridos. Os nomes completos e a composição do grupo ainda não foram fornecidos. O grupo deve corresponder à regra de equipe do edital ou à configuração previamente autorizada pelo professor.

GitHub e dashboard já estão publicados e validados. A revisão técnica de dados, métodos e arquivos foi executada e registrada em `evidencias/revisao_final_tecnica.json`; não constitui uma exigência adicional de aprovação humana. Restam a identificação dos integrantes e o vídeo gravado pelo grupo, seguido de conferência de duração, publicação no YouTube e inclusão do link no repositório.
