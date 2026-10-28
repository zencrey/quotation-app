import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import Quotation, QuotationItem
from excel_service import save_quotation_to_excel, delete_quotation_from_excel
from pdf_service import generate_quotation_pdf
from word_service import generate_quotation_word

def number_to_words(num: int) -> str:
    """Converts a positive integer up to billions into English words."""
    if num == 0:
        return "Zero"

    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    thousands = ["", "Thousand", "Million", "Billion"]

    def process_chunk(n: int) -> str:
        parts = []
        if n >= 100:
            parts.append(ones[n // 100] + " Hundred")
            n %= 100
        if n >= 20:
            parts.append(tens[n // 10])
            n %= 10
        if n > 0:
            parts.append(ones[n])
        return " ".join(parts)

    chunks = []
    chunk_idx = 0
    temp = num
    while temp > 0:
        chunk = temp % 1000
        if chunk != 0:
            chunk_str = process_chunk(chunk)
            if thousands[chunk_idx]:
                chunk_str += " " + thousands[chunk_idx]
            chunks.append(chunk_str)
        temp //= 1000
        chunk_idx += 1

    return " ".join(reversed(chunks)).strip()

def amount_to_kd_words(kd: int, fils: int = 0) -> str:
    """Formats KD and Fils into standard words, e.g. 'KD Twenty Five'."""
    kd_str = number_to_words(kd) if kd > 0 else ""
    if kd_str:
        result = f"KD {kd_str}"
    else:
        result = "KD Zero" if fils == 0 else ""

    if fils > 0:
        fils_str = number_to_words(fils)
        if result:
            result += f" and {fils_str} Fils"
        else:
            result = f"{fils_str} Fils"
    return result or "KD Zero"

def get_all_quotations(
    db: Session,
    search: Optional[str] = None,
    customer: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None
) -> List[Quotation]:
    """Returns list of quotations with flexible filtering."""
    query = db.query(Quotation)
    
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Quotation.quotation_no.ilike(search_pattern),
                Quotation.customer_name.ilike(search_pattern)
            )
        )
        
    if customer and customer.strip():
        query = query.filter(Quotation.customer_name == customer.strip())
        
    if min_amount is not None:
        query = query.filter(Quotation.total_amount >= min_amount)
        
    if max_amount is not None:
        query = query.filter(Quotation.total_amount <= max_amount)

    return query.order_by(Quotation.id.desc()).all()

def get_dashboard_stats(db: Session) -> dict:
    """Calculates summary statistics from real database records."""
    quotations = db.query(Quotation).all()
    total_count = len(quotations)
    total_val = sum(q.total_amount or 0.0 for q in quotations)
    avg_val = (total_val / total_count) if total_count > 0 else 0.0
    customers = sorted(list({q.customer_name.strip() for q in quotations if q.customer_name and q.customer_name.strip()}))
    
    # Calculate whole KD and Fils for total valuation
    tot_kd = int(total_val)
    tot_fills = int(round((total_val - tot_kd) * 1000))

    return {
        "total_count": total_count,
        "total_valuation": round(total_val, 3),
        "total_kd": tot_kd,
        "total_fills": tot_fills,
        "avg_valuation": round(avg_val, 3),
        "customers": customers,
        "customer_count": len(customers)
    }

def get_quotation_by_id(db: Session, quotation_id: int) -> Optional[Quotation]:
    return db.query(Quotation).filter(Quotation.id == quotation_id).first()

def get_quotation_by_no(db: Session, quotation_no: str) -> Optional[Quotation]:
    return db.query(Quotation).filter(Quotation.quotation_no == quotation_no.strip()).first()

def save_or_update_quotation(db: Session, data: dict, quotation_id: Optional[int] = None) -> Tuple[Optional[Quotation], Optional[str]]:
    """
    Saves a new quotation or updates an existing quotation.
    Validates unique quotation_no and synchronizes to Excel, PDF, and Word.
    """
    quotation_no = data.get("quotation_no", "").strip()
    if not quotation_no:
        return None, "Quotation Number is required."

    # Check for existing quotation number
    existing_q = get_quotation_by_no(db, quotation_no)
    if quotation_id:
        quotation = get_quotation_by_id(db, quotation_id)
        if not quotation:
            return None, "Quotation not found."
        if existing_q and existing_q.id != quotation_id:
            return None, f"Quotation Number '{quotation_no}' is already used by another quotation."
    else:
        if existing_q:
            return None, f"Quotation Number '{quotation_no}' already exists. Please use a unique number."
        quotation = Quotation()
        db.add(quotation)

    quotation.quotation_no = quotation_no
    quotation.company_name = data.get("company_name", "WARDHAN TRADING EST.").strip() or "WARDHAN TRADING EST."
    quotation.date = data.get("date", "").strip() or "24/9/2020"
    quotation.customer_name = data.get("customer_name", "").strip() or "Customer"
    quotation.incharge = data.get("incharge", "").strip()
    quotation.email = data.get("email", "").strip() or "thilakantmt@gmail.com"
    quotation.phone = data.get("phone", "").strip() or "+965 99983543"

    # Process Items
    raw_items = data.get("items", [])
    if quotation_id:
        # Clear existing items
        quotation.items.clear()
        db.flush()

    total_amount_sum = 0.0
    items_to_add = []

    for idx, item_data in enumerate(raw_items, start=1):
        desc = (item_data.get("description") or "").strip()
        if not desc:
            continue

        try:
            qty = float(item_data.get("quantity") or 0.0)
        except (ValueError, TypeError):
            qty = 0.0

        try:
            u_kd = int(item_data.get("unit_price_kd") or 0)
        except (ValueError, TypeError):
            u_kd = 0

        try:
            u_fills = int(item_data.get("unit_price_fills") or 0)
        except (ValueError, TypeError):
            u_fills = 0

        # Check line totals
        try:
            t_kd = int(item_data.get("total_kd") or 0)
        except (ValueError, TypeError):
            t_kd = 0

        try:
            t_fills = int(item_data.get("total_fills") or 0)
        except (ValueError, TypeError):
            t_fills = 0

        unit_price_float = u_kd + (u_fills / 1000.0)
        
        # Calculate line total if not explicitly provided or if qty and unit price are set
        if qty > 0 and unit_price_float > 0:
            calc_line_total = qty * unit_price_float
            t_kd = int(calc_line_total)
            t_fills = int(round((calc_line_total - t_kd) * 1000))
            line_total_float = calc_line_total
        else:
            line_total_float = t_kd + (t_fills / 1000.0)
            if qty > 0 and line_total_float > 0 and unit_price_float == 0:
                unit_price_float = line_total_float / qty
                u_kd = int(unit_price_float)
                u_fills = int(round((unit_price_float - u_kd) * 1000))

        item_obj = QuotationItem(
            item_order=idx,
            description=desc,
            quantity=qty,
            unit_price_kd=u_kd,
            unit_price_fills=u_fills,
            total_kd=t_kd,
            total_fills=t_fills,
            total_price=line_total_float
        )
        items_to_add.append(item_obj)
        total_amount_sum += line_total_float

    quotation.items = items_to_add
    quotation.total_amount = round(total_amount_sum, 3)
    quotation.total_kd = int(quotation.total_amount)
    quotation.total_fills = int(round((quotation.total_amount - quotation.total_kd) * 1000))

    # Amount in words
    custom_words = data.get("amount_in_words", "").strip()
    if custom_words:
        quotation.amount_in_words = custom_words
    else:
        quotation.amount_in_words = amount_to_kd_words(quotation.total_kd, quotation.total_fills)

    db.commit()
    db.refresh(quotation)

    # Automatically synchronize with Excel workbook
    try:
        save_quotation_to_excel(quotation, quotation.items)
    except Exception as e:
        print(f"Warning: Failed to sync Excel: {e}")

    # Generate PDF and Word files
    try:
        generate_quotation_pdf(quotation, quotation.items)
    except Exception as e:
        print(f"Warning: Failed to generate PDF: {e}")

    try:
        generate_quotation_word(quotation, quotation.items)
    except Exception as e:
        print(f"Warning: Failed to generate Word: {e}")

    return quotation, None

def delete_quotation(db: Session, quotation_id: int) -> bool:
    """Deletes a quotation from SQLite and synchronizes deletion in Excel."""
    quotation = get_quotation_by_id(db, quotation_id)
    if not quotation:
        return False
    
    db.delete(quotation)
    db.commit()

    try:
        delete_quotation_from_excel(quotation_id)
    except Exception as e:
        print(f"Warning: Failed to delete from Excel: {e}")

    return True

def seed_sample_quotation(db: Session):
    """Seeds the reference PDF sample quotation if database is empty."""
    if db.query(Quotation).count() == 0:
        sample_data = {
            "quotation_no": "203/2020",
            "company_name": "WARDHAN TRADING EST.",
            "date": "24/9/2020",
            "customer_name": "Radisson Blue Hotel, Kuwait",
            "incharge": "",
            "email": "thilakantmt@gmail.com",
            "phone": "+965 99983543",
            "amount_in_words": "KD Twenty Five",
            "items": [
                {
                    "description": "Roll curtain one window\nMaterial and fitting",
                    "quantity": 1,
                    "unit_price_kd": 25,
                    "unit_price_fills": 0,
                    "total_kd": 25,
                    "total_fills": 0
                }
            ]
        }
        save_or_update_quotation(db, sample_data)
