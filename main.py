import os
import re
import secrets
import hmac
import hashlib
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pdf_service import generate_quotation_pdf, PDF_DIR, sanitize_filename
from word_service import generate_quotation_word, WORD_DIR
from quotation_service import amount_to_kd_words

BASE_DIR = Path(__file__).resolve().parent

# ================= Security Configurations =================
# Server-side cryptographic secret for signing sessions
SERVER_SECRET = secrets.token_hex(32)

# High-security salted password verification
# Plaintext password is NEVER stored anywhere in code or database
PASSWORD_SALT = "wt_quotation_2026_sec_salt"
PASSWORD_HASH = "178740395d5cbf6687602daf8060db236cc79ae78aecac1e4ce0e0ea24830b2e"

# Strict 3-try lockout rule
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes (900 seconds)

# In-memory IP-based attempt tracking: {ip: {"attempts": int, "lockout_until": float}}
FAILED_LOGINS = {}

def get_client_ip(request: Request) -> str:
    """Extracts client IP, supporting forward headers if reverse-proxied."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def check_ip_lockout(ip: str) -> tuple[bool, int]:
    """Checks whether an IP is currently locked out. Returns (is_locked, remaining_seconds)."""
    record = FAILED_LOGINS.get(ip)
    if not record:
        return False, 0
    now = time.time()
    if record["lockout_until"] > now:
        return True, int(record["lockout_until"] - now)
    return False, 0

def record_failed_attempt(ip: str) -> tuple[int, int]:
    """Records a failed attempt for an IP. Returns (attempts_left, lockout_seconds)."""
    now = time.time()
    record = FAILED_LOGINS.get(ip)
    # Reset if no previous record or if a previous lockout expired
    if not record or (record["lockout_until"] > 0 and record["lockout_until"] <= now):
        record = {"attempts": 1, "lockout_until": 0.0}
    else:
        record["attempts"] += 1

    if record["attempts"] >= MAX_FAILED_ATTEMPTS:
        record["lockout_until"] = now + LOCKOUT_DURATION_SECONDS
        FAILED_LOGINS[ip] = record
        return 0, LOCKOUT_DURATION_SECONDS

    FAILED_LOGINS[ip] = record
    return MAX_FAILED_ATTEMPTS - record["attempts"], 0

def record_login_success(ip: str):
    """Resets failed attempt counters for an IP upon successful login."""
    if ip in FAILED_LOGINS:
        del FAILED_LOGINS[ip]

def verify_credentials(username: str, password: str) -> bool:
    """Constant-time cryptographic credential verification."""
    if not secrets.compare_digest(username.strip(), "user"):
        return False
    computed_hash = hashlib.sha256((PASSWORD_SALT + password.strip()).encode()).hexdigest()
    return secrets.compare_digest(computed_hash, PASSWORD_HASH)

def create_session_token() -> str:
    """Generates a cryptographically signed session token."""
    session_id = secrets.token_urlsafe(32)
    ts = str(int(time.time()))
    sig = hmac.new(SERVER_SECRET.encode(), f"{session_id}:{ts}".encode(), hashlib.sha256).hexdigest()
    return f"{session_id}:{ts}:{sig}"

def is_authenticated(request: Request) -> bool:
    """Validates session token from HTTP-only cookie or custom authorization header."""
    token = request.cookies.get("wt_session") or request.headers.get("X-Session-Token")
    if not token or ":" not in token:
        return False
    parts = token.split(":")
    if len(parts) != 3:
        return False
    session_id, ts, sig = parts
    expected_sig = hmac.new(SERVER_SECRET.encode(), f"{session_id}:{ts}".encode(), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(sig, expected_sig):
        return False
    try:
        if time.time() - int(ts) > 86400 * 7:  # 7-day session validity
            return False
    except ValueError:
        return False
    return True

# ================= FastAPI Application =================
app = FastAPI(
    title="WARDHAN TRADING EST. — Quotation Generator",
    description="Offline mobile-first quotation generator with bank-grade 3-attempt security lockout",
    version="2.1.0"
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Mount static files and templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def parse_quotation_form(form_data):
    """
    Parses form submission into lightweight objects without database persistence.
    """
    descriptions = form_data.getlist("item_description[]")
    quantities = form_data.getlist("item_quantity[]")
    unit_kds = form_data.getlist("item_unit_kd[]")
    unit_fillss = form_data.getlist("item_unit_fills[]")
    total_kds = form_data.getlist("item_total_kd[]")
    total_fillss = form_data.getlist("item_total_fills[]")

    items = []
    grand_kd = 0
    grand_fills = 0

    for i in range(len(descriptions)):
        desc = descriptions[i].strip() if i < len(descriptions) else ""
        if not desc:
            continue
        qty_str = quantities[i].strip() if i < len(quantities) else ""
        qty_val = ""
        if qty_str:
            try:
                q_f = float(qty_str)
                qty_val = int(q_f) if q_f.is_integer() else q_f
            except ValueError:
                qty_val = qty_str

        try:
            ukd = int(unit_kds[i]) if i < len(unit_kds) and unit_kds[i].strip() else ""
        except ValueError:
            ukd = ""

        try:
            ufills = int(unit_fillss[i]) if i < len(unit_fillss) and unit_fillss[i].strip() else ""
        except ValueError:
            ufills = ""

        try:
            tkd = int(total_kds[i]) if i < len(total_kds) and total_kds[i].strip() else ""
        except ValueError:
            tkd = ""

        try:
            tfills = int(total_fillss[i]) if i < len(total_fillss) and total_fillss[i].strip() else ""
        except ValueError:
            tfills = ""

        # Auto-compute line total only if total was NOT entered manually and both qty and unit price exist
        if tkd == "" and tfills == "" and isinstance(qty_val, (int, float)) and qty_val > 0 and (ukd != "" or ufills != ""):
            unit_total = (ukd if isinstance(ukd, int) else 0) + ((ufills if isinstance(ufills, int) else 0) / 1000.0)
            line_total = qty_val * unit_total
            tkd = int(line_total)
            tfills = round((line_total - tkd) * 1000)

        line_kd_int = tkd if isinstance(tkd, int) else 0
        line_fills_int = tfills if isinstance(tfills, int) else 0
        grand_kd += line_kd_int
        grand_fills += line_fills_int

        item_ns = SimpleNamespace(
            description=desc,
            quantity=qty_val,
            unit_price_kd=ukd,
            unit_price_fills=ufills,
            total_kd=tkd,
            total_fills=tfills
        )
        items.append(item_ns)

    if grand_fills >= 1000:
        grand_kd += grand_fills // 1000
        grand_fills = grand_fills % 1000

    amount_words = form_data.get("amount_in_words") or ""
    if not amount_words.strip() and (grand_kd > 0 or grand_fills > 0):
        amount_words = amount_to_kd_words(grand_kd, grand_fills)

    quotation = SimpleNamespace(
        company_name=form_data.get("company_name", "WARDHAN TRADING EST.").strip(),
        date=form_data.get("date", "").strip(),
        quotation_no=form_data.get("quotation_no", "").strip(),
        customer_name=form_data.get("customer_name", "").strip(),
        amount_in_words=amount_words.strip(),
        incharge=form_data.get("incharge", "").strip(),
        email=form_data.get("email", "").strip(),
        phone=form_data.get("phone", "").strip(),
        total_kd=grand_kd if grand_kd > 0 else "",
        total_fills=grand_fills if grand_fills > 0 else ""
    )

    return quotation, items

# ================= Routes =================

@app.get("/", response_class=HTMLResponse)
async def home_app(request: Request):
    """
    Renders the unified mobile-first quotation generator.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

@app.post("/api/auth/login")
async def login_api(request: Request):
    """
    Strict 3-try login verification endpoint with automatic IP lockout.
    """
    client_ip = get_client_ip(request)
    locked, remaining = check_ip_lockout(client_ip)
    if locked:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "locked": True,
                "lockout_remaining": remaining,
                "message": f"Security Lockdown: 3 failed attempts exceeded. Access locked for {remaining // 60}m {remaining % 60}s."
            }
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    username = str(body.get("username", ""))
    password = str(body.get("password", ""))

    if verify_credentials(username, password):
        record_login_success(client_ip)
        token = create_session_token()
        response = JSONResponse(content={"success": True, "token": token})
        response.set_cookie(
            key="wt_session",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7
        )
        return response
    else:
        attempts_left, lockout_sec = record_failed_attempt(client_ip)
        if attempts_left == 0:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "locked": True,
                    "lockout_remaining": lockout_sec,
                    "message": "Security Lockdown: 3 failed attempts exceeded. Access locked for 15 minutes."
                }
            )
        else:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "locked": False,
                    "attempts_left": attempts_left,
                    "message": f"Incorrect credentials. {attempts_left} attempt{'s' if attempts_left > 1 else ''} remaining."
                }
            )

@app.post("/api/auth/logout")
async def logout_api():
    """Clears session cookie."""
    response = JSONResponse(content={"success": True})
    response.delete_cookie(key="wt_session")
    return response

@app.get("/api/auth/status")
async def auth_status_api(request: Request):
    """Returns current auth and lockout state for client."""
    client_ip = get_client_ip(request)
    locked, remaining = check_ip_lockout(client_ip)
    record = FAILED_LOGINS.get(client_ip)
    attempts_used = record["attempts"] if record and not locked else 0
    return {
        "authenticated": is_authenticated(request),
        "locked": locked,
        "lockout_remaining": remaining,
        "attempts_left": max(0, MAX_FAILED_ATTEMPTS - attempts_used)
    }

@app.post("/api/pdf")
async def generate_pdf_endpoint(request: Request):
    """
    Generates and downloads ReportLab PDF on-the-fly without saving to database.
    Requires authenticated session.
    """
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")

    form_data = await request.form()
    quotation, items = parse_quotation_form(form_data)

    safe_q_no = sanitize_filename(quotation.quotation_no or "draft")
    file_path = PDF_DIR / f"Quotation_{safe_q_no}.pdf"

    generate_quotation_pdf(quotation, items, output_path=str(file_path))

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"Quotation_{safe_q_no}.pdf"
    )

@app.post("/api/word")
async def generate_word_endpoint(request: Request):
    """
    Generates and downloads Word (.docx) document on-the-fly without saving to database.
    Requires authenticated session.
    """
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")

    form_data = await request.form()
    quotation, items = parse_quotation_form(form_data)

    safe_q_no = sanitize_filename(quotation.quotation_no or "draft")
    file_path = WORD_DIR / f"Quotation_{safe_q_no}.docx"

    generate_quotation_word(quotation, items, output_path=str(file_path))

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"Quotation_{safe_q_no}.docx"
    )

@app.get("/api/number-to-words")
async def api_number_to_words(kd: int = 0, fils: int = 0):
    """Helper API to convert KD and Fils to Kuwait Currency words."""
    words = amount_to_kd_words(kd, fils)
    return {"kd": kd, "fils": fils, "words": words}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
