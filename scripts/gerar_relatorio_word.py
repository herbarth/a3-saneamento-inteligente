"""Conversão fiel dos flowables do relatório final para Word editável.

Somente lê o gerador e as evidências existentes. Não executa a geração PDF.
"""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import re
from collections import Counter
from html.parser import HTMLParser
from zipfile import ZipFile
from lxml import etree

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from reportlab.platypus import Paragraph, Spacer, Table, Image, PageBreak, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents

import os
ROOT = Path(os.environ.get('A3_PROJECT_ROOT', str(Path(__file__).resolve().parents[1])))
SOURCE = ROOT / 'scripts/gerar_relatorio.py'
PDF = ROOT / 'relatorios/Relatorio_A3_Saneamento_Inteligente.pdf'
OUT = Path(os.environ.get('A3_WORD_OUTPUT_PATH', str(PDF.with_suffix('.docx'))))
QA = OUT.parent / 'qa_word_gerado'
QA.mkdir(parents=True, exist_ok=True)
original_pdf_sha = hashlib.sha256(PDF.read_bytes()).hexdigest()

spec = importlib.util.spec_from_file_location('original_report', SOURCE)
source_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source_module)
tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
generate = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate')
body = []
for stmt in generate.body:
    if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'doc' for t in stmt.targets):
        break
    body.append(stmt)
generate.name = 'capture_story'
generate.body = body + [ast.Return(value=ast.Name(id='story', ctx=ast.Load()))]
capture_tree = ast.Module(body=[generate], type_ignores=[])
ast.fix_missing_locations(capture_tree)
exec(compile(capture_tree, str(SOURCE), 'exec'), source_module.__dict__)
story = source_module.capture_story()

doc = Document()
doc.core_properties.title = 'Saneamento Inteligente'
doc.core_properties.subject = 'Relatório A3 de Análise de Dados e Big Data'
doc.core_properties.author = 'Equipe do projeto A3 UNIFACS'
doc.core_properties.keywords = 'SINISA IBGE RAIS 2024 saneamento reciclagem emprego formal'
doc.core_properties.comments = ''


def style(name, size=12, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
          leading=1.5, before=0, after=6, indent=0, keep=False):
    if name not in doc.styles:
        from docx.enum.style import WD_STYLE_TYPE
        obj = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    else:
        obj = doc.styles[name]
    obj.font.name = 'Arial'
    obj.font.size = Pt(size)
    obj.font.bold = bold
    obj.font.color.rgb = RGBColor(0, 0, 0)
    rf = obj.element.get_or_add_rPr().get_or_add_rFonts()
    for key in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
        rf.attrib.pop(qn('w:' + key), None)
    for key in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        rf.set(qn('w:' + key), 'Arial')
    for border in obj.element.xpath('./w:pPr/w:pBdr'):
        border.getparent().remove(border)
    pf = obj.paragraph_format
    pf.alignment = align
    pf.line_spacing = leading
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.first_line_indent = Pt(indent)
    pf.keep_with_next = keep
    pf.widow_control = True
    return obj


style('Normal', indent=35.4, after=3)
style('Title', bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=18, keep=False)
style('Heading 1', bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, leading=Pt(18), after=12, keep=True)
style('Heading 2', bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, leading=Pt(18), before=6, after=6, keep=True)
style('A3 Capa', align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
style('A3 Pretextual', bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=18)
style('A3 Nota', size=10, align=WD_ALIGN_PARAGRAPH.LEFT, leading=1, after=6)
style('A3 Celula', size=10, align=WD_ALIGN_PARAGRAPH.LEFT, leading=1, after=0)
style('A3 Cabecalho Tabela', size=10, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, leading=1, after=0)
style('A3 URL', size=10, align=WD_ALIGN_PARAGRAPH.LEFT, leading=1, after=12)
style('A3 Referencia', align=WD_ALIGN_PARAGRAPH.LEFT, leading=1, after=12)
style('A3 Referencias Titulo', bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, leading=Pt(18), after=12, keep=True)
# Referências integram o sumário como nível principal.
outline = OxmlElement('w:outlineLvl')
outline.set(qn('w:val'), '0')
doc.styles['A3 Referencias Titulo'].element.get_or_add_pPr().append(outline)
style('TOC 1', bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, after=5)
style('TOC 2', align=WD_ALIGN_PARAGRAPH.LEFT, after=0)
doc.styles['TOC 2'].paragraph_format.left_indent = Pt(18)
for name in ['Header', 'Footer']:
    style(name, size=10, align=WD_ALIGN_PARAGRAPH.RIGHT, leading=1, after=0)

MAP = {
    'BodyA3': 'Normal', 'TitleA3': 'Title', 'CoverA3': 'A3 Capa',
    'EyebrowA3': 'A3 Pretextual', 'SmallA3': 'A3 Nota',
    'H1A3': 'Heading 1', 'H2A3': 'Heading 2',
    'CellA3': 'A3 Celula', 'HeaderCellA3': 'A3 Cabecalho Tabela',
    'URLA3': 'A3 URL', 'RefA3': 'A3 Referencia',
    'RefHeadingA3': 'A3 Referencias Titulo', 'NatureA3': 'Normal',
}


def configure_section(section):
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.left_margin = section.top_margin = Cm(3)
    section.right_margin = section.bottom_margin = Cm(2)
    section.header_distance = Cm(1.8)
    section.footer_distance = Cm(1.8)
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False


configure_section(doc.sections[0])
footer = doc.sections[0].footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.add_run('2026').font.size = Pt(12)
settings = doc.settings.element
update = OxmlElement('w:updateFields')
update.set(qn('w:val'), 'true')
settings.append(update)


def field(paragraph, instruction, cached=''):
    begin = OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = instruction
    sep = OxmlElement('w:fldChar'); sep.set(qn('w:fldCharType'), 'separate')
    end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end')
    paragraph.add_run()._r.append(begin)
    paragraph.add_run()._r.append(instr)
    paragraph.add_run()._r.append(sep)
    if cached:
        paragraph.add_run(cached)
    paragraph.add_run()._r.append(end)


expected = []
source_links = []


class Markup(HTMLParser):
    def __init__(self, paragraph=None):
        super().__init__(convert_charrefs=True)
        self.p = paragraph
        self.state = []
        self.plain = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'br':
            self.plain.append('\n')
            if self.p is not None:
                self.p.add_run().add_break()
        else:
            self.state.append((tag, attrs))
            if tag == 'link':
                source_links.append(attrs['href'])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag != 'br':
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.state)-1, -1, -1):
            if self.state[i][0] == tag:
                self.state.pop(i)
                break

    def handle_data(self, data):
        self.plain.append(data)
        if self.p is None:
            return
        tags = {t for t, a in self.state}
        link = next((a.get('href') for t, a in reversed(self.state) if t == 'link'), None)
        run = self.p.add_run(data)
        if 'b' in tags or 'strong' in tags:
            run.bold = True
        if 'i' in tags or 'em' in tags:
            run.italic = True
        if 'sup' in tags:
            run.font.superscript = True
        if 'sub' in tags:
            run.font.subscript = True
        if link:
            h = OxmlElement('w:hyperlink')
            h.set(qn('r:id'), self.p.part.relate_to(link, RT.HYPERLINK, is_external=True))
            h.append(run._r)
            self.p._p.append(h)


def fill_paragraph(par, obj):
    par.style = MAP[obj.style.name]
    parser = Markup(par)
    parser.feed(obj.text)
    expected.append(''.join(parser.plain))
    if obj.style.name == 'NatureA3':
        par.paragraph_format.left_indent = Pt(source_module.WIDTH / 2)
    return par


def add_paragraph(obj):
    global pending_page_break
    par = fill_paragraph(doc.add_paragraph(), obj)
    if pending_page_break:
        par.paragraph_format.page_break_before = True
        pending_page_break = False
    return par


def normalize_cell_numeric(value):
    return bool(re.fullmatch(r'[0-9.,%+−–\- ]+', value.strip()))


def add_table(obj):
    rows = obj._cellvalues
    widths = obj._argW
    if not widths or any(w is None for w in widths):
        widths = [source_module.WIDTH / len(rows[0])] * len(rows[0])
    tab = doc.add_table(rows=len(rows), cols=len(rows[0]))
    tab.alignment = WD_TABLE_ALIGNMENT.LEFT
    tab.autofit = False
    for col, width in zip(tab.columns, widths):
        col.width = Pt(width)
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        element = OxmlElement('w:' + edge)
        for key, value in {'val':'single','sz':'4','color':'D9D9D9'}.items():
            element.set(qn('w:' + key), value)
        borders.append(element)
    tab._tbl.tblPr.append(borders)
    for i, row in enumerate(tab.rows):
        cant = OxmlElement('w:cantSplit')
        row._tr.get_or_add_trPr().append(cant)
        if i == 0:
            repeat = OxmlElement('w:tblHeader')
            row._tr.get_or_add_trPr().append(repeat)
        for j, cell in enumerate(row.cells):
            cell.width = Pt(widths[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp = cell._tc.get_or_add_tcPr()
            margins = OxmlElement('w:tcMar')
            for side, twips in [('top',60),('bottom',60),('left',100),('right',100)]:
                el = OxmlElement('w:' + side); el.set(qn('w:w'), str(twips)); el.set(qn('w:type'), 'dxa'); margins.append(el)
            cp.append(margins)
            if i == 0:
                shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), 'F2F2F2'); cp.append(shd)
            source_p = rows[i][j]
            if isinstance(source_p, Paragraph):
                p = fill_paragraph(cell.paragraphs[0], source_p)
            else:
                raise TypeError(type(source_p))
            if i == 0:
                p.paragraph_format.keep_with_next = True
            elif j > 0 and len(rows[0]) > 3 and normalize_cell_numeric(p.text):
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    return tab


break_count = 0
pending_page_break = False
paragraph_count = table_count = image_count = 0


def convert(obj):
    global break_count, pending_page_break, paragraph_count, table_count, image_count
    if isinstance(obj, KeepTogether):
        for index, child in enumerate(obj._content):
            if index == 0 and isinstance(child, Paragraph):
                par = add_paragraph(child)
                par.paragraph_format.keep_with_next = True
                paragraph_count += 1
            else:
                convert(child)
    elif isinstance(obj, Paragraph):
        par = add_paragraph(obj)
        paragraph_count += 1
        if obj.text.startswith('Figura '):
            par.paragraph_format.keep_with_next = True
    elif isinstance(obj, Table):
        add_table(obj); table_count += 1
    elif isinstance(obj, Image):
        par = doc.add_paragraph()
        par.paragraph_format.first_line_indent = Pt(0)
        par.paragraph_format.space_after = Pt(0)
        par.paragraph_format.line_spacing = 1
        par.paragraph_format.keep_with_next = True
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pic = par.add_run().add_picture(obj.filename, width=Pt(obj.drawWidth), height=Pt(obj.drawHeight))
        pic._inline.docPr.set('descr', Path(obj.filename).stem.replace('_', ' '))
        image_count += 1
    elif isinstance(obj, Spacer):
        par = doc.add_paragraph()
        pf = par.paragraph_format
        pf.first_line_indent = Pt(0)
        pf.space_before = Pt(0)
        pf.space_after = Pt(max(obj.height - 1, 0))
        pf.line_spacing = Pt(1)
        par.add_run().font.size = Pt(1)
        if obj.height <= 5:
            pf.keep_with_next = True
    elif isinstance(obj, PageBreak):
        break_count += 1
        if break_count in (1, 2):
            sec = doc.add_section(WD_SECTION_START.NEW_PAGE)
            configure_section(sec)
            if break_count == 1:
                start = OxmlElement('w:pgNumType'); start.set(qn('w:start'), '1'); sec._sectPr.append(start)
            else:
                for start in sec._sectPr.findall(qn('w:pgNumType')):
                    sec._sectPr.remove(start)
                field(sec.header.paragraphs[0], ' PAGE ')
        else:
            pending_page_break = True
    elif isinstance(obj, TableOfContents):
        par = doc.add_paragraph()
        par.paragraph_format.first_line_indent = Pt(0)
        field(par, ' TOC \\o "1-2" \\h \\z \\u ')
    else:
        raise TypeError(f'Flowable não convertido: {type(obj)}')


for item in story:
    convert(item)
tables=[t for t in doc.tables if len(t.rows)==57 and t.cell(0,0).text=='Variável']
assert len(tables)==1
for row in tables[0].rows:
    for cell in row.cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:run.font.size=Pt(9.5)
        props=cell._tc.get_or_add_tcPr()
        for old in list(props.findall(qn('w:tcMar'))):props.remove(old)
        margins=OxmlElement('w:tcMar')
        for edge in ['top','bottom','left','right']:
            e=OxmlElement('w:'+edge);e.set(qn('w:w'),'45' if edge in ('top','bottom') else '75');e.set(qn('w:type'),'dxa');margins.append(e)
        props.append(margins)

doc.save(OUT)
(QA / 'paragrafos_fonte.json').write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding='utf-8')

# Validação nativa do conteúdo antes da atualização do sumário pelo Word.
def normalize(s):
    return re.sub(r'\s+', ' ', s).strip()

with ZipFile(OUT) as z:
    xml = etree.fromstring(z.read('word/document.xml'))
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    actual = [normalize(''.join(el.text or '' if el.tag == qn('w:t') else ' ' for el in p.iter() if el.tag in {qn('w:t'), qn('w:br'), qn('w:tab')})) for p in xml.xpath('//w:p', namespaces=ns)]
    expected_counts = Counter(normalize(s) for s in expected)
    actual_counts = Counter(actual)
    missing = expected_counts - actual_counts
    assert not missing, list(missing.items())
    links = [r.target_ref for r in doc.part.rels.values() if r.reltype == RT.HYPERLINK]
    assert set(source_links) == set(links)
    assert len(xml.xpath('//w:tbl', namespaces=ns)) == table_count
    assert len(xml.xpath('//*[local-name()="inline"]')) == image_count
assert hashlib.sha256(PDF.read_bytes()).hexdigest() == original_pdf_sha
qa = {
    'status': 'aguardando render e inspeção visual',
    'fonte_estruturada': str(SOURCE),
    'pdf_original_sha256': original_pdf_sha,
    'pdf_original_inalterado': True,
    'docx': str(OUT),
    'docx_sha256_antes_atualizar_campos': hashlib.sha256(OUT.read_bytes()).hexdigest(),
    'paragrafos_fonte_incluindo_celulas': len(expected),
    'paragrafos_corpo': paragraph_count,
    'tabelas_nativas': table_count,
    'figuras': image_count,
    'links_externos': sorted(set(source_links)),
    'conteudo_fonte_preservado_paragrafos_e_tabelas': not bool(missing),
    'pagina': 'A4 retrato; margens esquerda e superior 3cm; direita e inferior 2cm',
    'corpo': 'Arial 12pt, preto, 1,5, recuo primeira linha 1,25cm',
    'tabelas': 'Texto nativo Arial 10pt (9,5pt no dicionário), cabeçalho repetido, linhas sem divisão interna, bordas cinza',
    'sumario': 'Campo TOC funcional níveis 1-2; aguarda atualização Word nativo',
    'render_paginas_inspecionadas': [],
    'renderer': {'executado_por_este_script': False, 'orientacao': 'Atualizar os campos e o sumário no Word, renderizar e inspecionar todas as páginas antes de distribuir uma nova edição.'},
    'ajustes_apos_primeiro_render': ['Remoção de bordas decorativas herdadas do estilo Title', 'Remoção de referências de fonte de tema para garantir Arial', 'Paginação contínua após o sumário e sem contar capa', 'Quebras anteriores nos títulos para evitar página vazia por parágrafo de quebra isolado', 'Espaçamento entre parágrafos e headings moderado; corpo continua 12pt/1,5; tabelas continuam 10pt legíveis'],
}
(QA / 'validacao.json').write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(qa, ensure_ascii=False, indent=2))
