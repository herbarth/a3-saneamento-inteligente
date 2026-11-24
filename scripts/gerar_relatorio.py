"""Gera o relatório acadêmico consolidado com dados e evidências executadas.

Dependências: pandas, reportlab e Pillow. Executar na raiz: python scripts/gerar_relatorio.py
"""
from pathlib import Path
import os
import ast
import copy
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


_HERE = Path(__file__).resolve().parent
_DEFAULT_ROOT = Path(__file__).resolve().parents[1]
if not (_DEFAULT_ROOT / "data/processed/saneamento_municipios_2024_parcial.csv").exists():
    _DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "outputs/saneamento-inteligente-a3"
ROOT = Path(os.environ.get("A3_PROJECT_ROOT", str(_DEFAULT_ROOT)))
_STAGED = _HERE.name == "revisao_24"
OUT = Path(os.environ.get("A3_REPORT_OUTPUT_PATH", str(_HERE / "Relatorio_A3_revisado.pdf" if _STAGED else ROOT / "relatorios/Relatorio_A3_Saneamento_Inteligente.pdf")))
ASSET_DIR = OUT.parent / "assets_relatorio" if _STAGED else ROOT / "analises/diagnostico"
ASSET_DIR.mkdir(parents=True, exist_ok=True)
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


def original_generate():
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




# Revision following the professor's final-report structure. The original flowables
# above are retained as the authoritative library of already-validated findings.
def _capture_original():
    tree = ast.parse(Path(__file__).read_text(encoding='utf-8-sig'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'original_generate')
    body=[]
    for stmt in fn.body:
        if isinstance(stmt, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='doc' for t in stmt.targets):
            break
        body.append(stmt)
    fn.name='_read_original_story'
    fn.body=body+[ast.Return(value=ast.Name(id='story',ctx=ast.Load()))]
    model=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(model)
    exec(compile(model,str(__file__),'exec'),globals())
    return _read_original_story()


_ORIGINAL_STORY = _capture_original()
_ORIGINAL_SECTIONS={}
_old_number=0
for _flowable in _ORIGINAL_STORY:
    if isinstance(_flowable,Paragraph) and _flowable.style.name=='H1A3':
        _old_number=int(re.match(r'(\d+)',_flowable.getPlainText()).group(1))
    _ORIGINAL_SECTIONS.setdefault(_old_number,[]).append(_flowable)


def old_p(section, fragment):
    found=[x for x in _ORIGINAL_SECTIONS[section] if isinstance(x,Paragraph) and fragment in x.text and x.style.name in {'BodyA3','SmallA3'}]
    assert len(found)==1,(section,fragment,len(found))
    return copy.deepcopy(found[0])


def old_table(fragment):
    found=[x for x in _ORIGINAL_STORY if isinstance(x,KeepTogether) and any(isinstance(c,Paragraph) and fragment in c.getPlainText() for c in x._content)]
    assert len(found)==1,(fragment,len(found))
    return copy.deepcopy(found[0])


def h1(number,text):
    return Paragraph(f'{number} {text.upper()}',styles['H1A3'])


def h2(number,text):
    return Paragraph(f'{number} {text}',styles['H2A3'])


def new_table(headers,rows,widths,label,numeric=False):
    widths=[x*WIDTH/sum(widths) for x in widths]
    cells=[[p(str(x),'HeaderCellA3') for x in headers]]+[[p(str(x),'CellA3') for x in row] for row in rows]
    tab=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1)
    tab.spaceAfter=8
    tab.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#F2F2F2')),
        ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    kind='Tabela' if numeric else 'Quadro'
    return KeepTogether([p(f'{kind} @ - {label}','SmallA3'),tab,p('Fonte: elaboração própria com dados SINISA, IBGE e RAIS (2024).','SmallA3')])


def wrap_code(value,limit=25):
    tokens=str(value).split('_');parts=[];line=''
    for i,token in enumerate(tokens):
        token=token+('_' if i<len(tokens)-1 else '')
        if line and len(line)+len(token)>limit:
            parts.append(line);line=''
        line+=token
    if line:parts.append(line)
    return '<br/>'.join(escape(x) for x in parts)


def asset_figure(path,title_text,note,max_height=255):
    iw,ih=PILImage.open(path).size
    scale=min(WIDTH/iw,max_height/ih)
    return [p('Figura @ - '+title_text,'SmallA3'),Image(str(path),width=iw*scale,height=ih*scale),Spacer(1,5),p(note,'SmallA3')]


def _make_report_assets(sample):
    from PIL import Image as Im,ImageDraw,ImageFont
    canvas=Im.new('RGB',(1800,1080),'white');draw=ImageDraw.Draw(canvas)
    fpath='C:/Windows/Fonts/arial.ttf'
    fp='C:/Windows/Fonts/arialbd.ttf'
    if Path(fpath).exists() and Path(fp).exists():
        regular=ImageFont.truetype(fpath,38);boldface=ImageFont.truetype(fp,40)
    else:
        try:
            from matplotlib import font_manager
            regular=ImageFont.truetype(font_manager.findfont('DejaVu Sans'),38)
            boldface=ImageFont.truetype(font_manager.findfont(font_manager.FontProperties(family='DejaVu Sans',weight='bold')),40)
        except (ImportError,OSError):
            regular=ImageFont.load_default(size=38);boldface=ImageFont.load_default(size=40)
    def box(x0,y0,x1,y1,text,font=regular):
        draw.rounded_rectangle((x0,y0,x1,y1),radius=10,fill='#F3F3F3',outline='#333333',width=3)
        draw.multiline_text(((x0+x1)/2,(y0+y1)/2),text,font=font,fill='black',anchor='mm',align='center',spacing=10)
    def arrow(x0,y0,x1,y1):
        draw.line((x0,y0,x1,y1),fill='#333333',width=4)
        draw.polygon([(x1,y1),(x1-13,y1-20),(x1+13,y1-20)],fill='#333333')
    for x,t in [(50,'SINISA 2025\nReferência 2024'),(625,'IBGE\nPopulação de 2024'),(1200,'RAIS\nEstoque de 2024')]:
        box(x,20,x+550,160,t,boldface)
    for center in (325,900,1475):
        draw.line((center,160,center,205,900,205),fill='#333333',width=4)
    arrow(900,205,900,250)
    steps=[('Extração e preparação','Arquivos oficiais, códigos, tipos e unidades'),
           ('Transformação e integração','RAIS agregada e junções municipais um para um'),
           ('Indicadores e validações','Denominadores, somas, ausências e alertas'),
           ('Carga e documentação','CSV 5.570 × 56, dicionário e evidências')]
    for i,(a,b) in enumerate(steps):
        y=250+i*205
        box(250,y,1550,y+145,a+'\n'+b)
        if i<len(steps)-1:arrow(900,y+145,900,y+205)
    flow=ASSET_DIR/'00_fluxo_etl.png';canvas.save(flow)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'Arial' if Path(fpath).exists() else 'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    made={}
    fig,ax=plt.subplots(figsize=(6.4,3.1));ax.hist(np.log10(sample['despesa_manejo_por_hab_ibge2024']),bins=40,color='#666666',edgecolor='white')
    ax.set_xlabel('log10 da DEX por residente (R$/hab.ano)');ax.set_ylabel('Municípios');fig.tight_layout()
    made['hist']=ASSET_DIR/'05_histograma_despesas.png';fig.savefig(made['hist'],dpi=220);plt.close(fig)
    region_order=['Norte','Nordeste','Sudeste','Sul','Centro-Oeste']
    fig,ax=plt.subplots(figsize=(6.4,3.1));ax.boxplot([sample.loc[sample.regiao.eq(r),'despesa_manejo_por_hab_ibge2024'] for r in region_order],tick_labels=region_order,showfliers=False)
    ax.set_ylabel('DEX por residente (R$/hab.ano)');ax.tick_params(axis='x',labelsize=10);fig.tight_layout()
    made['box']=ASSET_DIR/'06_boxplot_despesas_regiao.png';fig.savefig(made['box'],dpi=220);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.4,3.1));ax.scatter(sample['despesa_manejo_por_hab_ibge2024'],sample['recuperacao_total_calculada_pct'],s=10,alpha=.35,color='#555555',linewidths=0)
    ax.set_xscale('log');ax.set_xlabel('DEX por residente (R$/hab.ano, escala log)');ax.set_ylabel('Recuperação total (%)');fig.tight_layout()
    made['scatter']=ASSET_DIR/'07_dispersao_despesa_recuperacao.png';fig.savefig(made['scatter'],dpi=220);plt.close(fig)
    made['flow']=flow
    return made


def _renumber(story):
    counts={'Figura':0,'Tabela':0,'Quadro':0}
    def walk(items):
        result=[]
        for item in items:
            if isinstance(item,KeepTogether):
                item._content=walk(item._content)
            elif isinstance(item,Paragraph):
                match=re.match(r'^(Figura|Tabela|Quadro) (?:@|\d+)(?:\.| -)\s*(.*)',item.text)
                if match:
                    kind,label=match.groups();counts[kind]+=1
                    item=Paragraph(f'{kind} {counts[kind]} - {label}',item.style)
            result.append(item)
        return result
    return walk(story),counts


def generate():
    dataset_path=ROOT/'data/processed/saneamento_municipios_2024_parcial.csv'
    dataset_hash=hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    data=pd.read_csv(dataset_path,dtype={'cod_ibge':'string'})
    sample=data.loc[data.apta_analise_custo_recuperacao.eq(True)].copy()
    assert data.shape==(5570,56) and len(sample)==4852
    assert dataset_hash=='f2529c8660ff8df47664a2b850a6be7cfbcb5dcc44261dc781249fe5bf7530de'
    publication=read_json(ROOT/'docs/publicacao.json')
    meta=read_json(ROOT/'docs/identificacao_academica.json')
    names=meta.get('integrantes',[])
    real_names=[(i,n) for i,n in enumerate(names) if 'informar' not in str(n).casefold() and '[' not in str(n)]
    matriculas=meta.get('matriculas',[])
    team_text='<br/>'.join(escape(str(n))+'<br/>RA/Matrícula: '+escape(str(matriculas[i] if i<len(matriculas) else '[RA/matrícula a informar]')) for i,n in real_names) if real_names else 'Equipe: nomes completos e RA/Matrículas a informar.<br/>Composição da equipe: a confirmar.'
    dictionary=pd.read_csv(ROOT/'docs/dicionario_dataset_completo.csv').fillna('')
    assert len(dictionary)==56 and set(dictionary.coluna)==set(data.columns)
    figures=_make_report_assets(sample)
    stats_cols=['despesa_manejo_por_hab_ibge2024','despesa_manejo_por_t_rsu','cobertura_seletiva_ibge2024_pct','recuperacao_total_calculada_pct']
    descriptions=sample[stats_cols].describe(percentiles=[.25,.5,.75]).T
    prior_stats=pd.read_csv(ROOT/'analises/diagnostico/estatisticas_por_amostra.csv')
    prior_stats=prior_stats.loc[prior_stats.amostra.eq('base')].set_index('variavel')
    for c in stats_cols:
        for key in ['count','mean','std','min','25%','50%','75%','max']:
            assert abs(float(descriptions.loc[c,key])-float(prior_stats.loc[c,key]))<=max(1e-9,abs(float(prior_stats.loc[c,key]))*1e-12)
    story=[]
    # Capa e identificação sem inventar quantidade, nomes ou matrículas.
    story += [p('UNIFACS','TitleA3'),p(escape(meta['curso'].upper()),'CoverA3'),Spacer(1,26),p('SANEAMENTO INTELIGENTE','TitleA3'),p('Eficiência de custos, reciclagem e oportunidades de emprego verde no Brasil','CoverA3'),Spacer(1,22),p('PROJETO A3 RELATÓRIO FINAL','TitleA3'),p('Unidade Curricular: Análise de Dados e Big Data<br/>Semestre: '+escape(str(meta.get('semestre','2026.2')))+'<br/>Professor: '+escape(meta['professor']),'CoverA3'),Spacer(1,20),p(team_text,'CoverA3'),Spacer(1,18),p('Área temática: Indicadores Socioeconômicos','CoverA3'),p('Repositório do projeto:<br/><link href="https://github.com/herbarth/a3-saneamento-inteligente">https://github.com/herbarth/a3-saneamento-inteligente</link>','CoverA3'),PageBreak(),p('SUMÁRIO','EyebrowA3')]
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOCPrimary24',fontName=bold,fontSize=12,leading=18,spaceBefore=5),ParagraphStyle('TOCSecondary24',fontName=font,fontSize=12,leading=18,leftIndent=18,spaceBefore=0)];toc.dotsMinLevel=0
    story += [toc,PageBreak(),h1(1,'Apresentação do projeto'),h2('1.1','Contextualização'),p('A gestão municipal de resíduos reúne decisões sobre despesas operacionais, coleta, recuperação de materiais e condições de trabalho. Comparar informações oficiais pode apoiar o planejamento e a prestação de contas, desde que se considerem o porte dos municípios, a cobertura dos serviços e a qualidade dos registros. O projeto se dirige a gestores municipais, prestadores, cooperativas e demais interessados na recuperação de materiais e no trabalho na cadeia de resíduos.'),h2('1.2','Problema de pesquisa'),old_p(1,'Como os municípios brasileiros'),h2('1.3','Objetivos'),old_p(1,'Analisar diferenças e associações'),p('Os objetivos específicos são integrar e validar três fontes oficiais em uma base municipal comum; descrever a distribuição de despesas, cobertura, recuperação e emprego formal; investigar diferenças entre grupos e associações entre indicadores; e formular recomendações gerenciais acompanhadas de indicadores, com divulgação em relatório e dashboard.'),h2('1.4','Escopo da análise'),old_table('Delimitação metodológica'),old_p(1,'Dados observacionais de um único ano')]
    story += [p('O estudo adota corte transversal de 2024 para integrar, no mesmo período, as informações municipais do SINISA 2025, a população do IBGE e o estoque formal da RAIS em 31 de dezembro. A primeira coleta do SINISA ocorreu em 2024, com referência 2023; a edição 2025 utilizada neste trabalho corresponde a 2024. A documentação oficial distingue metodologias demográficas entre esses ciclos [1, 7, 8]. Uma comparação histórica exigiria verificar a equivalência das variáveis, a cobertura de respostas e os denominadores, além de harmonizar as bases. Essa etapa longitudinal não foi executada. Os resultados descrevem diferenças e associações em 2024, sem estimar tendências temporais.')]

    story += [PageBreak(),h1(2,'Fontes de dados'),h2('2.1','Identificação das fontes')]
    story += [new_table(['Fonte','Instituição responsável','URL oficial','Dados obtidos'],[
      ['SINISA 2025','Ministério das Cidades','<link href="https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025">Resultados SINISA 2025</link> [1]','Despesas, massas coletadas e recuperadas, cobertura e trabalhadores informados.'],
      ['IBGE 2024','Instituto Brasileiro de Geografia e Estatística','<link href="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/">Estimativas municipais 2024</link> [2]','População residente, nomes e códigos municipais.'],
      ['RAIS 2024','Ministério do Trabalho e Emprego','<link href="https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/microdados-rais-e-caged">Microdados RAIS</link> [3-5]','Estoque formal de todos os setores e atividades de resíduos por município e CNAE.']], [65,112,120,156],'Identificação das fontes')]
    story += [p('Os endereços completos e as versões dos arquivos constam das referências e do inventário de fontes que acompanha o projeto.','SmallA3'),h2('2.2','Caracterização das fontes'),old_p(2,'A edição SINISA 2025'),old_p(2,'As versões IBGE DOU'),p('A RAIS disponibiliza tabelas complementares e microdados de estabelecimentos com vínculos, município e atividade econômica.'),p('São fontes públicas de instituições oficiais, com ciclos anuais de referência e eventuais revisões ou republicações. O SINISA disponibiliza planilhas Excel em arquivo ZIP; o IBGE, estimativas em planilha ODS; a RAIS, tabelas complementares e arquivo público de estabelecimentos comprimido em 7z. Os formatos efetivamente inspecionados e as versões foram registrados, em vez de presumir que todas as divulgações mantêm o mesmo esquema.'),h2('2.3','Justificativa da seleção'),p('O SINISA descreve a operação do manejo de resíduos; o IBGE fornece um denominador demográfico comum e uma chave territorial; a RAIS acrescenta o contexto do emprego formal e o recorte das atividades de resíduos. As três fontes permitem tratar custo, recuperação e trabalho no mesmo ano e na unidade municipal. A CNAE funciona como aproximação setorial e não como certificação de emprego verde.')]

    story += [PageBreak(),h1(3,'Processo de ETL extração transformação e carga'),h2('3.1','Visão geral do processo'),old_p(3,'1. Obter e preservar arquivos oficiais')]
    story += asset_figure(figures['flow'],'Fluxo de extração transformação integração e carga','Fonte: elaboração própria. O fluxo representa os procedimentos executados; os arquivos originais e as decisões de tratamento permanecem registrados.',max_height=270)
    story += [old_p(3,'O SINISA e o IBGE usam código municipal'),h2('3.2','Extração dos dados'),new_table(['Fonte','Método de extração','Ferramenta utilizada','Arquivo original'],[
      ['SINISA','Obtenção do ZIP oficial, inspeção de abas, cabeçalhos, unidades e glossários.','Python, zipfile e leitura de Excel.','ZIP com nove planilhas XLSX.'],
      ['IBGE','Leitura das tabelas e notas por XML no contêiner ODS.','Python, zipfile e XML.','ODS da estimativa DOU de 29/08/2024.'],
      ['RAIS','Descompactação e leitura de registros em blocos; agregação por município e atividade.','Python, leitor CSV e descompactador 7z.','7z/COMT; CSV com vírgulas, aspas e Windows-1252.']], [62,170,105,116],'Métodos e ferramentas de extração'),old_p(2,'O arquivo RAIS_ESTAB_PUB.7z'),old_p(2,'A coluna rotulada Classe')]
    story += [h2('3.3','Transformação e limpeza dos dados'),new_table(['Operação','Procedimento executado','Justificativa'],[
      ['Duplicidades e chaves','Checar unicidade e validar junções um para um. Linhas SINISA sem código municipal válido foram retiradas do conjunto municipal.','Impedir multiplicação artificial de municípios e de valores; não se afirma remoção de duplicados onde a checagem não os encontrou.'],
      ['Ausências e zeros','Preservar não resposta e campos não declarados. Atribuir zeros RAIS setoriais somente após leitura e validação do universo completo.','Distinguir falta de informação de ausência de vínculo formal registrado.'],
      ['Padronização','Harmonizar tipos numéricos, códigos e unidades. Associar o código RAIS de seis dígitos ao prefixo IBGE único.','Usar unidade e território coerentes sem juntar por nomes.'],
      ['Inconsistências','Manter dados originais e sinalizar dois alertas de soma de massa; suspender taxas de quatro municípios com ressalva territorial.','Evitar correções presumidas e razões com numerador e denominador incompatíveis.'],
      ['Integração','Agregar a RAIS antes das junções municipais; compatibilizar IBGE DOU e população SINISA.','Manter uma linha por município e ano, sem ligar diretamente rotas ou unidades operacionais ao resumo.']], [94,190,169],'Limpeza transformação e justificativas'),old_table('Verificações de qualidade'),old_p(4,'No SINISA, branco ou null'),old_p(4,'A RAIS inclui Boa Esperança')]
    story += [h2('3.4','Enriquecimento dos dados'),new_table(['Nova variável','Método de criação','Origem','Objetivo analítico'],[
      ['DEX por residente','GFI2221 ÷ população IBGE; R$/hab.ano.','SINISA e IBGE.','Comparar a despesa operacional de manejo por residente; não investimento.'],
      ['DEX por tonelada','GFI2221 ÷ GTR1028; R$/t.','SINISA.','Relacionar toda a operação do manejo à massa coletada; não custo marginal de coleta.'],
      ['Recuperação total calculada','100 × GTR1029 ÷ GTR1028.','SINISA: massas anuais.','Examinar recuperação de secos e orgânicos em relação ao RSU coletado.'],
      ['Cobertura seletiva calculada','100 × GTR0205 ÷ população IBGE.','SINISA e IBGE DOU.','Medir população atendida ao menos semanalmente; não massa reciclada.'],
      ['Densidade setorial de vínculos','1.000 × estoque CNAE 38 ou 38.3 ÷ população.','RAIS e IBGE.','Comparar intensidade do trabalho formal setorial, com ressalvas territoriais.'],
      ['Participação setorial formal','100 × vínculos CNAE 38 ÷ vínculos de todos os setores.','RAIS.','Contextualizar o setor no estoque formal do município.']], [105,150,78,120],'Variáveis derivadas e objetivos'),p('O indicador oficial IFR2002 usa GFI2221 ÷ GTR0201, isto é, habitante coberto pela coleta. Ele permanece separado da razão analítica por residente. Todas as razões exigem denominadores positivos; o dicionário identifica indicadores oficiais e recalculados.','SmallA3'),h2('3.5','Carga e consolidação'),old_p(3,'A base integrada tem 5.570 municípios'),p('O processo em Python carrega os arquivos padronizados, executa junções municipais com validação de integridade e grava a base em CSV. Foram conferidos códigos únicos, correspondência das fontes, somas, tipos, denominadores e disponibilidade de cada coluna. O notebook mantém saídas executadas, e os hashes vinculam a base às análises e ao relatório.'),PageBreak(),h2('3.6','Caracterização da base final'),new_table(['Característica','Resultado'],[['Fontes utilizadas','3: SINISA, IBGE e RAIS.'],['Registros','5.570 municípios, com código IBGE único.'],['Colunas','56 variáveis.'],['Período','Corte transversal de 2024.'],['Formato final','CSV, com cópia de consulta em Excel e dicionário de dados.']], [150,303],'Características da base consolidada'),h2('3.7','Dicionário de dados'),p('O Apêndice A contém as 56 variáveis, com tipo, descrição, origem e unidade ou valores. O arquivo docs/dicionario_dataset_completo.csv acrescenta códigos oficiais, arquivos e disponibilidade.')]

    story += [PageBreak(),h1(4,'Análise exploratória de dados EDA'),h2('4.1','Objetivos da análise exploratória'),p('A exploração procura compreender dispersão, concentração, valores atípicos, ausência de resposta e diferenças entre grupos municipais antes de interpretar associações. As perguntas são quanto variam despesas e recuperação, como a distribuição muda entre portes e regiões e como o trabalho formal aparece no recorte setorial.'),old_p(1,'H1: as razões de despesa'),h2('4.2','Estatística descritiva')]
    stat_rows=[]
    for key,label in [('count','n'),('mean','Média'),('50%','Mediana'),('25%','Q1'),('75%','Q3'),('std','Desvio padrão'),('min','Mínimo'),('max','Máximo')]:
        stat_rows.append([label]+[br(descriptions.loc[c,key],0 if key=='count' else 2) for c in stats_cols])
    story += [new_table(['Estatística','DEX por residente<br/>(R$/hab.ano)','DEX por tonelada<br/>(R$/t)','Cobertura seletiva<br/>(%)','Recuperação total<br/>(%)'],stat_rows,[93,92,92,88,88],'Estatísticas descritivas da amostra principal',numeric=True),p('Estatísticas municipais não ponderadas da amostra principal (n=4.852), sem corte de extremos. Q1 e Q3 são os percentis 25 e 75, calculados por interpolação linear. O desvio padrão é amostral, com divisor n-1; nas colunas de percentuais, sua unidade é ponto percentual (pp), correspondendo a 35,93 pp de cobertura e 7,41 pp de recuperação. Ausências são excluídas por variável e zeros válidos são preservados. Cobertura e recuperação nesta tabela são recalculadas com população IBGE e massas SINISA. Não são taxas nacionais agregadas.','SmallA3'),p('A média de despesa por residente (R$ 232,35) supera a mediana (R$ 69,17), e o desvio padrão de R$ 3.230,53 evidencia forte dispersão da cauda. O intervalo entre Q1 (R$ 31,35) e Q3 (R$ 121,58) situa a metade central dos municípios. A recuperação tem mediana zero e Q3 de 1,39%, enquanto a cobertura seletiva tem mediana zero e Q3 de 33,85%. A leitura conjunta da média, dos quartis, do desvio padrão e dos extremos evita tratar a média isolada como um município típico.'),h2('4.3','Visualização e distribuição dos dados')]
    story += asset_figure(figures['hist'],'Histograma da despesa de manejo por residente','Fonte: SINISA e IBGE, amostra principal de 4.852 municípios. A transformação log10 é somente uma escala de visualização e não altera a base.',max_height=220)
    story += [p('Interpretação: a distribuição se concentra nos intervalos centrais e tem cauda superior longa. A escala logarítmica permite visualizar municípios com ordens de grandeza distintas; os valores administrativos mais altos continuam sujeitos à investigação na fonte.','SmallA3')]
    story += asset_figure(figures['box'],'Box plots de despesa por residente por região','Fonte: SINISA e IBGE, amostra principal de 4.852 municípios. Os pontos além dos bigodes estão ocultos apenas no desenho; não foram removidos dos cálculos.',max_height=220)
    story += [p('Interpretação: as regiões apresentam centros e dispersões diferentes. O box plot descreve os respondentes elegíveis e não produz um ranking de eficiência nem corrige diferenças de escopo do serviço.','SmallA3')]
    story += asset_figure(figures['scatter'],'Dispersão entre despesa por residente e recuperação total','Fonte: SINISA e IBGE, amostra principal de 4.852 municípios. Despesas no eixo horizontal em escala logarítmica; recuperação recalculada no eixo vertical.',max_height=220)
    story += [p('Interpretação: muitos municípios se alinham em recuperação zero em diferentes níveis de despesa. O desenho evidencia heterogeneidade e apoia a investigação diagnóstica; não demonstra que aumentar ou cortar gastos cause determinado resultado.','SmallA3'),h2('4.4','Identificação de padrões e tendências')]
    story += figure('02_custos_por_porte.png','Figura @. Despesa por residente por porte após corte P1-P99. O box plot mostra mediana e dispersão; pontos além dos bigodes ficam ocultos apenas nesta figura e permanecem nos CSVs. Fonte: SINISA e IBGE, elaboração do projeto.',max_height=235)
    story += [old_table('Despesas e recuperação por região'),old_p(6,'As medianas regionais'),old_p(6,'Para investigação gerencial'),p('A análise identifica agrupamentos definidos por porte populacional e região, além de concentração de zeros e extremos. Esses grupos são comparações descritivas, sem aplicação de algoritmo de clusterização. Como a base contém um único ano, não foram estimadas tendências temporais.'),old_p(9,'A leitura integral da RAIS'),old_table('Vínculos formais por atividade'),old_p(9,'Estoque ativo em 31/12/2024'),h2('4.5','Hipóteses investigadas'),new_table(['Hipótese','Evidências encontradas','Resultado e limite'],[
      ['H1 Despesas variam por porte e região.','Diferenças de medianas e distribuição nos grupos; tabelas completas por porte e região.','Evidência descritiva favorável no recorte. Composição dos serviços e fatores omitidos limitam explicações.'],
      ['H2 Maior cobertura acompanha maior recuperação.','Spearman 0,888 no conjunto e -0,056 na subamostra com recuperação positiva.','Associação de presença; inconclusiva para ganho de intensidade e causalidade.'],
      ['H3 Vínculos setoriais acompanham recuperação municipal.','Associação 0,228; controle de porte 0,198; nos ambos positivos, 0,216 e 0,055.','Associação limitada e sensível ao recorte; inconclusiva quanto a efeito e criação de vagas.']], [125,166,162],'Hipóteses evidências e resultados'),h2('4.6','Novos questionamentos'),old_p(11,'As novas questões são verificar')]

    story += [PageBreak(),h1(5,'Análises diagnósticas'),h2('5.1','Objetivo da análise diagnóstica'),p('A etapa diagnóstica aprofunda a influência dos extremos sobre a despesa média, a diferença entre presença e intensidade de recuperação e o contexto do emprego formal. Investiga fatores associados e explicações concorrentes, sem atribuir automaticamente as diferenças a desperdício, qualidade de gestão ou impacto de uma política.'),h2('5.2','Investigação das possíveis causas'),p('<b>Investigação 1 Confiabilidade e concentração das despesas.</b> A hipótese examinada é que poucos registros administrativos influenciam fortemente a média. A investigação compara amostras e confere os valores com os arquivos originais.'),old_p(5,'Na amostra principal, a média municipal'),old_table('Sensibilidade das despesas')]
    story += figure('01_custos_extremos_sensibilidade.png','Figura @. Sensibilidade das despesas aos extremos. Fonte: elaboração a partir de SINISA e IBGE; amostras e limites registrados nos CSVs do diagnóstico.',max_height=225)
    story += [old_p(5,'A conferência de 23 registros'),old_p(5,'Retirar o mesmo número'),p('<b>Investigação 2 Presença e intensidade da recuperação.</b> Foram comparados os municípios que declaram zero ou valor positivo e verificados os padrões divergentes entre cobertura e massa recuperada.'),old_p(7,'As duas correlações respondem'),old_p(7,'Com cobertura seletiva positiva'),p('<b>Investigação 3 Escopo e composição do emprego.</b> O estoque setorial formal foi confrontado com a recuperação de materiais e com o porte municipal. Informalidade, atividade principal do estabelecimento e prestação regional permanecem explicações a investigar, em vez de serem confundidas com efeito causal.'),h2('5.3','Correlações e relacionamentos'),old_p(7,'Dos {br(') if False else old_p(7,'municípios da amostra principal, <b>')]
    story += figure('03_cobertura_recuperacao.png','Figura @. Associação entre cobertura seletiva e recuperação declarada. A inclusão de zeros influencia a leitura. As faixas no painel direito apresentam médias medianas e n. Fonte: SINISA e IBGE, elaboração do projeto.',max_height=250)
    story += [old_p(7,'Neste diagnóstico, cobertura e recuperação'),old_p(9,'Em 3.782 municípios'),old_p(8,'Foram estimados modelos lineares')]
    story += figure('04_associacao_ajustada_sensibilidade.png','Figura @. Sensibilidade da associação ajustada de cobertura em diferentes amostras. Os intervalos refletem as premissas do modelo e não corrigem erro administrativo seleção de respondentes ou fatores omitidos.',max_height=240)
    story += [old_table('Associações ajustadas'),old_p(8,'Não foi usado custo por tonelada'),h2('5.4','Investigação de causalidade'),p('O projeto não executou um desenho de identificação causal. As correlações e regressões são análises observacionais transversais e descrevem associações, inclusive após controles. A ausência de dados de rotas, distâncias, contratos, preços de destinação, história institucional e qualidade dos registros impede isolar efeitos de uma intervenção. Não houve experimento, comparação longitudinal harmonizada ou demonstração de que maior cobertura cause economia, recuperação adicional ou contratação.'),h2('5.5','Síntese dos resultados diagnósticos'),old_p(11,'H1 apresentou diferenças')]
    story += [h1(6,'Análises preditivas opcional'),p('A equipe optou por não desenvolver análises preditivas. Esta etapa é opcional no edital. Os modelos lineares exploratórios apresentados na seção 5 apoiam o diagnóstico associativo e não foram utilizados para prever resultados futuros, definir metas operacionais ou estimar criação de empregos.')]

    story += [PageBreak(),h1(7,'Análises prescritivas e recomendações'),h2('7.1','Objetivo'),p('As recomendações procuram transformar os achados em decisões verificáveis: melhorar a confiabilidade da informação, selecionar comparáveis e testar intervenções com orçamento e acompanhamento. São propostas da equipe, ainda não implementadas. Benefícios, responsáveis e prioridades abaixo são sugestões para avaliação local, sem metas de economia ou emprego inventadas.'),h2('7.2','Recomendações propostas')]
    original_recs=old_table('Prescrições gerenciais')._content[1]._cellvalues
    problems=['Dados extremos ou inconsistentes dificultam a decisão.','Comparações entre municípios diferentes podem induzir conclusões frágeis.','Zeros e divergências de massa podem misturar situações operacionais e de registro.','O benefício líquido de expandir a recuperação é desconhecido.','O estoque formal não descreve toda a população trabalhadora.']
    rr=[]
    for i,row in enumerate(original_recs[1:]):
        rr.append([f'<b>P{i+1} Problema:</b> {problems[i]}<br/><b>Evidência:</b> '+row[0].text,row[1].text,row[2].text])
    story += [new_table(['Problema e evidência','Ação recomendada','Acompanhamento e limite'],rr,[140,175,138],'Recomendações vinculadas às evidências'),new_table(['Ação','Benefício esperado','Responsável sugerido','Indicador de acompanhamento'],[
      ['P1 Auditar registros','Diagnóstico mais confiável e confirmações documentadas.','Gestão do manejo, finanças e prestador municipal.','I1 Taxa de registros revisados com documentação (%).'],
      ['P2 Selecionar comparáveis','Referências com escopo de serviço mais semelhante.','Planejamento municipal e regulação.','I2 Comparáveis com porte região e escopo validados (%).'],
      ['P3 Conferir zeros e pesagem','Distinguir ausência de recuperação de falhas de informação.','Prestador e equipes de pesagem triagem e destino.','I3 Massa com origem pesagem e destino rastreáveis (%).'],
      ['P4 Orçar e avaliar piloto','Conhecer custo e resultado incremental antes da ampliação.','Gestão do manejo e finanças com prestador e cooperativas.','I4 Custo incremental líquido por tonelada adicional recuperada (R$/t).'],
      ['P5 Inclusão','Participação e condições de trabalho mais bem documentadas.','Gestão municipal de trabalho ou assistência com cooperativas e trabalhadores.','I5a Organizações consultadas (%); I5b Trabalhadores consultados (%).']], [68,120,126,139],'Benefícios responsáveis e indicadores propostos')]
    story += [p('Definição e periodicidade dos indicadores','SmallA3'),p('<b>I1:</b> 100 × registros com confirmação ou retificação documentada ÷ registros selecionados para revisão. Acompanhamento mensal. Revisão não equivale a erro confirmado.','SmallA3'),p('<b>I2:</b> 100 × comparáveis com porte, região e escopo de serviço conferidos ÷ comparáveis inicialmente selecionados. Atualizar em cada revisão contratual ou análise comparativa. Registrar quais critérios foram verificados.','SmallA3'),p('<b>I3:</b> 100 × toneladas registradas com origem, pesagem e destino identificados ÷ toneladas registradas no período. Acompanhamento mensal, separando secos, orgânicos e rejeitos. Rastreabilidade não equivale a recuperação efetiva.','SmallA3'),p('<b>I4:</b> (custos incrementais de implantação apropriados ao período + operação adicional - receitas efetivas dos materiais) ÷ toneladas adicionais efetivamente recuperadas. Apurar mensalmente no piloto, contra linha de base e escopo definidos antes de iniciar. Se não houver tonelagem adicional positiva, o indicador fica indisponível; registrar a regra de apropriação dos investimentos.','SmallA3'),p('<b>I5a:</b> 100 × organizações consultadas ÷ organizações mapeadas no cadastro local. <b>I5b:</b> 100 × trabalhadores consultados ÷ trabalhadores mapeados. As duas taxas têm universos separados e ficam indisponíveis se o respectivo denominador for zero. Acompanhamento trimestral participativo, junto a renda mediana, segurança e mudanças nas tarefas. Respeitar a privacidade dos participantes.','SmallA3'),h2('7.3','Priorização das recomendações'),p('A matriz é uma avaliação qualitativa proposta pela equipe. Impacto considera a contribuição potencial para a confiabilidade da decisão, a operação e a inclusão. Viabilidade considera uso de dados já disponíveis, necessidade de articulação e implantação. As classificações não são benefícios medidos nem substituem orçamento e diagnóstico local.'),new_table(['Recomendação','Impacto esperado','Viabilidade','Prioridade proposta'],[
      ['P1 Auditoria dos registros','Alto','Alta','Imediata; base para as demais decisões.'],
      ['P2 Comparáveis do serviço','Médio','Alta','Após validação dos dados de P1.'],
      ['P3 Zeros e rastreabilidade','Alto','Média','Alta; em paralelo a P2, após P1.'],
      ['P4 Piloto com orçamento','Alto potencial','Média','Condicionada a P1-P3, orçamento e participação.'],
      ['P5 Inclusão e condições de trabalho','Alto social','Média','Transversal desde o início, junto a P1-P4.']], [148,83,68,154],'Matriz qualitativa de impacto viabilidade e prioridade'),h2('7.4','Benefícios esperados'),p('A auditoria e a escolha de comparáveis podem reduzir decisões apoiadas em registros incompatíveis. A rastreabilidade e o piloto permitem avaliar resultados locais e custos adicionais antes de ampliar a intervenção. A participação dos trabalhadores pode qualificar o desenho das ações e tornar visíveis efeitos sobre renda, segurança e tarefas. Esses benefícios são esperados, dependem da implementação e precisam ser medidos.'),old_p(10,'Escolher cenário de referência')]

    dashboard_test=read_json(ROOT/'evidencias/testes_dashboard.json')
    story += [PageBreak(),h1(8,'Dashboard interativo'),h2('8.1','Apresentação'),p('O dashboard foi construído em Streamlit para permitir consulta municipal e comparação dos indicadores por região, estado, porte populacional e município. As cinco abas são Panorama, Despesas, Recuperação, Emprego formal e Qualidade e fontes. Há critérios de qualidade e exportação CSV do recorte; o panorama preserva também os não respondentes.'),h2('8.2','Principais insights'),p('O Panorama distingue os 4.854 respondentes ao SINISA dos 716 não respondentes. Despesas permite comparar distribuições e denominadores, em vez de transformar menor gasto em sinônimo de eficiência. Recuperação mostra zeros e relações observadas; Emprego formal apresenta os 265.143 vínculos municipais do recorte de resíduos e suas limitações. Qualidade e fontes explicita alertas, cobertura e decisões metodológicas.'),old_p(12,'O dashboard foi executado localmente'),h2('8.5','Link de acesso'),p(publication_line('Dashboard',publication.get('dashboard_url'),publication.get('dashboard_status')),'SmallA3'),p('Ferramenta utilizada: Streamlit. O link público e os downloads devem ser conferidos antes da apresentação e da entrega, pois o serviço pode hibernar por inatividade.','SmallA3'),PageBreak(),h1(9,'Storytelling vídeo de apresentação'),p('Link do vídeo no YouTube: pendente de gravação e publicação pelo grupo.<br/>Duração real: ainda não medida. Limite do edital: 7 minutos.<br/>Meta de montagem do roteiro: aproximadamente 6 minutos e 20 segundos; trata-se de planejamento, não de duração de um vídeo existente.','SmallA3'),p('A narrativa parte da decisão de uma prefeitura que pretende melhorar a reciclagem e precisa conhecer despesas, materiais recuperados e trabalho no setor. Apresenta a integração das três fontes, os achados sobre extremos e zeros, o retrato do emprego formal e uma demonstração breve do dashboard. Encerra com a proposta de conferir os registros e testar um piloto com orçamento, medição e participação dos trabalhadores. A fala é destinada a público não técnico; o detalhamento estatístico permanece no relatório. O roteiro completo é fornecido separadamente ao grupo.'),p('Após a gravação, será necessário conferir o tempo real e a inteligibilidade do áudio, publicar o vídeo no YouTube e inserir o endereço público no repositório. A conclusão desta seção não substitui essas etapas pendentes.','SmallA3')]

    story += [PageBreak(),h1(10,'Conclusões'),h2('10.1','Síntese dos resultados'),old_p(11,'A integração tornou verificáveis'),h2('10.2','Objetivos alcançados'),p('Foram atendidos os objetivos de integrar e validar três fontes públicas, descrever distribuições, examinar associações e elaborar recomendações com evidências e indicadores. O dashboard foi disponibilizado e o relatório consolida o processo. Não foram demonstradas economia realizada, eficiência causal ou criação futura de empregos, nem testada a eficácia das ações propostas. A série histórica harmonizada ficou fora do escopo executado. A equipe foi identificada com cinco integrantes. O vídeo final e a submissão ainda precisam ser concluídos para a entrega acadêmica.'),h2('10.3','Contribuições do projeto'),old_p(11,'Como contribuição aplicada'),h2('10.4','Limitações'),old_p(9,'A CNAE não certifica benefício'),p('As fontes combinam estimativas demográficas, informações autodeclaradas de serviços e estoques formais de estabelecimentos. Não resposta, extremos e diferenças territoriais afetam comparações; alertas não certificam todos os demais registros. O corte de um ano e a ausência de variáveis contratuais, geográficas e de qualidade impedem demonstrar mecanismos causais. Os resultados se referem às amostras e aos denominadores declarados em cada análise.'),h2('10.5','Trabalhos futuros'),p('Os próximos estudos podem harmonizar ciclos do SINISA e do antigo SNIS antes de analisar evolução temporal, incorporar distâncias, rotas, contratos, rejeitos e condições de trabalho e produzir cadastros locais participativos. Um piloto deve registrar linha de base, custos incrementais e resultados materiais e sociais, com prazo de avaliação definido antes da execução. Novas fontes ou mudanças territoriais exigem novamente conferir versões, chaves e denominadores.')]

    refs=[
      ('1','BRASIL. Ministério das Cidades. Resultados SINISA 2025: ano de referência 2024. Brasília, DF: Ministério das Cidades, 2025.','https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025','24 nov. 2026'),
      ('2','IBGE. Estimativas da população residente para os municípios: 2024. Rio de Janeiro: IBGE, 2024.','https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/','20 nov. 2026'),
      ('3','BRASIL. Ministério do Trabalho e Emprego. Microdados RAIS e CAGED. Brasília, DF: MTE, 2025.','https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/microdados-rais-e-caged','20 nov. 2026'),
      ('4','BRASIL. Ministério do Trabalho e Emprego. RAIS ano-base 2024: microdados públicos de estabelecimentos. Brasília, DF: MTE, 2026. Arquivo republicado em 18 maio 2026.','ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/2024/RAIS_ESTAB_PUB.7z','20 nov. 2026'),
      ('5','BRASIL. Ministério do Trabalho e Emprego. RAIS 2024: divulgação complementar: tabelas 2023 e 2024. Brasília, DF: MTE, 2025.','https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2024/rais-2024-1/rais-complementar-tabelas-2023x2024.xlsx','20 nov. 2026'),
      ('6','IBGE. Comissão Nacional de Classificação. Estrutura detalhada da CNAE e CNAE Fiscal 2.0. Rio de Janeiro: IBGE, [s.d.].','https://concla.ibge.gov.br/images/concla/documentacao/EstruturaDetalhadaCNAE_CNAEFiscal2_Atualizada.pdf','20 nov. 2026'),
      ('7','BRASIL. Ministério das Cidades. Resultados SINISA: primeira coleta SINISA 2024, ano de referência 2023. Brasília, DF: Ministério das Cidades, 2025.','https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa','24 nov. 2026'),
      ('8','BRASIL. Ministério das Cidades. Regulamentação SINISA: metodologias demográficas para os ciclos de coleta. Brasília, DF: Ministério das Cidades.','https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/sinisa-1/portaria-sinisa','24 nov. 2026')]
    story += [PageBreak(),p('REFERÊNCIAS','RefHeadingA3')]
    for label,description,url,access in refs:
        story += [p(f'[{label}] {escape(description)} Disponível em: <link href="{escape(url)}">{escape(url)}</link>. Acesso em: {access}.','RefA3')]

    story += [PageBreak(),Paragraph('APÊNDICE A DICIONÁRIO COMPLETO DA BASE CONSOLIDADA',styles['H1A3']),p('Este apêndice apresenta todas as 56 colunas da base integrada. Ausência significa informação não disponível conforme a origem; zero permanece um valor observado ou atribuído somente após a validação do universo RAIS. A origem, o código oficial, os arquivos e a disponibilidade detalhada estão também no CSV do dicionário. O campo notas_ibge é textual e está vazio nesta versão; a leitura CSV o inferiu como float64 pela ausência de valores, sem mudar seu significado nem preencher a base.','SmallA3')]
    dict_rows=[]
    for r in dictionary.itertuples():
        dtype={'str':'texto','int64':'inteiro','float64':'real','bool':'lógico'}.get(str(r.tipo_lido_csv),str(r.tipo_lido_csv))
        if r.coluna=='notas_ibge':dtype='texto'
        desc=escape(str(r.descricao))+f'<br/><i>Origem: {escape(str(r.fonte))}.</i>'
        unit = {'estabelecimentos':'estab.', 'Associações/cooperativas':'associações /<br/>cooperativas', 'associações/cooperativas':'associações /<br/>cooperativas'}.get(str(r.unidade),escape(str(r.unidade)))
        dict_rows.append([wrap_code(r.coluna),dtype,desc,unit])
    story += [new_table(['Variável','Tipo','Descrição e origem','Unidade ou valores'],dict_rows,[137,49,199,68],'Dicionário integral das 56 variáveis')]
    story += [PageBreak(),Paragraph('APÊNDICE B REPRODUÇÃO E EVIDÊNCIAS',styles['H1A3']),old_p(12,'scripts/etl.py e scripts/extrair_rais_setorial.py'),old_p(12,'Base desta versão:'),p(publication_line('GitHub',publication.get('github_url'),publication.get('github_status')),'SmallA3'),p('A submissão final deve incluir o endereço do repositório com relatório, link do dashboard e link do vídeo, conforme as orientações da disciplina. O prazo indicado é 03/12/2026. A identificação da equipe foi preenchida conforme as informações fornecidas pelo grupo.','SmallA3')]
    story,counts=_renumber(story)
    doc = AcademicDocTemplate(str(OUT),pagesize=A4,rightMargin=RIGHT,leftMargin=LEFT,topMargin=TOP,bottomMargin=BOTTOM,title='Saneamento Inteligente Relatório A3',author='Equipe do projeto A3 UNIFACS',subject='Relatório final conforme estrutura do professor')
    doc.multiBuild(story,onFirstPage=page_footer,onLaterPages=page_footer)
    manifest={'gerado_em_utc':datetime.now(timezone.utc).isoformat(),'arquivo':str(OUT),'sha256_pdf':hashlib.sha256(OUT.read_bytes()).hexdigest(),'sha256_dataset':dataset_hash,'dataset_linhas':len(data),'dataset_colunas':len(data.columns),'fontes':['SINISA','IBGE','RAIS'],'secoes_template':10,'figuras':counts['Figura'],'tabelas':counts['Tabela'],'quadros':counts['Quadro'],'dicionario_variaveis':len(dictionary),'predicao':'opcional não executada','video_url':None,'video_duracao_real':None,'video_meta_planejada':'6min20s','identificacao':f'{len(real_names)} integrantes informados; matrícula de Pedro a conferir conforme orientação do usuário','fontes_temporais':[refs[0][2],refs[6][2],refs[7][2]],'modelo_referencia':'Template_Relatório Final.docx fornecido pelo professor; estrutura de dez seções preservada.'}
    (OUT.parent/('manifesto_relatorio_revisado.json' if _STAGED else 'manifesto_relatorio.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))


if __name__=='__main__':
    generate()
