# Reprodução do relatório

O relatório de 24/11/2026 segue as dez seções do template do professor. Os dados, cálculos, tabelas e figuras são lidos das evidências e da base municipal do projeto. Os dois geradores abaixo usam o mesmo conteúdo estruturado.

Na raiz do projeto, com as dependências de `requirements.txt` instaladas:

```bash
python scripts/gerar_relatorio.py
python scripts/gerar_relatorio_word.py
```

O primeiro comando gera um PDF com ReportLab e atualiza o manifesto dessa exportação. O segundo gera o Word com tabelas editáveis, links e campo de sumário. Ele não atualiza os campos nem exporta o Word para PDF.

Antes de distribuir uma nova edição, abra o Word, atualize o sumário e os campos, confira todas as páginas e exporte o PDF a partir desse mesmo arquivo. A edição entregue foi exportada no Microsoft Word 16 e teve suas 35 páginas inspecionadas; o PDF gerado pelo ReportLab pode ter paginação diferente. Não atribua essa aprovação a uma edição regenerada sem nova conferência. Registre novamente os hashes no manifesto e nas evidências depois da exportação final.

Para gerar uma cópia de teste sem substituir o arquivo entregue, defina `A3_WORD_OUTPUT_PATH` para outro destino. Para o PDF, use `A3_REPORT_OUTPUT_PATH`. `A3_PROJECT_ROOT` permite apontar ambos para outra cópia completa do projeto.

Os nomes e as matrículas dos cinco integrantes foram informados pelo usuário e são mantidos em `docs/identificacao_academica.json`. A matrícula de Pedro deve ser conferida antes da entrega; até lá, permanece exatamente como enviada. Alterações posteriores devem ser registradas nesse arquivo antes da nova geração. O link e a duração real do vídeo permanecem pendentes e devem ser conferidos depois da gravação. O roteiro de fala e o guia do grupo são distribuídos separadamente, fora do repositório público.

Os anexos integrais do professor ficam apenas no pacote técnico local, em `evidencias/anexos_professor/`. As versões de referência são identificadas por título e hash nas evidências públicas da revisão. Os cálculos e a base preservam os registros de validação anteriores; a revisão documental não representa nova extração dos microdados RAIS.
