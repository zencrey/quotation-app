import os
import re
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

BASE_DIR = Path(__file__).resolve().parent
WORD_DIR = BASE_DIR / "generated" / "word"
WORD_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    """Removes or replaces invalid characters for filenames."""
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def add_horizontal_line(doc, space_before=4, space_after=8):
    """Inserts a clean solid black horizontal rule across the page."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        r'<w:bottom w:val="single" w:sz="12" w:space="1" w:color="000000"/>'
        r'</w:pBdr>'
    )
    p._p.get_or_add_pPr().append(pBdr)
    return p

def set_cell_margins(cell, top=50, bottom=50, left=100, right=100):
    """Sets internal padding for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        r'</w:tcMar>'
    )
    tcPr.append(tcMar)

def generate_quotation_word(quotation, items, output_path: str = None) -> str:
    """
    Generates an editable Word (.docx) document matching the sample quotation PDF.
    """
    if not output_path:
        safe_q_no = sanitize_filename(quotation.quotation_no)
        output_path = str(WORD_DIR / f"Quotation_{safe_q_no}.docx")

    doc = docx.Document()

    # Page Margins: 0.7 inch (approx 50pt)
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.65)
        s.bottom_margin = Inches(0.65)
        s.left_margin = Inches(0.7)
        s.right_margin = Inches(0.7)

    # 1. Company Name (Centered, Bold, Underlined, ~18pt)
    p_comp = doc.add_paragraph()
    p_comp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_comp.paragraph_format.space_before = Pt(0)
    p_comp.paragraph_format.space_after = Pt(20)
    run_comp = p_comp.add_run(quotation.company_name or "WARDHAN TRADING EST.")
    run_comp.font.name = "Arial"
    run_comp.font.size = Pt(17)
    run_comp.font.bold = True
    run_comp.font.underline = True

    # 2. QUOTATION Title (Centered, Bold, ~14pt)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("QUOTATION")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(14)
    run_title.font.bold = True

    # 3. Horizontal Line
    add_horizontal_line(doc, space_before=2, space_after=6)

    # 4. Meta Row: Date & Quotation No (2-column layout via table)
    meta_table = doc.add_table(rows=1, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    
    # Left cell: Date
    cell_date = meta_table.cell(0, 0)
    cell_date.width = Inches(3.5)
    p_d = cell_date.paragraphs[0]
    p_d.paragraph_format.space_before = Pt(0)
    p_d.paragraph_format.space_after = Pt(0)
    run_d = p_d.add_run(f"Date  :  {quotation.date}")
    run_d.font.name = "Arial"
    run_d.font.size = Pt(11)

    # Right cell: Quotation No
    cell_qno = meta_table.cell(0, 1)
    cell_qno.width = Inches(3.5)
    p_q = cell_qno.paragraphs[0]
    p_q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_q.paragraph_format.space_before = Pt(0)
    p_q.paragraph_format.space_after = Pt(0)
    run_q = p_q.add_run(f"Quotation No:{quotation.quotation_no}")
    run_q.font.name = "Arial"
    run_q.font.size = Pt(11)

    # Spacer
    p_sp1 = doc.add_paragraph()
    p_sp1.paragraph_format.space_before = Pt(12)
    p_sp1.paragraph_format.space_after = Pt(0)

    # 5. Customer Name (Centered, Bold, ~13pt)
    p_cust = doc.add_paragraph()
    p_cust.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cust.paragraph_format.space_before = Pt(0)
    p_cust.paragraph_format.space_after = Pt(12)
    run_cust = p_cust.add_run(quotation.customer_name or "Radisson Blue Hotel, Kuwait")
    run_cust.font.name = "Arial"
    run_cust.font.size = Pt(13)
    run_cust.font.bold = True

    # 6. Items Table
    # 6 columns: Description, Quantity, Price KD, Price Fills, Total KD, Total Fills
    col_widths = [Inches(2.8), Inches(0.9), Inches(0.725), Inches(0.725), Inches(0.725), Inches(0.725)]
    total_table_width = sum(col_widths)

    item_count = len(items)
    data_rows_needed = max(8, item_count)
    # Total rows = 2 (header) + data_rows_needed + 1 (total row)
    total_rows = 2 + data_rows_needed + 1

    table = doc.add_table(rows=total_rows, cols=6)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Apply column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

    # Row 0 & 1 Headers
    # Merge Description (0,0) and (1,0)
    cell_desc = table.cell(0, 0)
    cell_desc.merge(table.cell(1, 0))
    p = cell_desc.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Description")
    r.font.name = "Arial"
    r.font.size = Pt(10)

    # Merge Quantity (0,1) and (1,1)
    cell_qty = table.cell(0, 1)
    cell_qty.merge(table.cell(1, 1))
    p = cell_qty.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Quantity")
    r.font.name = "Arial"
    r.font.size = Pt(10)

    # Unit Price Header (0,2) merged with (0,3)
    cell_unit_hdr = table.cell(0, 2)
    cell_unit_hdr.merge(table.cell(0, 3))
    p = cell_unit_hdr.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Price per\npiece")
    r.font.name = "Arial"
    r.font.size = Pt(10)

    # Total Price Header (0,4) merged with (0,5)
    cell_tot_hdr = table.cell(0, 4)
    cell_tot_hdr.merge(table.cell(0, 5))
    p = cell_tot_hdr.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Total price\nper piece")
    r.font.name = "Arial"
    r.font.size = Pt(10)

    # Row 1 subheaders
    subheaders = [
        (2, "K.D"),
        (3, "Fills"),
        (4, "K.D"),
        (5, "Fills")
    ]
    for c_idx, label in subheaders:
        c = table.cell(1, c_idx)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(label)
        r.font.name = "Arial"
        r.font.size = Pt(9.5)

    # Populate Items into rows starting at row index 2
    for i in range(data_rows_needed):
        r_idx = 2 + i
        if i < item_count:
            item = items[i]
            # Description
            c_desc = table.cell(r_idx, 0)
            p_desc = c_desc.paragraphs[0]
            p_desc.paragraph_format.space_before = Pt(2)
            p_desc.paragraph_format.space_after = Pt(2)
            r = p_desc.add_run(item.description)
            r.font.name = "Arial"
            r.font.size = Pt(9.5)

            # Quantity
            c_qty = table.cell(r_idx, 1)
            p_qty = c_qty.paragraphs[0]
            p_qty.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_qty.paragraph_format.space_before = Pt(2)
            p_qty.paragraph_format.space_after = Pt(2)
            if item.quantity not in ("", None):
                try:
                    q_val = float(item.quantity)
                    if q_val > 0:
                        qty_txt = str(int(q_val)) if q_val.is_integer() else str(q_val)
                        r = p_qty.add_run(qty_txt)
                        r.font.name = "Arial"
                        r.font.size = Pt(9.5)
                except (ValueError, TypeError):
                    r = p_qty.add_run(str(item.quantity))
                    r.font.name = "Arial"
                    r.font.size = Pt(9.5)

            # Unit KD
            c_ukd = table.cell(r_idx, 2)
            p_ukd = c_ukd.paragraphs[0]
            p_ukd.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_ukd.paragraph_format.space_before = Pt(2)
            p_ukd.paragraph_format.space_after = Pt(2)
            if item.unit_price_kd:
                r = p_ukd.add_run(str(item.unit_price_kd))
                r.font.name = "Arial"
                r.font.size = Pt(9.5)

            # Unit Fills
            c_uf = table.cell(r_idx, 3)
            p_uf = c_uf.paragraphs[0]
            p_uf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_uf.paragraph_format.space_before = Pt(2)
            p_uf.paragraph_format.space_after = Pt(2)
            if item.unit_price_fills:
                r = p_uf.add_run(str(item.unit_price_fills))
                r.font.name = "Arial"
                r.font.size = Pt(9.5)

            # Total KD
            c_tkd = table.cell(r_idx, 4)
            p_tkd = c_tkd.paragraphs[0]
            p_tkd.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_tkd.paragraph_format.space_before = Pt(2)
            p_tkd.paragraph_format.space_after = Pt(2)
            if item.total_kd:
                r = p_tkd.add_run(str(item.total_kd))
                r.font.name = "Arial"
                r.font.size = Pt(9.5)

            # Total Fills
            c_tf = table.cell(r_idx, 5)
            p_tf = c_tf.paragraphs[0]
            p_tf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_tf.paragraph_format.space_before = Pt(2)
            p_tf.paragraph_format.space_after = Pt(2)
            if item.total_fills:
                r = p_tf.add_run(str(item.total_fills))
                r.font.name = "Arial"
                r.font.size = Pt(9.5)
        else:
            # Blank row for template spacing
            for c_idx in range(6):
                c = table.cell(r_idx, c_idx)
                p = c.paragraphs[0]
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(4)

    # Total Row (Last Row): "total" is in Description cell; all columns have individual cells
    total_row_idx = total_rows - 1

    # Cell 0: Description column has "total" right-aligned
    c_tot_lbl = table.cell(total_row_idx, 0)
    p_tot = c_tot_lbl.paragraphs[0]
    p_tot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_tot.paragraph_format.space_before = Pt(3)
    p_tot.paragraph_format.space_after = Pt(3)
    p_tot.paragraph_format.right_indent = Pt(12)
    r_tot = p_tot.add_run("total")
    r_tot.font.name = "Arial"
    r_tot.font.size = Pt(10)

    # Cells 1, 2, 3 remain separate individual cells with borders
    for c_empty_idx in (1, 2, 3):
        c_emp = table.cell(total_row_idx, c_empty_idx)
        p_emp = c_emp.paragraphs[0]
        p_emp.paragraph_format.space_before = Pt(3)
        p_emp.paragraph_format.space_after = Pt(3)

    # Total KD
    c_tot_kd = table.cell(total_row_idx, 4)
    p_tot_kd = c_tot_kd.paragraphs[0]
    p_tot_kd.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tot_kd.paragraph_format.space_before = Pt(3)
    p_tot_kd.paragraph_format.space_after = Pt(3)
    if quotation.total_kd:
        r_tot_kd = p_tot_kd.add_run(str(quotation.total_kd))
        r_tot_kd.font.name = "Arial"
        r_tot_kd.font.size = Pt(10)

    # Total Fills
    c_tot_f = table.cell(total_row_idx, 5)
    p_tot_f = c_tot_f.paragraphs[0]
    p_tot_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tot_f.paragraph_format.space_before = Pt(3)
    p_tot_f.paragraph_format.space_after = Pt(3)
    if quotation.total_fills:
        r_tot_f = p_tot_f.add_run(str(quotation.total_fills))
        r_tot_f.font.name = "Arial"
        r_tot_f.font.size = Pt(10)

    # 7. Amount in Words (Centered, Bold)
    p_words = doc.add_paragraph()
    p_words.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_words.paragraph_format.space_before = Pt(10)
    p_words.paragraph_format.space_after = Pt(14)
    run_words = p_words.add_run(quotation.amount_in_words or "KD Twenty Five")
    run_words.font.name = "Arial"
    run_words.font.size = Pt(11)
    run_words.font.bold = True

    # 8. Incharge and Contact Details
    # Incharge
    p_inch = doc.add_paragraph()
    p_inch.paragraph_format.space_before = Pt(0)
    p_inch.paragraph_format.space_after = Pt(8)
    incharge_val = quotation.incharge or ""
    inch_text = f"Incharge: {incharge_val}".strip()
    if not incharge_val:
        inch_text = "Incharge:"
    r_inch = p_inch.add_run(inch_text)
    r_inch.font.name = "Arial"
    r_inch.font.size = Pt(10.5)

    # Email
    p_mail = doc.add_paragraph()
    p_mail.paragraph_format.space_before = Pt(0)
    p_mail.paragraph_format.space_after = Pt(8)
    r_mail_lbl = p_mail.add_run("Email: ")
    r_mail_lbl.font.name = "Arial"
    r_mail_lbl.font.size = Pt(10.5)
    r_mail_val = p_mail.add_run(quotation.email or "thilakantmt@gmail.com")
    r_mail_val.font.name = "Arial"
    r_mail_val.font.size = Pt(10.5)
    r_mail_val.font.color.rgb = RGBColor(26, 13, 171) # Blue link
    r_mail_val.font.underline = True

    # Phone
    p_ph = doc.add_paragraph()
    p_ph.paragraph_format.space_before = Pt(0)
    p_ph.paragraph_format.space_after = Pt(16)
    r_ph = p_ph.add_run(f"Ph no: {quotation.phone or '+965 99983543'}")
    r_ph.font.name = "Arial"
    r_ph.font.size = Pt(10.5)

    # 9. Bottom Horizontal Line
    add_horizontal_line(doc, space_before=4, space_after=0)

    doc.save(output_path)
    return output_path
