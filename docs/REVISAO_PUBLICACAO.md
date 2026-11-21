# Revisão para publicação

Revisão local em 20/11/2026, anterior à validação do endereço público.

- O aplicativo usa caminhos relativos ao próprio `app.py`. Para abrir o painel, o único arquivo de dados obrigatório é `data/processed/saneamento_municipios_2024_parcial.csv`. A tabela `evidencias/validacoes_por_municipio.csv` acrescenta a consulta de alertas.
- Não foram identificados caminhos do perfil pessoal ou padrões de credenciais nos arquivos de texto candidatos ao repositório, após normalizar cinco campos de caminho em três JSONs de evidência. Métricas, datas e hashes dos dados foram preservados.
- O `.gitignore` foi ampliado para excluir caches, arquivos temporários, segredos locais, dados brutos e os anexos originais de avaliação. As fontes oficiais permanecem identificadas por URL e SHA256. Os agregados municipais não contêm identificadores individuais de trabalhadores.
- O painel não depende de fontes tipográficas do Windows. O gerador do relatório usa Arial quando disponível e possui alternativa Helvetica. Não foi executado teste em Linux nesta revisão; selecionar Python 3.12 na hospedagem preserva a versão principal usada na execução local.
- Antes de considerar a publicação concluída, conferir o carregamento do endereço público, os filtros e a exportação CSV. A aprovação dos testes locais não substitui essa conferência.

Os geradores de diagnóstico e de metadados RAIS foram ajustados para registrar caminhos relativos ao projeto em novas execuções. Para arquivos externos ao projeto, registram somente o nome do arquivo. A sintaxe dos dois scripts foi compilada, sem executar os geradores. As fórmulas, os filtros e a leitura dos dados não foram alterados; nenhuma análise foi reexecutada nesta revisão.
