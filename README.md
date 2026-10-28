# TTMKQG — Premium Quotation Generator

A premium, modern, fully responsive, and professional web application for generating, managing, and exporting commercial quotations.

The official website name is **TTMKQG**.

---

## 1. Key Capabilities

- **Strict TTMKQG Branding**: Modern, sleek business identity with centralized styling.
- **Dual-Theme Engine (Light &amp; Dark Mode)**: Instant theme toggle with local persistence and automatic OS preference detection. Quotation document sheets remain independent physical white paper.
- **Fully Responsive Architecture**: Custom-tailored layouts for mobile devices (320px+), tablets, laptops, desktops, and ultra-wide screens.
- **Premium Landing Page**: Interactive hero section with floating animated document mockup, feature highlights, and a 3-step workflow.
- **Data-Driven Dashboard**: Live statistics cards (Total Quotations, Total Valuation, Average Value, Active Clients) calculated directly from SQLite records.
- **Advanced Multi-Filter &amp; Search System**: Real-time filtering by quotation number, client name, description, and amount range.
- **ReportLab Vector PDF Generator**: Exact vector PDF document layout with crisp typography, double-tier headers, and commercial invoice borders.
- **python-docx Word Generator**: Generates 100% editable Microsoft Word (.docx) files matching the reference document.
- **Automated Excel Sync (`data/quotations.xlsx`)**: Synchronizes `Quotations` and `Quotation Items` worksheets without creating duplicate records on edits.
- **Kuwait Currency &amp; Word Conversion**: Full support for Kuwaiti Dinar (K.D) and Fils (1 K.D = 1000 Fils) with automatic translation to English currency words.

---

## 2. Project Structure

```
quotation_app/
│
├── main.py                  # FastAPI application with landing, dashboard & export routes
├── database.py              # SQLite configuration and directory initialization
├── models.py                # SQLAlchemy ORM models (Quotation & QuotationItem)
├── quotation_service.py     # Business logic, statistics, and number-to-words
├── word_service.py          # python-docx Word (.docx) document generator
├── pdf_service.py           # ReportLab PDF document generator
├── excel_service.py         # openpyxl two-sheet synchronization (data/quotations.xlsx)
│
├── templates/
│   ├── base.html            # Core layout with TTMKQG navbar, theme toggle & footer
│   ├── landing.html         # Premium landing page with animated hero mockup
│   ├── dashboard.html       # Management dashboard with stats & multi-filter
│   ├── quotation_form.html  # Two-column form with responsive mobile tabs
│   └── quotation_preview.html # Printable document view
│
├── static/
│   ├── style.css            # Complete design system with light/dark CSS variables
│   └── script.js            # Theme switcher, mobile drawer, filters & live preview
│
├── data/
│   ├── quotations.db        # SQLite database
│   └── quotations.xlsx      # Synchronized Excel workbook
│
├── generated/
│   ├── pdf/                 # Generated vector PDF documents
│   └── word/                # Generated editable Word (.docx) documents
│
├── requirements.txt         # Dependencies
├── README.md                # Documentation
└── run.bat                  # One-click Windows runner
```

---

## 3. Running on Windows

Open PowerShell or Command Prompt:

```powershell
cd D:\dash_p\quotation_app

# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run the application
uvicorn main:app --reload
```

Or simply double-click `run.bat` or `..\start_quotation_app.bat`.

Open your browser to:
**`http://127.0.0.1:8000`**

---

## 4. Routes Reference

| Route | Method | Description |
|---|---|---|
| `/` | `GET` | Premium landing page with hero mockup & features |
| `/dashboard` | `GET` | Full management dashboard with statistics & multi-filter |
| `/quotations/new` | `GET` | Quotation creator with live paper preview |
| `/quotations/save` | `POST` | Save new quotation to SQLite & Excel |
| `/quotations/{id}/edit` | `GET` | Edit existing quotation form |
| `/quotations/{id}/update` | `POST` | Update quotation in-place without duplicating |
| `/quotations/{id}/preview` | `GET` | Printable A4 document view |
| `/quotations/{id}/pdf` | `GET` | Download vector PDF (ReportLab) |
| `/quotations/{id}/word` | `GET` | Download editable Word (.docx) |
| `/quotations/{id}/delete` | `POST` | Delete quotation from SQLite & Excel |
| `/data/excel` | `GET` | Download synchronized `quotations.xlsx` workbook |
| `/api/stats` | `GET` | JSON endpoint returning real-time database statistics |
| `/api/number-to-words` | `GET` | Helper API to convert KD and Fils to words |
