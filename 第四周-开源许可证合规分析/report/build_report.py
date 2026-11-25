#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 report/报告源文.md 生成为符合课程模板格式的 Word 报告。

格式要求（来自课程模板）：
- 正文：宋体五号（10.5pt），黑色，首行缩进 2 字符；
- 英文：Times New Roman；
- 行距：多倍行距 1.25；
- 图片居中且高度不超过页面 1/3（本报告未使用图片）；
- 封面包含姓名、学号、班级、指导教师、学期、时间、报告日期、成绩等字段。

运行：
    python3 report/build_report.py
"""

import os
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(BASE_DIR, "report", "报告源文.md")
OUTPUT = os.path.join(BASE_DIR, "f25011202-方帝斯-开源合规与许可证.docx")

BODY_CN = "宋体"
BODY_EN = "Times New Roman"
HEAD_CN = "黑体"
CODE_EN = "Consolas"


def set_run_font(run, cn=BODY_CN, en=BODY_EN, size=10.5, bold=False,
                 color=None, italic=False):
    run.font.name = en
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = RGBColor(*color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), en)
    rfonts.set(qn("w:hAnsi"), en)
    rfonts.set(qn("w:eastAsia"), cn)
    rfonts.set(qn("w:cs"), en)


def add_rich_text(paragraph, text, size=10.5, cn=BODY_CN, en=BODY_EN,
                  color=None, bold=False):
    """支持 **加粗**、`代码` 两种简单行内格式。"""
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    tokens = re.split(r"(\*\*.+?\*\*|`[^`]+`)", text)
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            run = paragraph.add_run(token[2:-2])
            set_run_font(run, cn=cn, en=en, size=size, bold=True, color=color)
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, cn=cn, en=CODE_EN, size=size - 0.5,
                         bold=bold, color=(70, 70, 70))
        else:
            run = paragraph.add_run(token)
            set_run_font(run, cn=cn, en=en, size=size, bold=bold, color=color)


def style_body(paragraph):
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Pt(21)
    fmt.line_spacing = 1.25
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def shade_paragraph(paragraph, fill="F2F2F2"):
    ppr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    ppr.append(shd)


def shade_cell(cell, fill="E7ECF5"):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def set_cell_margins(table, top=40, bottom=40, left=90, right=90):
    tblpr = table._tbl.tblPr
    margins = OxmlElement("w:tblCellMar")
    for key, value in (("top", top), ("left", left),
                       ("bottom", bottom), ("right", right)):
        node = OxmlElement(f"w:{key}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        margins.append(node)
    tblpr.append(margins)


def remove_table_borders(table):
    tblpr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:val"), "nil")
        borders.append(node)
    tblpr.append(borders)


def set_value_border(cell):
    tcpr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:color"), "808080")
    borders.append(bottom)
    tcpr.append(borders)


def add_field(paragraph, instruction, size=9):
    run = paragraph.add_run()
    set_run_font(run, size=size, color=(120, 120, 120))
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(text)
    run._r.append(fld_end)


def build_cover(doc):
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(3.0)
    section.different_first_page_header_footer = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("课程编号：____________________")
    set_run_font(run, size=10.5)

    for _ in range(2):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("《开源创新思维》")
    set_run_font(run, cn=HEAD_CN, size=26, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run("平时作业报告")
    set_run_font(run, cn=HEAD_CN, size=26, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(30)
    run = p.add_run("开源软件许可证合规分析——以 PM2 为例")
    set_run_font(run, size=15)

    info = [
        ("姓　　名", "方帝斯"),
        ("学　　号", "f25011202"),
        ("班　　级", "f250117"),
        ("指导教师", "祝欣蓉"),
        ("开设学期", "2026—2027 秋季学期"),
        ("开设时间", "第 1 周——第 16 周"),
        ("报告日期", "2026 年 11 月 25 日"),
        ("评定成绩", ""),
        ("评 定 人", "祝欣蓉"),
        ("评定日期", ""),
    ]

    table = doc.add_table(rows=len(info), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    remove_table_borders(table)
    set_cell_margins(table, top=40, bottom=40, left=120, right=120)

    for row, (label, value) in enumerate(info):
        cells = table.rows[row].cells
        cells[0].width = Cm(4.2)
        cells[1].width = Cm(7.8)
        p0 = cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r0 = p0.add_run(label + "：")
        set_run_font(r0, size=12)
        p1 = cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p1.add_run(value if value else "　")
        set_run_font(r1, size=12)
        set_value_border(cells[1])

    for _ in range(2):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("上海杉达学院")
    set_run_font(run, cn=HEAD_CN, size=18, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("二〇二六年十一月")
    set_run_font(run, size=12)


def build_header_footer(section):
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run("《开源创新思维》平时作业报告　|　f25011202 方帝斯")
    set_run_font(run, size=8.5, color=(120, 120, 120))

    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("第 ")
    set_run_font(run, size=9, color=(120, 120, 120))
    add_field(p, "PAGE")
    run = p.add_run(" 页　共 ")
    set_run_font(run, size=9, color=(120, 120, 120))
    add_field(p, "NUMPAGES")
    run = p.add_run(" 页")
    set_run_font(run, size=9, color=(120, 120, 120))


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    fmt.keep_with_next = True
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fmt.page_break_before = True
        fmt.space_before = Pt(6)
        fmt.space_after = Pt(12)
        size = 16
    elif level == 2:
        fmt.space_before = Pt(10)
        fmt.space_after = Pt(6)
        size = 14
    else:
        fmt.space_before = Pt(6)
        fmt.space_after = Pt(4)
        size = 12
    run = p.add_run(text)
    set_run_font(run, cn=HEAD_CN, size=size, bold=True)


def add_code_block(doc, lines):
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    fmt.first_line_indent = Pt(0)
    fmt.line_spacing = 1.0
    fmt.space_before = Pt(4)
    fmt.space_after = Pt(4)
    fmt.left_indent = Cm(0.4)
    shade_paragraph(p)
    for index, line in enumerate(lines):
        if index:
            p.add_run().add_break()
        run = p.add_run(line)
        set_run_font(run, cn=BODY_CN, en=CODE_EN, size=9, color=(50, 50, 50))


def set_row_cant_split(row):
    trpr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    trpr.append(cant_split)


def add_table(doc, rows):
    cols = len(rows[0])
    table = doc.add_table(rows=len(rows), cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    set_cell_margins(table)

    widths = None
    if cols == 4 and rows[0][0].startswith("许可证"):
        widths = [4.2, 1.7, 1.7, 7.4]
    elif cols == 4 and rows[0][0] == "包名":
        widths = [4.0, 3.6, 4.2, 3.2]
    if widths:
        table.autofit = False
        for index, width in enumerate(widths):
            table.columns[index].width = Cm(width)

    for r_index, row in enumerate(rows):
        set_row_cant_split(table.rows[r_index])
        for c_index, value in enumerate(row):
            cell = table.rows[r_index].cells[c_index]
            if widths:
                cell.width = Cm(widths[c_index])
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            fmt = p.paragraph_format
            fmt.first_line_indent = Pt(0)
            fmt.line_spacing = 1.0
            fmt.space_before = Pt(1)
            fmt.space_after = Pt(1)
            # 除最后一行外，保持与下一行同页，避免表格被拆散
            if r_index < len(rows) - 1:
                fmt.keep_with_next = True
            text = value.replace("**", "").replace("`", "")
            run = p.add_run(text)
            set_run_font(run, size=9, bold=(r_index == 0))
            if r_index == 0:
                shade_cell(cell)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)


def parse_table(lines, start):
    rows = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        line = lines[index].strip()
        if re.match(r"^\|[\s|:-]+\|$", line):
            index += 1
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
        index += 1
    return rows, index


def build_body(doc):
    with open(SOURCE, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if stripped.startswith("```"):
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            index += 1
            add_code_block(doc, code_lines)
            continue

        if stripped.startswith("# "):
            add_heading(doc, stripped[2:].strip(), 1)
            index += 1
            continue

        if stripped.startswith("## "):
            add_heading(doc, stripped[3:].strip(), 2)
            index += 1
            continue

        if stripped.startswith("### "):
            add_heading(doc, stripped[4:].strip(), 3)
            index += 1
            continue

        if stripped.startswith("|"):
            rows, index = parse_table(lines, index)
            if rows:
                add_table(doc, rows)
            continue

        if re.match(r"^表\s*\d", stripped):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            fmt = p.paragraph_format
            fmt.first_line_indent = Pt(0)
            fmt.space_before = Pt(6)
            fmt.space_after = Pt(2)
            fmt.keep_with_next = True
            run = p.add_run(stripped)
            set_run_font(run, cn=HEAD_CN, size=9.5, bold=True)
            index += 1
            continue

        if re.match(r"^\[\d+\]", stripped):
            p = doc.add_paragraph()
            fmt = p.paragraph_format
            fmt.first_line_indent = Pt(0)
            fmt.line_spacing = 1.1
            fmt.space_before = Pt(0)
            fmt.space_after = Pt(0)
            run = p.add_run(stripped)
            set_run_font(run, size=9.5)
            index += 1
            continue

        p = doc.add_paragraph()
        style_body(p)
        add_rich_text(p, stripped)
        index += 1


def main():
    if not os.path.exists(SOURCE):
        sys.exit(f"找不到源文件：{SOURCE}")

    doc = Document()
    doc.core_properties.title = "开源软件许可证合规分析——以 PM2 为例"
    doc.core_properties.author = "方帝斯"
    doc.core_properties.subject = "《开源创新思维》平时作业报告"
    doc.core_properties.comments = "学号 f25011202，班级 f250117"

    normal = doc.styles["Normal"]
    normal.font.name = BODY_EN
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_CN)

    build_cover(doc)
    build_header_footer(doc.sections[0])

    # 正文使用同一节，但封面页不显示页眉页脚（different first page）
    build_body(doc)

    doc.save(OUTPUT)
    print(f"已生成：{OUTPUT}")


if __name__ == "__main__":
    main()
