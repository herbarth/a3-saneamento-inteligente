"""Gera o relatório acadêmico consolidado com dados e evidências executadas.

Dependências: pandas, reportlab e Pillow. Executar na raiz: python scripts/gerar_relatorio.py
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from xml.sax.saxutils import escape

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
import re


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "relatorios" / "Relatorio_A3_Saneamento_Inteligente.pdf"
NAVY = colors.black
TEAL = colors.black
PALE = colors.HexColor("#f2f2f2")
GRAY = colors.black
LEFT = TOP = 3 * 72 / 2.54
RIGHT = BOTTOM = 2 * 72 / 2.54
WIDTH = A4[0] - LEFT - RIGHT


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def publication_line(label, url, status):
    """Mostra somente o estado registrado; a presença de URL não prova validação."""
    text = f"<b>{escape(label)}:</b> {escape(str(status or 'estado não informado'))}."
    if url:
        safe_url = escape(str(url), {'"': "&quot;", "'": "&apos;"})
        if str(url).startswith("https://"):
            text += f' <link href="{safe_url}" color="#000000">{safe_url}</link>'
        else:
            text += f" {safe_url}"
    return text


def br(value, decimals=0):
    if pd.isna(value):
        return "-"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


font, bold = "Helvetica", "Helvetica-Bold"
regular_path, bold_path = Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")
if regular_path.exists() and bold_path.exists():
    pdfmetrics.registerFont(TTFont("ArialA3", str(regular_path)))
    pdfmetrics.registerFont(TTFont("ArialA3-Bold", str(bold_path)))
    pdfmetrics.registerFontFamily("ArialA3", normal="ArialA3", bold="ArialA3-Bold", italic="ArialA3", boldItalic="ArialA3-Bold")
    font, bold = "ArialA3", "ArialA3-Bold"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("BodyA3", fontName=font, fontSize=12, leading=18, textColor=colors.black, alignment=TA_JUSTIFY, firstLineIndent=35.4, spaceAfter=6))
styles.add(ParagraphStyle("SmallA3", parent=styles["BodyA3"], fontSize=10, leading=12, firstLineIndent=0, spaceAfter=8))
styles.add(ParagraphStyle("TitleA3", fontName=bold, fontSize=12, leading=18, textColor=colors.black, alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle("H1A3", fontName=bold, fontSize=12, leading=18, textColor=colors.black, spaceBefore=0, spaceAfter=18, keepWithNext=True))
styles.add(ParagraphStyle("H2A3", fontName=bold, fontSize=12, leading=18, textColor=colors.black, spaceBefore=9, spaceAfter=9, keepWithNext=True))
styles.add(ParagraphStyle("EyebrowA3", fontName=bold, fontSize=12, leading=18, textColor=colors.black, spaceAfter=18, alignment=TA_CENTER))
styles.add(ParagraphStyle("CellA3", fontName=font, fontSize=10, leading=12, firstLineIndent=0, spaceAfter=0))
styles.add(ParagraphStyle("HeaderCellA3", parent=styles["CellA3"], fontName=bold, textColor=colors.black))
styles.add(ParagraphStyle("URLA3", fontName=font, fontSize=10, leading=12, firstLineIndent=0, splitLongWords=True, textColor=colors.black, spaceAfter=12))
styles.add(ParagraphStyle("CoverA3", fontName=font, fontSize=12, leading=18, alignment=TA_CENTER, textColor=colors.black))
styles.add(ParagraphStyle("NatureA3", parent=styles["BodyA3"], leading=12, firstLineIndent=0, leftIndent=WIDTH / 2, spaceAfter=12))
styles.add(ParagraphStyle("RefA3", fontName=font, fontSize=12, leading=12, firstLineIndent=0, alignment=TA_LEFT, spaceAfter=12))
styles.add(ParagraphStyle("RefHeadingA3", fontName=bold, fontSize=12, leading=18, alignment=TA_CENTER, spaceAfter=18, keepWithNext=True))
CURRENT_SECTION = 0
CURRENT_SUBSECTION = 0
TABLE_NUMBER = 0
NUMERIC_TABLE_NUMBER = 0
FRAME_NUMBER = 0
ACADEMIC_META = {}


def p(text, style="BodyA3"):
    global CURRENT_SUBSECTION
    text = text.replace("[R3-R5]", "[3-5]")
    text = re.sub(r"\[R(\d+)\]", r"[\1]", text)
    text = text.replace("página 12", "seção Referências")
    if style == "H2A3" and CURRENT_SECTION:
        CURRENT_SUBSECTION += 1
        text = f"{CURRENT_SECTION}.{CURRENT_SUBSECTION} {text}"
    return Paragraph(text, styles[style])


def title(part, text):
    global CURRENT_SECTION, CURRENT_SUBSECTION
    match = re.match(r"(\d+)\.\s*(.*)", text)
    CURRENT_SECTION = int(match.group(1)) if match else 0
    CURRENT_SUBSECTION = 0
    label = match.group(2) if match else text
    if CURRENT_SECTION == 1:
        label = "Introdução"
    return [p(f"{CURRENT_SECTION} {label.upper()}" if CURRENT_SECTION else label.upper(), "H1A3")]


def table(headers, rows, widths=None):
    global TABLE_NUMBER, NUMERIC_TABLE_NUMBER, FRAME_NUMBER
    TABLE_NUMBER += 1
    data = [[p(str(x), "HeaderCellA3") for x in headers]]
    data += [[p(str(x), "CellA3") for x in row] for row in rows]
    if widths:
        widths = [value * WIDTH / sum(widths) for value in widths]
    obj = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    obj.spaceAfter = 8
    obj.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (0, 0), (-1, 0), .7, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), .5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), .7, colors.black),
    ]))
    labels = ["Delimitação metodológica", "Fontes e extração dos dados", "Variáveis analíticas e escopo", "Verificações de qualidade", "Sensibilidade das despesas", "Despesas e recuperação por região", "Associações ajustadas", "Vínculos formais por atividade", "Prescrições gerenciais"]
    label = labels[TABLE_NUMBER - 1] if TABLE_NUMBER <= len(labels) else "Resultados da análise"
    if TABLE_NUMBER in {5, 6, 8}:
        NUMERIC_TABLE_NUMBER += 1
        designation = f"Tabela {NUMERIC_TABLE_NUMBER}"
    else:
        FRAME_NUMBER += 1
        designation = f"Quadro {FRAME_NUMBER}"
        obj.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .4, colors.black)]))
    return KeepTogether([p(f"{designation} - {label}", "SmallA3"), obj, p("Fonte: elaboração própria com dados SINISA, IBGE e RAIS (2024).", "SmallA3")])


def figure(name, caption, folder="diagnostico", max_height=290):
    path = ROOT / "analises" / folder / name
    width, height = PILImage.open(path).size
    scale = min(WIDTH / width, max_height / height)
    parts = caption.split(". ", 2)
    heading = " - ".join(parts[:2]) if len(parts) > 1 else caption
    note = parts[2] if len(parts) > 2 else "Fonte: elaboração própria com dados de 2024."
    return [p(heading, "SmallA3"), Image(str(path), width=width * scale, height=height * scale), Spacer(1, 5), p(note, "SmallA3")]


def page_footer(canvas, doc):
    if doc.page == 1:
        canvas.saveState()
        canvas.setFont(font, 12)
        canvas.setFillColor(colors.black)
        canvas.drawCentredString(LEFT + WIDTH / 2, BOTTOM, "2026")
        canvas.restoreState()
    if getattr(doc, "text_started", False):
        canvas.saveState()
        canvas.setFont(font, 10)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(A4[0] - RIGHT, A4[1] - 2 * 72 / 2.54, str(doc.page - 1))
        doc._number_drawn_page = doc.page
        canvas.restoreState()


class AcademicDocTemplate(SimpleDocTemplate):
    def beforeDocument(self):
        self.text_started = False
        self._number_drawn_page = None

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in {"H1A3", "H2A3", "RefHeadingA3"}:
            text = flowable.getPlainText()
            if flowable.style.name == "H1A3":
                self.text_started = True
                if getattr(self, "_number_drawn_page", None) != self.page:
                    page_footer(self.canv, self)
            level = 0 if flowable.style.name in {"H1A3", "RefHeadingA3"} else 1
            self.notify("TOCEntry", (level, text, self.page - 1))


def generate():
    global ACADEMIC_META
    OUT.parent.mkdir(parents=True, exist_ok=True)
    dataset_path = ROOT / "data/processed/saneamento_municipios_2024_parcial.csv"
    dataset_bytes = dataset_path.read_bytes()
    dataset_hash = hashlib.sha256(dataset_bytes).hexdigest()
    data = pd.read_csv(dataset_path, dtype={"cod_ibge": "string"})
    validation = read_json(ROOT / "evidencias/validacoes_etl.json")
    diagnosis = read_json(ROOT / "analises/diagnostico/resumo_diagnostico.json")
    sensitivity = pd.read_csv(ROOT / "analises/diagnostico/sensibilidade_amostras.csv")
    regions = pd.read_csv(ROOT / "analises/diagnostico/por_regiao.csv")
    dashboard_test = read_json(ROOT / "evidencias/testes_dashboard.json")
    publication_path = ROOT / "docs/publicacao.json"
    publication = read_json(publication_path) if publication_path.exists() else {}
    sector_summary_path = ROOT / "analises/emprego_setorial/resumo_diagnostico_setorial.json"
    sector_summary = read_json(sector_summary_path) if sector_summary_path.exists() else None
    sector_csv = ROOT / "data/processed/rais_residuos_municipios_2024.csv"
    assert validation["linhas"] == len(data) == 5570
    assert validation["colunas"] == len(data.columns) == 56
    assert set(validation["fontes_realmente_integradas"]) == {"SINISA", "IBGE", "RAIS"}
    assert diagnosis["sha256_dataset"] == dataset_hash, "Atualize o diagnóstico após a última execução do ETL."
    assert dashboard_test["resultado"] == "aprovado"
    assert int(data["vinculos_cnae38_3112"].sum()) == 265143
    base = sensitivity.set_index("amostra").loc["base"]
    trimmed = sensitivity.set_index("amostra").loc["corte_p1_p99_hab"]
    n_sector = int(data["vinculos_cnae38_3112"].gt(0).sum())
    story = []

    meta_path = ROOT / "docs/identificacao_academica.json"
    ACADEMIC_META = read_json(meta_path) if meta_path.exists() else {"curso": "[Curso a informar]", "professor": "[Professor a informar]", "cidade": "[Cidade a informar]", "integrantes": ["[Nomes dos integrantes a informar]"]}
    authors = "<br/>".join(escape(str(name).upper()) for name in ACADEMIC_META["integrantes"])
    main_title = "SANEAMENTO INTELIGENTE"
    subtitle = "Eficiência de custos, reciclagem e oportunidades de emprego verde no Brasil"
    story += [p("UNIFACS", "TitleA3"), p(escape(ACADEMIC_META["curso"].upper()), "CoverA3"), Spacer(1, 54), p(authors, "CoverA3"), Spacer(1, 90), p(main_title, "TitleA3"), p(subtitle, "CoverA3"), Spacer(1, 54), p("Análise de Dados e Big Data<br/>Relatório de apresentação, ETL e análises<br/><br/>Professor: " + escape(ACADEMIC_META["professor"]), "CoverA3")]
    story.append(PageBreak())
    story += [p("SUMÁRIO", "EyebrowA3")]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("TOCPrimary", fontName=bold, fontSize=12, leading=18, spaceBefore=5, textColor=colors.black), ParagraphStyle("TOCSecondary", fontName=font, fontSize=12, leading=18, leftIndent=18, firstLineIndent=0, spaceBefore=0, textColor=colors.black)]
    toc.dotsMinLevel = 0
    story.append(toc)
    story.append(PageBreak())

    # 2 - Apresentação e método.
    story += title("Parte I - Apresentação", "1. Problema, objetivos e desenho")
    story += [p("Problema de pesquisa", "H2A3"), p("Como os municípios brasileiros podem avaliar despesas de manejo de resíduos, recuperação de materiais e vínculos formais da cadeia de resíduos, identificando prioridades de gestão com dados verificáveis?")]
    story += [p("Objetivo geral", "H2A3"), p("Analisar diferenças e associações entre despesas operacionais, cobertura, recuperação e emprego formal setorial para orientar auditoria de informações e decisões de gestão. O termo eficiência no tema orienta a pergunta; não constitui um resultado presumido.")]
    story += [table(["Dimensão", "Definição"], [
        ["Unidade e período", "Uma linha por município e ano; corte transversal de 2024."],
        ["Universo territorial", "5.570 códigos municipais da versão IBGE DOU de 29/08/2024, compatível com a base SINISA selecionada."],
        ["Área e público", "Indicadores Socioeconômicos; gestores municipais e públicos não técnicos."],
        ["Fontes", "SINISA: operação e despesas; IBGE: população; RAIS: estoque formal municipal e por atividade."],
        ["Desenho analítico", "Estatística descritiva, box plots, dispersão, correlação de Spearman, comparação por grupos e modelos associativos com controles."],
    ], [116, WIDTH - 116])]
    story += [p("Hipóteses examinadas", "H2A3"), p("H1: as razões de despesa variam por porte e região? H2: maior cobertura seletiva acompanha maior recuperação? H3: presença de vínculos formais no setor de resíduos acompanha a recuperação municipal? Cada hipótese exige explicitar amostra, denominador e possíveis explicações concorrentes.")]
    story += [p("Limite de inferência", "H2A3"), p("Dados observacionais de um único ano permitem examinar associações, não demonstrar efeitos causais ou tendências. A situação atual pode resultar de história institucional, geografia, preço da disposição, contratos e qualidade dos registros. A predição é opcional no edital e não foi usada como ferramenta operacional nesta versão.")]
    story.append(PageBreak())

    # 3 - Fontes.
    story += title("Parte II - Relatório de ETL", "2. Fontes oficiais e compatibilidade")
    story += [table(["Fonte / arquivo", "Referência e conteúdo", "Extração realizada"], [
        ["SINISA 2025 [R1]", "2024. Despesas, massas, cobertura, indicadores e trabalhadores declarados pelo prestador.", "ZIP oficial com nove planilhas Excel; inspeção de cabeçalhos, códigos e glossários."],
        ["IBGE [R2]", "População estimada em 01/07/2024. Versão DOU de 29/08/2024.", "Arquivo ODS lido por XML; preservação dos códigos, notas e versão."],
        ["RAIS 2024 [R3-R5]", "Vínculos ativos em 31/12/2024; estabelecimento, município e CNAE principal.", "Planilha complementar oficial e microdados de estabelecimentos .7z/.COMT, lidos em blocos."],
    ], [109, 197, WIDTH - 306])]
    story += [p("SINISA e população", "H2A3"), p("A edição SINISA 2025 divulga o ano de referência 2024. Indicadores e informações têm linhas de cabeçalho diferentes; os dados municipais começam na linha 14. O formulário de Manejo inclui linhas adicionais sem código válido, removidas e contabilizadas sem considerá-las municípios excluídos.")]
    story += [p("As versões IBGE DOU e TCU revisada de 30/12/2024 foram comparadas. A versão DOU coincide com DFE0001 nos 5.570 registros do SINISA. A revisão contém Boa Esperança do Norte e diferenças pontuais de população. A escolha DOU mantém a compatibilidade da base principal; não houve redistribuição automática de despesas, massas ou vínculos.")]
    story += [p("RAIS setorial: leitura efetiva e decisão de classificação", "H2A3"), p("O arquivo RAIS_ESTAB_PUB.7z, com 140.661.991 bytes, foi descompactado em RAIS_ESTAB_PUB.COMT (1.431.437.349 bytes). Foram lidos 13.186.059 registros de estabelecimentos declarantes. O formato observado é CSV com vírgulas, aspas duplas e codificação Windows-1252.")]
    story += [p("A coluna rotulada Classe contém códigos de sete dígitos, iguais aos da Subclasse em todos os registros. Para evitar atribuir cinco dígitos a um campo mal rotulado, o ETL usa o campo explicitamente chamado Subclasse e deriva os prefixos. A divisão 38 da CNAE abrange coleta, tratamento e disposição de resíduos e recuperação de materiais [R6].")]
    story.append(PageBreak())

    # 4 - ETL e fórmulas.
    story += title("Parte II - Relatório de ETL", "3. Extração, transformação e carga")
    story += [p("Fluxo executado", "H2A3"), p("1. Obter e preservar arquivos oficiais e hashes. 2. Inspecionar abas, cabeçalhos, unidades e códigos. 3. Padronizar chaves e tipos, preservando ausências. 4. Agregar o estoque RAIS por município e atividade. 5. Integrar por código IBGE com validação de unicidade. 6. Criar indicadores com denominadores positivos. 7. Exportar CSV, dicionários e relatórios de verificação.")]
    story += [p("Chaves e granularidade", "H2A3"), p("O SINISA e o IBGE usam código municipal de sete dígitos. A RAIS usa seis dígitos, associados aos prefixos únicos do código IBGE; UF e cobertura também foram conferidas. As junções municipais são um para um. Abas de rotas ou unidades não foram ligadas diretamente ao resumo municipal, evitando multiplicação de despesas e população.")]
    story += [table(["Variável analítica", "Cálculo e escopo"], [
        ["DEX por residente", "GFI2221 / população IBGE 2024; R$/habitante.ano. Operação do manejo, não investimento."],
        ["DEX por habitante coberto", "IFR2002 oficial: GFI2221 / GTR0201. Denominador de população atendida, distinto de residentes totais."],
        ["DEX por tonelada", "GFI2221 / GTR1028; R$/t. Abrange manejo completo; não custo exclusivo ou marginal de coleta."],
        ["Recuperação total calculada", "100 × GTR1029 / GTR1028. Secos e orgânicos segundo a definição SINISA."],
        ["Cobertura seletiva calculada", "100 × GTR0205 / população IBGE (DOU 29/08/2024), igual a DFE0001 nesta base. Serviço ao menos semanal; não percentual de massa reciclada."],
        ["Vínculos setoriais relativos", "1.000 × estoque CNAE 38 / população; e 100 × CNAE 38 / estoque formal de todos os setores."],
    ], [149, WIDTH - 149])]
    story += [p("Carga e arquivos de saída", "H2A3"), p("A base integrada tem 5.570 municípios, 56 colunas e três fontes efetivamente utilizadas. O arquivo CSV e o dicionário acompanham o projeto. Cada coluna tem origem, código, unidade e disponibilidade registrados. Alertas e campos ausentes permanecem identificados para a revisão.")]
    story.append(PageBreak())

    # 5 - Validações.
    story += title("Parte II - Relatório de ETL", "4. Validações e decisões de qualidade")
    story += [table(["Verificação executada", "Resultado e tratamento"], [
        ["Chave / fontes", "5.570 códigos únicos; SINISA, IBGE e RAIS integrados. Junção por nomes não utilizada."],
        ["Resposta SINISA", "4.854 respondentes e 716 não respondentes, todos preservados no universo. Não resposta continua ausente."],
        ["Massa coletada", "Duas divergências GTR1028 ≠ GTR1025 + GTR1027: São José de Ubá/RJ e Irineópolis/SC. Dados mantidos com alerta."],
        ["Indicadores", "Denominadores positivos, ausência de infinito e limites percentuais verificados; reprodução de IRS3010 tolera 0,02 ponto de arredondamento."],
        ["RAIS completa", "13.186.059 declarantes e 57.132.156 vínculos ativos reconciliam com o Brasil oficial; todos os 5.570 totais municipais conferem com a TABELA 4."],
        ["Consistência setorial", "Inteiros não negativos; divisão 38 não excede total formal; três grupos somam a divisão em cada município."],
    ], [151, WIDTH - 151])]
    story += [p("Ausência e zero têm significados diferentes", "H2A3"), p("No SINISA, branco ou null pode refletir não declaração ou não resposta; não foi substituído por zero. Na RAIS setorial, os zeros municipais foram atribuídos apenas depois de ler e validar o universo completo: representam ausência de vínculo ativo registrado nas atividades selecionadas, não ausência de trabalho informal ou de reciclagem.")]
    story += [p("Compatibilidade territorial e totais não localizados", "H2A3"), p("A RAIS inclui Boa Esperança do Norte (945 vínculos totais e zero na divisão 38), fora do universo DOU selecionado. Há 10.899 vínculos totais com município não identificado; oito deles pertencem à divisão 38, todos em recuperação de materiais. Esses registros permanecem separados. As taxas de quatro municípios de Mato Grosso que cederam território ficam suspensas até harmonização.")]
    story.append(PageBreak())

    # 6 - Sensibilidade.
    story += title("Parte III - EDA e diagnóstico", "5. Custos: a média depende dos extremos")
    story += [p(f"Na amostra principal, a média municipal da DEX por residente é <b>R$ {br(base.custo_hab_media, 2)}</b> e a mediana é <b>R$ {br(base.custo_hab_mediana, 2)}</b>. Manter apenas P1-P99 reduz a média a <b>R$ {br(trimmed.custo_hab_media, 2)}</b>, enquanto a mediana permanece em <b>R$ {br(trimmed.custo_hab_mediana, 2)}</b>. A mudança da média é -61,82%; o corte é diagnóstico, não retificação da fonte.")]
    rows = []
    for name, label in [("base", "Principal"), ("corte_p1_p99_hab", "P1-P99 por residente"), ("recuperacao_positiva", "Recuperação positiva")]:
        row = sensitivity.set_index("amostra").loc[name]
        rows.append([label, br(row.n), br(row.custo_hab_media, 2), br(row.custo_hab_mediana, 2), br(row.custo_t_mediana, 2)])
    story += [table(["Amostra", "n", "Média R$/hab", "Mediana R$/hab", "Mediana R$/t"], rows, [WIDTH * .25, WIDTH * .1, WIDTH * .22, WIDTH * .22, WIDTH * .21])]
    story += figure("01_custos_extremos_sensibilidade.png", "Figura 1. Sensibilidade das despesas aos extremos. Fonte: elaboração a partir do SINISA e IBGE; amostras e limites registrados nos CSVs do diagnóstico.", max_height=225)
    story += [p("A conferência de 23 registros extremos não encontrou diferença de DEX entre a base e o arquivo original. Em Várzea Grande/PI, a fonte declara R$ 550,2 milhões para 4.515 residentes. Os 49 valores acima de P99 concentram 35,41% da DEX e 0,89% da população da amostra. Esses montantes exigem auditoria de unidade, período, escopo e contratos; não foram corrigidos por suposição.")]
    story += [p("Retirar o mesmo número de observações de cada cauda preserva a posição central. A mediana igual após o corte simétrico não valida os registros de forma independente.", "SmallA3")]
    story.append(PageBreak())

    # 7 - Porte e região com figura inteira em largura útil.
    story += title("Parte III - EDA e diagnóstico", "6. Comparar exige considerar porte e região")
    story += figure("02_custos_por_porte.png", "Figura 2. DEX por residente por porte, após corte P1-P99. O box plot apresenta mediana e dispersão; pontos além dos bigodes ficam ocultos apenas nesta figura e permanecem nos CSVs. Fonte: SINISA e IBGE, elaboração do projeto.", max_height=286)
    rows = [[r.regiao, br(r.n), br(r.custo_hab_mediana, 2), br(r.recuperacao_positiva_pct, 2) + "%"] for r in regions.itertuples()]
    story += [table(["Região", "n principal", "Mediana DEX R$/hab", "Recuperação positiva"], rows, [123, 89, 146, WIDTH - 358])]
    story += [p("As medianas regionais e a frequência de recuperação diferem. Elas descrevem os respondentes elegíveis; não são metas de gasto nem estimativas representativas de todos os municípios. A base não contém distância de transporte, densidade urbana, preço de destinação ou qualidade contratual, possíveis explicações concorrentes.")]
    story += [p("Para investigação gerencial, selecionar municípios do mesmo porte e região e conferir o escopo. As tabelas por_regiao_porte.csv e por_regiao_porte_corte_p1_p99.csv mostram também o tamanho de cada célula. Células pequenas exigem leitura individual.", "SmallA3")]
    story.append(PageBreak())

    # 8 - Recuperação.
    story += title("Parte III - EDA e diagnóstico", "7. Coleta seletiva: presença e intensidade")
    story += [p(f"Dos {br(diagnosis['n_principal'])} municípios da amostra principal, <b>{br(diagnosis['recuperacao_zero_n'])} ({br(diagnosis['recuperacao_zero_pct'], 2)}%)</b> declaram recuperação zero e <b>{br(diagnosis['seletiva_zero_n'])} ({br(diagnosis['seletiva_zero_pct'], 2)}%)</b> declaram cobertura seletiva zero. A correlação de Spearman entre as razões recalculadas de cobertura e recuperação é <b>0,888</b> no conjunto e <b>-0,056</b> apenas entre os 1.529 com recuperação positiva.")]
    story += figure("03_cobertura_recuperacao.png", "Figura 3. Associação transversal entre cobertura seletiva e recuperação declarada; a inclusão de muitos zeros influencia a leitura. As faixas no painel direito mostram médias e medianas com seus n. Fonte: SINISA e IBGE, elaboração do projeto.", max_height=275)
    story += [p("As duas correlações respondem a perguntas diferentes. A primeira distingue fortemente presença de ausência declarada; a segunda investiga intensidade entre municípios que já declaram recuperação. Restringir a positivos também seleciona outra população e pode favorecer melhores capacidades de registro.")]
    story += [p("Com cobertura seletiva positiva, 1.410 de 1.414 municípios têm recuperação positiva (99,72%). Com cobertura zero, 119 de 3.438 têm recuperação positiva (3,46%). Os quatro casos com cobertura positiva e recuperação zero e os 119 do padrão inverso foram listados para investigar conceitos, frequência, rotas, pesagem e rejeitos.")]
    story += [p("Neste diagnóstico, cobertura e recuperação são recalculadas; painel e estudo de emprego usam as oficiais SINISA. Cobertura mede população, e recuperação, massa anual. Orgânicos seguem a rota à compostagem, não o rendimento de composto. A fonte operacional comum limita inferências causais.", "SmallA3")]
    story.append(PageBreak())

    # 9 - Modelos.
    story += title("Parte III - EDA e diagnóstico", "8. Associações ajustadas e seus limites")
    story += [p("Foram estimados modelos lineares exploratórios da recuperação, em pontos percentuais, com cobertura seletiva, logaritmos de DEX por residente e população e indicadores para cada UF. Os intervalos usam erros agrupados por UF, correção de amostra finita e distribuição t com G-1 graus de liberdade. São comparações condicionais, não estimativas de impacto.")]
    story += figure("04_associacao_ajustada_sensibilidade.png", "Figura 4. Sensibilidade da associação ajustada de cobertura em diferentes amostras. Os intervalos refletem as premissas do modelo; não corrigem erro administrativo, seleção de respondentes ou fatores omitidos.", max_height=250)
    story += [table(["Comparação associativa", "Estimativa e leitura"], [
        ["+10 pontos de cobertura", "Amostra principal: +0,80 pp de recuperação (IC95%: 0,57 a 1,02; n=4.852). Apenas recuperação positiva: -0,61 pp (-1,11 a -0,12; n=1.529)."],
        ["Duplicação da DEX por residente", "Amostra principal: -0,01 pp (-0,11 a 0,09). No corte P1-P99: 0,00 pp (-0,10 a 0,11). Não há base para prometer ganho por ampliar ou cortar despesas."],
        ["Contexto do emprego formal", "O controle por vínculos de todos os setores por mil residentes mantém a associação de cobertura em +0,80 pp; n=4.848 pelas quatro ressalvas territoriais."],
    ], [153, WIDTH - 153])]
    story += [p("Não foi usado custo por tonelada versus recuperação como prova de efeito: ambos dividem pela massa coletada, podendo gerar associação por denominador comum. OLS pode produzir valores ajustados fora de 0%-100%; os diagnósticos estão preservados e o modelo não foi usado para prever operação ou estabelecer metas.", "SmallA3")]
    story.append(PageBreak())

    # 10 - Emprego setorial.
    story += title("Parte III - EDA e diagnóstico", "9. Emprego formal na cadeia de resíduos")
    story += [p(f"A leitura integral da RAIS encontrou <b>265.151 vínculos ativos</b> na divisão 38 em todo o Brasil. Os {br(len(data))} códigos do conjunto principal somam <b>265.143</b>; a diferença são oito vínculos sem município identificado, no grupo de recuperação. Há <b>{br(n_sector)} municípios</b> com estoque setorial positivo.")]
    story += [table(["Atividade", "Brasil, com não identificado", "Universo municipal do projeto"], [
        ["Coleta (38.1)", "198.344", br(data["vinculos_coleta_381_3112"].sum())],
        ["Tratamento e disposição (38.2)", "23.856", br(data["vinculos_tratamento_382_3112"].sum())],
        ["Recuperação de materiais (38.3)", "42.951", br(data["vinculos_recuperacao_383_3112"].sum())],
        ["Divisão 38", "265.151", br(data["vinculos_cnae38_3112"].sum())],
    ], [169, 166, WIDTH - 335])]
    story += [p("O que esse recorte mede", "H2A3"), p("Estoque ativo em 31/12/2024, por município e atividade principal do estabelecimento. Não são pessoas únicas ou novas vagas. A divisão inclui resíduos urbanos, industriais e perigosos; outras atividades ambientais podem ficar em CNAEs diferentes.")]
    sector_doc_path = ROOT / "docs/EMPREGO_SETORIAL_ANALISE.md"
    if sector_summary:
        story += [p("Diagnóstico setorial complementar", "H2A3"), p("Em 3.782 municípios, o estoque CNAE 38 é zero, sem comprovar ausência de trabalho informal. Vínculos na recuperação de materiais por mil habitantes e recuperação de secos (SINISA oficial) têm Spearman de 0,228 (n=4.848), ou 0,198 após controle exploratório de porte. Nos 584 com ambas as medidas positivas, os coeficientes são 0,216 e 0,055. As subamostras selecionam populações diferentes; não estimam vagas criadas por reciclagem. Métodos e tabelas acompanham o estudo setorial.")]
    story += [p("Emprego verde: limites e aspectos negativos", "H2A3"), p("A CNAE não certifica benefício ambiental, segurança, renda ou trabalho decente. Catadores informais, autônomos e empregos em prefeituras classificados em administração pública podem ficar fora do recorte. A associação com recuperação não identifica criação líquida de vagas. Automação e exigências contratuais podem deslocar tarefas ou excluir trabalhadores; inclusão e capacitação precisam acompanhar qualquer proposta.")]
    story.append(PageBreak())

    # 11 - Prescrições.
    story += title("Parte III - Prescrições", "10. Ações propostas com evidência e verificação")
    story += [table(["Evidência", "Ação gerencial proposta", "Acompanhamento e limite"], [
        ["Média sensível à cauda; extremos conferem com o bruto.", "Auditar primeiro unidades, competência anual, escopo e contratos dos extremos e os dois alertas de massa.", "Registrar confirmação ou retificação; percentil prioriza a auditoria, não prova erro. Suspender metas de economia desses casos."],
        ["Custos diferem por porte e região.", "Escolher municípios comparáveis e usar mediana e quartis como referência de investigação.", "Conferir cobertura, rotas, distância, toneladas pesadas e preço da disposição. Não atribuir toda diferença a desperdício."],
        ["3.323 municípios declaram recuperação zero; padrões de cobertura e massa divergem.", "Conferir o significado do zero e a cadeia de pesagem, triagem, tratamento e destino; planejar piloto mensurável.", "Separar secos e orgânicos; acompanhar regularidade, contaminação, rejeitos e massa efetivamente encaminhada."],
        ["Recuperação não demonstra redução causal da despesa.", "Orçar um piloto incluindo implantação, operação, transporte, disposição de rejeitos e receita real dos materiais.", "Comparar custo incremental e qualidade. Não presumir que a venda de materiais pagará o serviço."],
        ["RAIS descreve estoque formal setorial, com lacunas do trabalho informal.", "Combinar diagnóstico agregado com cadastro local de cooperativas e trabalhadores, de forma participativa.", "Acompanhar formalização, renda, segurança e inclusão. Não converter correlação em previsão de vagas ou corte de pessoal."],
    ], [130, 184, WIDTH - 314])]
    story += [p("Condições para testar as propostas", "H2A3"), p("Escolher cenário de referência, período de acompanhamento e indicadores antes do piloto. Custos de implantação e manutenção, demanda por recicláveis, segurança ocupacional e capacidade das cooperativas podem reduzir o benefício líquido. Avaliar acessibilidade do serviço e efeitos sobre tarefas e renda, além da massa recuperada.")]
    story += [PageBreak()] + title("Conclusão", "11. Considerações finais")
    story += [p("A integração tornou verificáveis três frentes do tema: despesa, recuperação e emprego formal. O resultado mais sólido é a necessidade de melhorar a qualidade e a comparabilidade antes de estabelecer metas. Os extremos alteram fortemente a média, e a mediana exige a ressalva da aparação simétrica. Cobertura e intensidade de recuperação respondem a perguntas diferentes. O estoque formal da cadeia pode orientar investigação local, com a informalidade explicitamente fora de parte da medição. Nenhuma dessas evidências autoriza prometer economia ou geração causal de empregos.")]
    story += [p("Como contribuição aplicada, o projeto organiza informações de três fontes públicas em uma unidade municipal comum, conserva os problemas de qualidade e oferece indicadores com definições e amostras explícitas. A agenda de gestão decorrente consiste em auditar registros extremos, escolher comparáveis adequados e testar intervenções com orçamento e acompanhamento de serviços e trabalhadores. Estudos posteriores podem ampliar a série temporal e incorporar distância, contratos, perdas de triagem e condições de trabalho, desde que a compatibilidade das fontes seja novamente verificada.")]
    story += [p("Síntese das hipóteses e novas questões", "H2A3"), p("H1 apresentou diferenças descritivas de despesa por porte e região. H2 mostrou associação entre presença de cobertura seletiva e recuperação, sem relação positiva estável de intensidade nas subamostras. H3 identificou associação limitada entre vínculos formais e recuperação, sensível ao porte e à seleção. Esses resultados não provam causas nem criação de vagas.")]
    story += [p("As novas questões são verificar o significado dos custos extremos e dos zeros, explicar diferenças entre serviços comparáveis e investigar o trabalho formal e informal com cadastro local. Um piloto deverá medir custo incremental, materiais e condições de trabalho antes de avaliar benefícios. A matriz de evidências e os dados adicionais necessários estão em docs/HIPOTESES_E_QUESTOES.md.", "SmallA3")]
    story.append(PageBreak())

    # 12 - Reprodução, estado e referências com URLs oficiais.
    story += title("Reprodução", "12. Evidências e disponibilização")
    story += [p("Arquivos de reprodução", "H2A3"), p("scripts/etl.py e scripts/extrair_rais_setorial.py: transformação e integração. scripts/diagnostico.py: amostras, auditoria e modelos. app.py: painel. docs/dicionario_dataset_completo.csv: códigos, unidades e cobertura. evidencias/: hashes e validações. analises/diagnostico/ e analises/emprego_setorial/: tabelas, figuras e resumos. Os microdados RAIS descompactados, com 1,43 GB, ficam fora do repositório; a origem e o hash permitem obtê-los novamente.", "SmallA3")]
    story += [p(f"Base desta versão: {br(len(data))} × {len(data.columns)}. SHA256:<br/>{dataset_hash}", "SmallA3")]
    story += [p("Estado real da disponibilização", "H2A3"), p(f"O dashboard foi executado localmente e aprovado em {len(dashboard_test['cenarios'])} cenários AppTest: filtros, não respondente, critérios de qualidade, controles visuais e download. Esses testes são registrados separadamente da validação do acesso público.", "SmallA3")]
    story += [p("<br/>".join([
        publication_line("GitHub", publication.get("github_url"), publication.get("github_status")),
        publication_line("Dashboard online", publication.get("dashboard_url"), publication.get("dashboard_status", "publicação ainda não registrada")),
        publication_line("Vídeo YouTube de até sete minutos", publication.get("video_url"), publication.get("video_status", "última etapa conforme o grupo; ainda não produzido")),
    ]), "SmallA3")]
    story += [p("O registro de disponibilização é lido de docs/publicacao.json. Os links e seus estados devem ser conferidos antes da entrega de 03/12/2026.", "SmallA3")]
    refs = [
        ("R1", "BRASIL. Ministério das Cidades. Resultados SINISA 2025: ano de referência 2024. Brasília, DF: Ministério das Cidades, 2025.", "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025"),
        ("R2", "IBGE. Estimativas da população residente para os municípios: 2024. Rio de Janeiro: IBGE, 2024.", "https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/"),
        ("R3", "BRASIL. Ministério do Trabalho e Emprego. Microdados RAIS e CAGED. Brasília, DF: MTE, 2025.", "https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/microdados-rais-e-caged"),
        ("R4", "BRASIL. Ministério do Trabalho e Emprego. RAIS ano-base 2024: microdados públicos de estabelecimentos. Brasília, DF: MTE, 2026. Arquivo republicado em 18 maio 2026.", "ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/2024/RAIS_ESTAB_PUB.7z"),
        ("R5", "BRASIL. Ministério do Trabalho e Emprego. RAIS 2024: divulgação complementar: tabelas 2023 e 2024. Brasília, DF: MTE, 2025.", "https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1/rais-complementar-tabelas-2023x2024.xlsx"),
        ("R6", "IBGE. Comissão Nacional de Classificação. Estrutura detalhada da CNAE e CNAE Fiscal 2.0. Rio de Janeiro: IBGE, [s.d.].", "https://concla.ibge.gov.br/images/concla/documentacao/EstruturaDetalhadaCNAE_CNAEFiscal2_Atualizada.pdf"),
    ]
    story += [PageBreak(), p("REFERÊNCIAS", "RefHeadingA3")]
    for label, description, url in refs:
        story += [p(f"[{label.replace('R', '')}] {escape(description)} Disponível em: <link href='{escape(url)}' color='#000000'>{escape(url)}</link>. Acesso em: 20 nov. 2026.", "RefA3")]

    doc = AcademicDocTemplate(str(OUT), pagesize=A4, rightMargin=RIGHT, leftMargin=LEFT, topMargin=TOP, bottomMargin=BOTTOM,
                            title="Saneamento Inteligente - Relatório A3", author="Equipe do projeto A3", subject="Apresentação, ETL, EDA, diagnóstico e prescrições - UNIFACS")
    doc.multiBuild(story, onFirstPage=page_footer, onLaterPages=page_footer)
    manifest = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(), "arquivo": str(OUT.relative_to(ROOT)),
        "sha256_pdf": hashlib.sha256(OUT.read_bytes()).hexdigest(), "sha256_dataset": dataset_hash,
        "dataset_linhas": len(data), "dataset_colunas": len(data.columns),
        "diagnostico_sha256_dataset": diagnosis["sha256_dataset"],
        "resumo_setorial_disponivel": sector_summary is not None,
        "fontes": ["SINISA", "IBGE", "RAIS"], "data_contexto_usuario": "2026-11-20",
        "formatacao": "Apresentação acadêmica formal, com capa, sumário, seções, tabelas e referências; edital e checklist são as referências obrigatórias. ABNT estrita não exigida.",
        "publicacao": {key: publication.get(key) for key in ("github_url", "github_status", "dashboard_url", "dashboard_status", "video_url", "video_status")},
    }
    (OUT.parent / "manifesto_relatorio.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    generate()
