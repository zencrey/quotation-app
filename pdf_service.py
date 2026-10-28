import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "generated" / "pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    """Removes or replaces invalid characters for filenames."""
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def generate_quotation_pdf(quotation, items, output_path: str = None) -> str:
    """
    Generates a professional PDF quotation matching the sample reference document.
    """
    if not output_path:
        safe_q_no = sanitize_filename(quotation.quotation_no)
        output_path = str(PDF_DIR / f"Quotation_{safe_q_no}.pdf")

    # Document Geometry: A4 (595.27 x 841.89 pt)
    # Margins: 50pt left and right -> Printable width = 495.27pt
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=45,
        bottomMargin=40
    )

    story = []

    # Typography & Styles
    company_style = ParagraphStyle(
        'CompanyTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    quotation_title_style = ParagraphStyle(
        'QuotationTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    header_meta_left = ParagraphStyle(
        'MetaLeft',
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    header_meta_right = ParagraphStyle(
        'MetaRight',
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        alignment=TA_RIGHT,
        textColor=colors.black
    )

    customer_style = ParagraphStyle(
        'CustomerTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    tbl_header_center = ParagraphStyle(
        'TblHeaderCenter',
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    tbl_header_left = ParagraphStyle(
        'TblHeaderLeft',
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    cell_style_left = ParagraphStyle(
        'CellLeft',
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    cell_style_center = ParagraphStyle(
        'CellCenter',
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    total_label_style = ParagraphStyle(
        'TotalLabel',
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
        textColor=colors.black,
        rightIndent=14
    )

    amount_words_style = ParagraphStyle(
        'AmountWords',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    contact_style = ParagraphStyle(
        'ContactText',
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    # 1. Company Name (Centered, Bold, Underlined)
    company_text = quotation.company_name or "WARDHAN TRADING EST."
    story.append(Paragraph(f"<u><b>{company_text}</b></u>", company_style))
    story.append(Spacer(1, 26))

    # 2. Quotation Title (Centered, Bold)
    story.append(Paragraph("<b>QUOTATION</b>", quotation_title_style))
    story.append(Spacer(1, 6))

    # 3. Horizontal Line across printable area
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=0, spaceAfter=8))

    # 4. Date and Quotation Number
    date_text = f"Date  :  {quotation.date}"
    qno_text = f"Quotation No:{quotation.quotation_no}"
    meta_table = Table(
        [[Paragraph(date_text, header_meta_left), Paragraph(qno_text, header_meta_right)]],
        colWidths=[247.5, 247.5]
    )
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 18))

    # 5. Customer Name (Centered, Bold)
    customer_name = quotation.customer_name or "Radisson Blue Hotel, Kuwait"
    story.append(Paragraph(f"<b>{customer_name}</b>", customer_style))
    story.append(Spacer(1, 16))

    # 6. Quotation Items Table
    # Printable width: 495 pt - perfectly balanced & symmetric subcolumns
    col_widths = [215, 68, 53, 53, 53, 53]

    # Two Header Rows
    table_data = [
        [
            Paragraph("Description", tbl_header_left),
            Paragraph("Quantity", tbl_header_center),
            Paragraph("Price per<br/>piece", tbl_header_center),
            "",
            Paragraph("Total price<br/>per piece", tbl_header_center),
            ""
        ],
        [
            "",
            "",
            Paragraph("K.D", tbl_header_center),
            Paragraph("Fills", tbl_header_center),
            Paragraph("K.D", tbl_header_center),
            Paragraph("Fills", tbl_header_center)
        ]
    ]

    table_styles = [
        # Merges for double-tier header
        ('SPAN', (0, 0), (0, 1)), # Description spans rows 0 & 1
        ('SPAN', (1, 0), (1, 1)), # Quantity spans rows 0 & 1
        ('SPAN', (2, 0), (3, 0)), # Unit Price spans cols 2 & 3
        ('SPAN', (4, 0), (5, 0)), # Total Price spans cols 4 & 5
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]

    # Populate Items
    for item in items:
        # Format multiline description
        desc_escaped = item.description.replace("\r\n", "\n").replace("\n", "<br/>")
        
        qty_str = ""
        if item.quantity not in ("", None):
            try:
                q_f = float(item.quantity)
                if q_f > 0:
                    qty_str = str(int(q_f)) if q_f.is_integer() else str(q_f)
            except (ValueError, TypeError):
                qty_str = str(item.quantity)

        unit_kd_str = str(item.unit_price_kd) if item.unit_price_kd else ""
        unit_fills_str = str(item.unit_price_fills) if item.unit_price_fills else ""

        tot_kd_str = str(item.total_kd) if item.total_kd else ""
        tot_fills_str = str(item.total_fills) if item.total_fills else ""

        table_data.append([
            Paragraph(desc_escaped, cell_style_left),
            Paragraph(qty_str, cell_style_center),
            Paragraph(unit_kd_str, cell_style_center),
            Paragraph(unit_fills_str, cell_style_center),
            Paragraph(tot_kd_str, cell_style_center),
            Paragraph(tot_fills_str, cell_style_center)
        ])

    # Pad with empty rows to match reference layout (minimum 8 data rows)
    current_data_rows = len(items)
    desired_data_rows = max(8, current_data_rows)
    for _ in range(desired_data_rows - current_data_rows):
        table_data.append(["", "", "", "", "", ""])

    # Total Row: "total" belongs in the Description column; all remaining columns have individual cells
    total_kd_str = str(quotation.total_kd) if quotation.total_kd else ""
    total_fills_str = str(quotation.total_fills) if quotation.total_fills else ""

    table_data.append([
        Paragraph("total", total_label_style),
        "",
        "",
        "",
        Paragraph(total_kd_str, cell_style_center),
        Paragraph(total_fills_str, cell_style_center)
    ])

    items_table = Table(table_data, colWidths=col_widths, repeatRows=2)
    items_table.setStyle(TableStyle(table_styles))
    story.append(items_table)
    story.append(Spacer(1, 10))

    # 7. Amount in Words (Centered, Bold)
    amount_in_words = quotation.amount_in_words or "KD Twenty Five"
    story.append(Paragraph(f"<b>{amount_in_words}</b>", amount_words_style))
    story.append(Spacer(1, 16))

    # 8. Incharge and Contact Details (Left aligned, Blue link for email)
    incharge_val = quotation.incharge or ""
    incharge_text = f"Incharge: {incharge_val}".strip()
    if not incharge_val:
        incharge_text = "Incharge:"
    story.append(Paragraph(incharge_text, contact_style))
    story.append(Spacer(1, 10))

    email_val = quotation.email or "thilakantmt@gmail.com"
    email_text = f'Email: <font color="#1a0dab"><u>{email_val}</u></font>'
    story.append(Paragraph(email_text, contact_style))
    story.append(Spacer(1, 10))

    phone_val = quotation.phone or "+965 99983543"
    story.append(Paragraph(f"Ph no: {phone_val}", contact_style))
    story.append(Spacer(1, 22))

    # 9. Bottom Horizontal Rule
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=0, spaceAfter=0))

    doc.build(story)
    return output_path
