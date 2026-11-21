# Hipóteses examinadas e novas questões de pesquisa

## Escopo da avaliação

Esta síntese consolida H1, H2 e H3 já apresentadas no relatório. Os resultados são observacionais, referentes a 2024, e não demonstram efeitos de políticas. O status de uma hipótese informa o que foi observado na amostra; não é uma declaração de validade universal ou de causalidade.

A base contém 5.570 municípios e 56 colunas, integrando SINISA, IBGE e RAIS. A amostra principal de despesas e recuperação tem 4.852 municípios. As associações com taxas RAIS usam 4.848 unidades, após as quatro ressalvas territoriais. Ausência de informação não foi convertida em zero. A base de referência tem SHA256 `f2529c8660ff8df47664a2b850a6be7cfbcb5dcc44261dc781249fe5bf7530de`.

## H1 — As razões de despesa variam por porte e região?

**Evidência executada.** As medianas de DEX por habitante residente variam de R$ 62,98 no grupo de até 20 mil habitantes a R$ 138,46 nos municípios com mais de 500 mil habitantes. Por região, vão de R$ 44,26 no Norte a R$ 92,17 no Sul. Os tamanhos dos grupos, quartis e demais estatísticas estão nas tabelas por porte, região e combinação dos dois critérios.

**Conclusão observacional.** Há diferenças descritivas entre os grupos. O resultado sustenta usar comparáveis de porte e região semelhantes para investigação gerencial. Não demonstra que porte ou região causem as diferenças, nem identifica desperdício ou eficiência.

**Limites.** Não resposta desigual, preços, distâncias, contratos, densidade urbana e níveis de serviço podem alterar a comparação. As medianas regionais não são metas universais de gasto. Valores extremos continuam preservados. A estabilidade exata da mediana após retirar o mesmo número de observações das duas caudas também decorre do procedimento de aparação e não valida os registros de forma independente.

**Evidências.** `analises/diagnostico/por_porte.csv`, `por_regiao.csv`, `por_regiao_porte.csv`, `por_regiao_porte_corte_p1_p99.csv` e `estatisticas_por_amostra.csv`; relatório, seções 5 e 6.

## H2 — Maior cobertura seletiva acompanha maior recuperação?

**Evidência executada.** A correlação de Spearman entre cobertura seletiva calculada com população IBGE e recuperação total calculada é 0,888 na amostra principal (n=4.852). Entre os municípios com recuperação positiva, é -0,056 (n=1.529). Com cobertura positiva, 1.410 de 1.414 municípios têm recuperação positiva; com cobertura zero, são 119 de 3.438.

**Conclusão observacional.** O conjunto apresenta associação forte entre presença declarada de cobertura e de recuperação. A hipótese de uma relação positiva geral de intensidade não se sustenta de modo estável quando a análise é restrita aos municípios que já recuperam materiais. As duas amostras respondem a perguntas diferentes e nenhuma é automaticamente superior.

**Limites.** Selecionar apenas resultados positivos muda a população analisada. Cobertura mede população atendida e recuperação mede massa; os indicadores também pertencem à mesma cadeia operacional e fonte administrativa. Não foi estimado um ganho causal de recuperação por ampliar a coleta seletiva. Os modelos ajustados são associativos, não previsões operacionais.

**Evidências.** `analises/diagnostico/correlacoes_sensibilidade.csv`, `cobertura_positiva_recuperacao_zero.csv`, `cobertura_zero_recuperacao_positiva.csv`, `coeficientes_modelos.csv` e `diagnosticos_modelos.csv`; relatório, seções 7 e 8.

## H3 — Vínculos formais na cadeia de resíduos acompanham a recuperação municipal?

**Evidência executada.** A densidade de vínculos no grupo de recuperação de materiais (CNAE 38.3) e a recuperação de resíduos secos têm Spearman de 0,228 (n=4.848). Após controle exploratório de porte, a correlação parcial é 0,198. Nos 584 municípios com ambas as medidas positivas, os coeficientes são 0,216 e 0,055. As tabelas também examinam a divisão 38, contagens absolutas e participação no total formal, identificando separadamente cada medida e amostra.

**Conclusão observacional.** A associação positiva da amostra ampla é limitada e sensível ao porte e à seleção. Os registros podem orientar a investigação da distribuição do trabalho formal no setor. Não permitem afirmar quantos empregos a reciclagem criou, criará ou deveria criar.

**Limites.** Vínculos não são pessoas únicas nem admissões anuais. A atividade principal do estabelecimento não certifica emprego verde ou trabalho decente. Informais, autônomos, empregos em outras CNAEs e prestadores regionais podem não coincidir com o recorte municipal. O controle de porte não elimina diferenças regionais, econômicas ou institucionais.

**Evidências.** `analises/emprego_setorial/associacoes_spearman_com_n.csv`, `descritivas_por_uf.csv`, `descritivas_por_porte_populacional.csv` e `resumo_diagnostico_setorial.json`; relatório, seção 9.

## Novas perguntas geradas e dados necessários

| Questão para investigação posterior | Evidência que a motivou | Informação adicional ou verificação necessária |
|---|---|---|
| Os maiores e menores custos refletem unidades, competência anual, escopo ou contratos diferentes? | A média muda fortemente ao aparar extremos, e 23 registros selecionados coincidem com o arquivo oficial. | Conferência documental dos valores, componentes, contratos e período. Coincidência aritmética não comprova veracidade econômica. |
| O zero de recuperação representa inexistência real, perda total na cadeia ou informação incompleta? | Muitos municípios declaram recuperação zero; há quatro com cobertura positiva e recuperação zero e 119 no padrão inverso. | Frequência e início do serviço, pesagem, triagem, rejeitos, rotas e destino dos materiais. |
| As diferenças permanecem entre municípios de serviço e contexto comparáveis? | Medianas e frequências variam por porte e região; a resposta à pesquisa também difere. | Distância de transporte, densidade urbana, nível de serviço, preço de disposição e características contratuais. |
| Como cooperativas, informalidade e prestadores regionais explicam discrepâncias entre recuperação e estoque formal local? | RAIS e SINISA descrevem unidades e geografias distintas; parte do trabalho não aparece na CNAE 38. | Cadastro local participativo e classificação da atividade, sem tratar zero formal como ausência de trabalho. |
| Um piloto pode melhorar o serviço com custo incremental e condições de trabalho aceitáveis? | As associações atuais não estimam impacto, custo marginal, receita líquida ou criação de vagas. | Definir linha de base, orçamento completo, receita efetiva, massa recuperada/rejeitos, regularidade, renda e segurança antes do piloto. |

Essas perguntas delimitam estudos e verificações futuros. A entrega atual não supõe que esses dados adicionais já tenham sido coletados. A interpretação para gestores e a narrativa do vídeo devem manter a distinção entre observação, recomendação a testar e efeito ainda não demonstrado.
