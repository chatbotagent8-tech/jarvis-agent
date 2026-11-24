import io
import json
import re
import html
import time
import datetime

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------
st.set_page_config(
    page_title="J.A.R.V.I.S. | UAE Product Hunter",
    page_icon="🔵",
    layout="wide",
)

MODEL_NAME = "gemini-3.8-flash"

# ---------------------------------------------------------------
# Jarvis HUD styling
# ---------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@400;500;600&display=swap');

.stApp {
    background: radial-gradient(ellipse at 50% 0%, #07243a 0%, #030b14 60%, #02060b 100%);
    color: #cfefff;
    font-family: 'Rajdhani', sans-serif;
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

.hud-wrap { display: flex; flex-direction: column; align-items: center; margin: 8px 0 18px 0; }
.reactor { position: relative; width: 150px; height: 150px; margin-bottom: 10px; }
.ring { position: absolute; border-radius: 50%; }
.r1 { inset: 0; border: 2px solid rgba(0,200,255,0.25); border-top-color: #00d4ff; animation: spin 6s linear infinite; }
.r2 { inset: 16px; border: 2px dashed rgba(0,200,255,0.45); animation: spin 10s linear infinite reverse; }
.r3 { inset: 34px; border: 3px solid rgba(0,200,255,0.2); border-bottom-color: #5ee3ff; animation: spin 4s linear infinite; }
.core {
    position: absolute; inset: 56px; border-radius: 50%;
    background: radial-gradient(circle, #e6fbff 0%, #00d4ff 55%, #006a8a 100%);
    box-shadow: 0 0 30px #00d4ff, 0 0 70px rgba(0,212,255,0.55);
    animation: pulse 2.4s ease-in-out infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 0%,100% { opacity: 0.75; } 50% { opacity: 1; } }

.title {
    font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 2.1rem;
    letter-spacing: 0.35em; color: #7fe7ff; text-shadow: 0 0 18px rgba(0,212,255,0.8);
    margin: 0; text-align: center;
}
.subtitle { color: #6fb8cf; letter-spacing: 0.12em; font-size: 1.02rem; margin-top: 4px; text-align: center; }

.status-line {
    border: 1px solid rgba(0,212,255,0.35); border-left: 4px solid #00d4ff;
    background: rgba(0,40,60,0.45); padding: 10px 16px; margin: 10px 0 18px 0;
    color: #9fe8ff; font-size: 1.05rem;
}

.card {
    position: relative; border: 1px solid rgba(0,212,255,0.4);
    background: linear-gradient(160deg, rgba(0,60,90,0.55), rgba(2,14,24,0.85));
    padding: 18px 20px; margin-bottom: 18px;
    box-shadow: 0 0 22px rgba(0,212,255,0.12), inset 0 0 24px rgba(0,212,255,0.05);
    clip-path: polygon(0 0, calc(100% - 18px) 0, 100% 18px, 100% 100%, 18px 100%, 0 calc(100% - 18px));
}
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.pname { font-family: 'Orbitron', sans-serif; font-size: 1.15rem; color: #8defff; letter-spacing: 0.04em; }
.score-badge {
    font-family: 'Orbitron', sans-serif; font-size: 1.5rem; color: #031018;
    background: #00d4ff; padding: 4px 12px; box-shadow: 0 0 16px rgba(0,212,255,0.7); white-space: nowrap;
}
.meter { height: 8px; background: rgba(0,212,255,0.15); margin: 12px 0 14px 0; }
.meter > div { height: 100%; background: linear-gradient(90deg, #0090b8, #00e5ff); box-shadow: 0 0 12px #00e5ff; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 12px; }
.stat { border: 1px solid rgba(0,212,255,0.25); padding: 8px 10px; background: rgba(0,25,40,0.6); }
.stat .k { color: #5fa9c0; font-size: 0.85rem; }
.stat .v { color: #dff8ff; font-size: 1.15rem; font-weight: 600; }
.line { margin: 6px 0; color: #bfe9f7; font-size: 1.05rem; line-height: 1.35; }
.line b { color: #7fe7ff; font-weight: 600; }
.risk-low { color: #5dffb0; } .risk-med { color: #ffd166; } .risk-high { color: #ff6b6b; }

div.stButton > button, div.stDownloadButton > button {
    font-family: 'Orbitron', sans-serif; letter-spacing: 0.18em;
    background: transparent; color: #7fe7ff; border: 2px solid #00d4ff; border-radius: 0;
    padding: 0.7rem 1.4rem; box-shadow: 0 0 18px rgba(0,212,255,0.45);
    transition: all 0.2s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover { background: #00d4ff; color: #02121b; box-shadow: 0 0 30px rgba(0,212,255,0.9); }
div.stButton > button:focus-visible, div.stDownloadButton > button:focus-visible { outline: 3px solid #ffffff; outline-offset: 2px; }

label, .stSelectbox label, .stTextInput label { color: #8fd8ee !important; }

@media (prefers-reduced-motion: reduce) {
    .r1, .r2, .r3, .core { animation: none; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    '<div class="hud-wrap">'
    '<div class="reactor"><div class="ring r1"></div><div class="ring r2"></div>'
    '<div class="ring r3"></div><div class="core"></div></div>'
    '<p class="title">J.A.R.V.I.S.</p>'
    '<p class="subtitle">UAE Winning Product Hunter</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# API key
# ---------------------------------------------------------------
api_key = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = None

if not api_key:
    st.markdown(
        '<div class="status-line">Gemini key nahi mili. Streamlit mein App settings > Secrets kholein '
        'aur yeh line daalein: <b>GEMINI_API_KEY = "aapki-key"</b></div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ---------------------------------------------------------------
# Controls
# ---------------------------------------------------------------
CATEGORIES = [
    "Sab categories",
    "Home & Kitchen",
    "Beauty & Personal Care",
    "Gadgets & Accessories",
    "Fitness & Wellness",
    "Car Accessories",
    "Pets",
    "Kids & Baby",
]

col1, col2 = st.columns([1, 1])
with col1:
    category = st.selectbox("Category", CATEGORIES)
with col2:
    extra = st.text_input("Khaas hidayat (optional)", placeholder="maslan: sirf 50 AED se kam wale products")

pasted = st.text_area(
    "Trending products ki list paste karein (optional, behtar results ke liye)",
    placeholder="TikTok Creative Center ya Amazon.ae se 5-10 product naam yahan paste karein, har line mein ek",
    height=110,
)
use_search = st.checkbox(
    "Live Google Search use karein (free key par aksar 429 error deta hai)",
    value=False,
)

run = st.button("RUN JARVIS")


# ---------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------
def build_prompt(category, extra, pasted, use_search):
    today = datetime.date.today().strftime("%d %B %Y")
    cat_line = "Koi bhi category" if category == "Sab categories" else category
    extra_line = extra.strip() if extra else "Koi nahi"
    pasted_text = pasted.strip() if pasted else ""

    if pasted_text:
        source_line = (
            "The user has pasted a list of products they saw trending. Choose the best 5 from this list "
            "(you may add a product only if the list has fewer than 5 usable items):\n" + pasted_text
        )
    elif use_search:
        source_line = (
            "Use Google Search to find products that are trending RIGHT NOW in the UAE (check TikTok trends, "
            "Amazon.ae and Noon best sellers/movers, Google Trends UAE, and recent UAE ad/social trends)."
        )
    else:
        source_line = (
            "You do NOT have live data. Use your general knowledge of products that have performed well "
            "in UAE e-commerce and social media, and say honestly in why_trending that this is based on "
            "general market knowledge and not live data."
        )

    return f"""You are J.A.R.V.I.S., an expert dropshipping product researcher for the UAE market.
Today's date is {today}.

{source_line}

Category focus: {cat_line}
Extra instructions from the user: {extra_line}

Pick exactly 5 products that suit a Shopify dropshipping store selling to the UAE with Cash on Delivery common.

Rules:
- Skip branded or trademarked products, anything with batteries or liquids that is hard to ship, products with medical claims, and anything restricted or banned in the UAE.
- Prefer products with a wow factor, easy to demonstrate in a short video, small and light, selling price roughly 49 to 199 AED, and healthy margin.
- Be honest. If you are unsure about a price or cost, give a cautious estimate. Do not invent statistics.

Return ONLY a valid JSON array (no markdown, no extra text) with exactly 5 objects. Each object must have these keys:
"name": product name,
"why_trending": one or two sentences on why it is trending in the UAE now,
"sell_price_aed": number, estimated selling price in AED,
"supplier_cost_aed": number, estimated landed supplier cost in AED,
"margin_percent": number, estimated gross margin percent,
"cod_risk": "Low" or "Medium" or "High",
"shipping_risk": "Low" or "Medium" or "High",
"ad_angle": the best ad angle or hook for TikTok/Instagram in the UAE,
"search_keyword": a keyword to search this product on AliExpress or CJ Dropshipping,
"score": integer from 1 to 10.
Sort the array from highest score to lowest."""


def parse_products(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(cleaned[start : end + 1])
        if isinstance(data, list):
            return data
    except Exception:
        return None
    return None


STATIC_FALLBACKS = ["gemini-flash-latest", "gemini-flash-lite-latest"]
SKIP_WORDS = ("tts", "image", "live", "embed", "audio", "vision", "robotics", "computer", "thinking-exp")


def is_busy_error(err):
    text = str(err)
    return any(code in text for code in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded", "404", "NOT_FOUND"))


def candidate_models(client):
    names = [MODEL_NAME] + STATIC_FALLBACKS
    try:
        found = []
        for m in client.models.list():
            n = (getattr(m, "name", "") or "").replace("models/", "")
            actions = getattr(m, "supported_actions", None) or []
            if "flash" in n and "generateContent" in actions and not any(w in n for w in SKIP_WORDS):
                found.append(n)
        found.sort(reverse=True)
        names += found[:4]
    except Exception:
        pass
    seen, ordered = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def run_jarvis(category, extra, pasted, use_search):
    # Har request 25 second se zyada na rukay, taake agla model jaldi try ho
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=25000))
    search_on = bool(use_search) and not (pasted and pasted.strip())
    config_kwargs = {"temperature": 0.6}
    if search_on:
        config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    prompt = build_prompt(category, extra, pasted, search_on)

    models = candidate_models(client)
    started = time.time()
    time_budget = 150  # seconds
    error_log = []
    waits = [2, 4, 8, 12, 15]

    for round_no in range(len(waits) + 1):
        for model in models:
            if time.time() - started > time_budget:
                break
            t0 = time.time()
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                text = response.text or ""
                if parse_products(text) is None and round_no < len(waits):
                    error_log.append(model + ": jawab ka format theek nahi tha")
                    continue
                st.session_state["model_used"] = model
                st.session_state["error_log"] = error_log
                return text
            except Exception as e:
                short = str(e).replace("\n", " ")[:90]
                error_log.append(f"{model} ({time.time() - t0:.0f}s): " + short)
                if not is_busy_error(e):
                    st.session_state["error_log"] = error_log
                    raise
        if time.time() - started > time_budget or round_no >= len(waits):
            break
        time.sleep(waits[round_no])

    st.session_state["error_log"] = error_log
    raise RuntimeError("BUSY")


# ---------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------
def esc(value):
    return html.escape(str(value if value is not None else "-"))


def risk_class(value):
    v = str(value).strip().lower()
    if v.startswith("low"):
        return "risk-low"
    if v.startswith("high"):
        return "risk-high"
    return "risk-med"


def to_num(value, default=0):
    try:
        return float(value)
    except Exception:
        return default


def render_card(p):
    score = int(to_num(p.get("score"), 0))
    score = max(0, min(10, score))
    parts = [
        '<div class="card">',
        '<div class="card-head">',
        f'<div class="pname">{esc(p.get("name"))}</div>',
        f'<div class="score-badge">{score}/10</div>',
        "</div>",
        f'<div class="meter"><div style="width:{score * 10}%"></div></div>',
        '<div class="grid">',
        f'<div class="stat"><div class="k">Selling price</div><div class="v">{esc(p.get("sell_price_aed"))} AED</div></div>',
        f'<div class="stat"><div class="k">Supplier cost</div><div class="v">{esc(p.get("supplier_cost_aed"))} AED</div></div>',
        f'<div class="stat"><div class="k">Margin</div><div class="v">{esc(p.get("margin_percent"))}%</div></div>',
        f'<div class="stat"><div class="k">COD risk</div><div class="v {risk_class(p.get("cod_risk"))}">{esc(p.get("cod_risk"))}</div></div>',
        f'<div class="stat"><div class="k">Shipping risk</div><div class="v {risk_class(p.get("shipping_risk"))}">{esc(p.get("shipping_risk"))}</div></div>',
        "</div>",
        f'<div class="line"><b>Kyun trend kar raha hai:</b> {esc(p.get("why_trending"))}</div>',
        f'<div class="line"><b>Ad angle:</b> {esc(p.get("ad_angle"))}</div>',
        f'<div class="line"><b>Supplier search keyword:</b> {esc(p.get("search_keyword"))}</div>',
        "</div>",
    ]
    return "".join(parts)


# ---------------------------------------------------------------
# History: permanent storage (Google Sheet), date range filter, Excel / Word export
# ---------------------------------------------------------------
HISTORY_FILE = "jarvis_history.json"
PKT = datetime.timezone(datetime.timedelta(hours=5))  # Pakistan time


def now_pkt():
    return datetime.datetime.now(PKT)


COLUMNS = [
    "Date", "Time", "Category", "Product", "Score", "Sell price (AED)", "Supplier cost (AED)",
    "Margin (%)", "COD risk", "Shipping risk", "Why trending", "Ad angle", "Supplier keyword",
    "Source", "Status", "Notes",
]
SHOW_COLUMNS = [
    "Date", "Product", "Score", "Sell price (AED)", "Supplier cost (AED)", "Margin (%)",
    "COD risk", "Shipping risk", "Status",
]


def num_or_text(value):
    try:
        x = float(value)
        return int(x) if x == int(x) else round(x, 1)
    except Exception:
        return "" if value is None else str(value)


def norm_date(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return s


def normalize_row(r):
    d = {}
    for c in COLUMNS:
        val = r.get(c, "")
        d[c] = "" if val is None else val
    d["Date"] = norm_date(d["Date"])
    return d


def sheets_configured():
    try:
        return bool(st.secrets.get("GCP_JSON")) and bool(st.secrets.get("SHEET_ID"))
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def get_sheet():
    import gspread

    info = json.loads(st.secrets["GCP_JSON"])
    gc = gspread.service_account_from_dict(info)
    sh = gc.open_by_key(str(st.secrets["SHEET_ID"]).strip())
    ws = sh.sheet1
    if not ws.row_values(1):
        ws.append_row(COLUMNS, value_input_option="RAW")
    return ws


def load_history_file():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [normalize_row(r) for r in data] if isinstance(data, list) else []
    except Exception:
        return []


def save_history_file(rows):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)
    except Exception:
        pass


def load_history():
    if sheets_configured():
        try:
            ws = get_sheet()
            records = ws.get_all_records()
            rows = [normalize_row(r) for r in records if str(r.get("Product", "")).strip()]
            st.session_state["sheet_error"] = None
            return rows
        except Exception as e:
            st.session_state["sheet_error"] = str(e)[:300]
    return load_history_file()


def row_key(r):
    return (str(r.get("Date", "")), str(r.get("Product", "")).strip().lower())


def merge_rows(existing, incoming, override=False):
    result = list(existing)
    index = {row_key(r): i for i, r in enumerate(result)}
    for r in incoming:
        k = row_key(r)
        if k in index:
            if override:
                result[index[k]] = r
        else:
            index[k] = len(result)
            result.append(r)
    return result


def make_rows(products, category, pasted_text, use_search_flag):
    now = now_pkt()
    if pasted_text and pasted_text.strip():
        source = "Pasted list"
    elif use_search_flag:
        source = "Live search"
    else:
        source = "AI knowledge"
    rows = []
    for p in products:
        rows.append({
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%H:%M"),
            "Category": category,
            "Product": str(p.get("name", "")),
            "Score": num_or_text(p.get("score")),
            "Sell price (AED)": num_or_text(p.get("sell_price_aed")),
            "Supplier cost (AED)": num_or_text(p.get("supplier_cost_aed")),
            "Margin (%)": num_or_text(p.get("margin_percent")),
            "COD risk": str(p.get("cod_risk", "")),
            "Shipping risk": str(p.get("shipping_risk", "")),
            "Why trending": str(p.get("why_trending", "")),
            "Ad angle": str(p.get("ad_angle", "")),
            "Supplier keyword": str(p.get("search_keyword", "")),
            "Source": source,
            "Status": "",
            "Notes": "",
        })
    return rows


def add_scan_to_history(products, category, pasted_text, use_search_flag):
    new_rows = make_rows(products, category, pasted_text, use_search_flag)
    hist = st.session_state["history"]
    merged = merge_rows(hist, new_rows)
    fresh = merged[len(hist):]
    if not fresh:
        return
    st.session_state["history"] = merged
    save_history_file(merged)
    if sheets_configured():
        try:
            ws = get_sheet()
            ws.append_rows([[r.get(c, "") for c in COLUMNS] for r in fresh], value_input_option="RAW")
            st.session_state["sheet_error"] = None
        except Exception as e:
            st.session_state["sheet_error"] = str(e)[:300]


def filter_rows(rows, start, end):
    if start is None or end is None:
        return list(rows)
    out = []
    for r in rows:
        try:
            d = datetime.datetime.strptime(str(r.get("Date", "")), "%Y-%m-%d").date()
        except ValueError:
            continue
        if start <= d <= end:
            out.append(r)
    return out


def build_excel(rows):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "Jarvis History"
    ws.append(COLUMNS)
    for r in rows:
        ws.append([r.get(c, "") for c in COLUMNS])
    head_fill = PatternFill("solid", fgColor="0B3A55")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head_fill
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    widths = {
        "Date": 12, "Time": 8, "Category": 18, "Product": 34, "Score": 8, "Sell price (AED)": 14,
        "Supplier cost (AED)": 16, "Margin (%)": 11, "COD risk": 11, "Shipping risk": 13,
        "Why trending": 50, "Ad angle": 50, "Supplier keyword": 28, "Source": 14, "Status": 14, "Notes": 30,
    }
    for i, c in enumerate(COLUMNS, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = widths.get(c, 15)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def read_excel(file):
    from openpyxl import load_workbook

    wb = load_workbook(file, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    header = next(rows_iter, None)
    if not header:
        raise ValueError("File khali hai")
    idx = {str(h).strip(): i for i, h in enumerate(header) if h is not None}
    if "Product" not in idx or "Date" not in idx:
        raise ValueError("Yeh Jarvis ki Excel file nahi lagti (Date aur Product columns chahiye)")
    out = []
    for row in rows_iter:
        if not row or row[idx["Product"]] in (None, ""):
            continue
        d = {}
        for c in COLUMNS:
            val = row[idx[c]] if c in idx and idx[c] < len(row) else ""
            if val is None:
                val = ""
            if isinstance(val, datetime.datetime):
                val = val.strftime("%Y-%m-%d") if c == "Date" else val.strftime("%H:%M")
            elif isinstance(val, datetime.date):
                val = val.strftime("%Y-%m-%d")
            elif isinstance(val, datetime.time):
                val = val.strftime("%H:%M")
            d[c] = val
        out.append(normalize_row(d))
    return out


def build_word(rows):
    from docx import Document

    doc = Document()
    doc.add_heading("JARVIS - UAE Product Hunt Report", 0)
    dates = sorted({str(r.get("Date", "")) for r in rows}, reverse=True)
    for d in dates:
        doc.add_heading(d, level=1)
        for r in [x for x in rows if str(x.get("Date", "")) == d]:
            doc.add_heading(f'{r.get("Product", "")} (Score {r.get("Score", "")}/10)', level=2)
            table = doc.add_table(rows=0, cols=2)
            table.style = "Table Grid"
            for label, key in [
                ("Selling price (AED)", "Sell price (AED)"),
                ("Supplier cost (AED)", "Supplier cost (AED)"),
                ("Margin (%)", "Margin (%)"),
                ("COD risk", "COD risk"),
                ("Shipping risk", "Shipping risk"),
                ("Supplier keyword", "Supplier keyword"),
                ("Status", "Status"),
            ]:
                cells = table.add_row().cells
                cells[0].text = label
                cells[1].text = str(r.get(key, ""))
            doc.add_paragraph("Why trending: " + str(r.get("Why trending", "")))
            doc.add_paragraph("Ad angle: " + str(r.get("Ad angle", "")))
            if r.get("Notes"):
                doc.add_paragraph("Notes: " + str(r.get("Notes", "")))
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


if "history" not in st.session_state:
    st.session_state["history"] = load_history()


# ---------------------------------------------------------------
# Run + show
# ---------------------------------------------------------------
if run:
    with st.spinner("JARVIS UAE market scan kar raha hai..."):
        try:
            raw = run_jarvis(category, extra, pasted, use_search)
            products = parse_products(raw)
            st.session_state["raw"] = raw
            st.session_state["products"] = products
            st.session_state["time"] = now_pkt().strftime("%d %b %Y, %H:%M")
            st.session_state["error"] = None
            if products:
                add_scan_to_history(products, category, pasted, use_search)
        except Exception as e:
            st.session_state["error"] = str(e)

error = st.session_state.get("error")
if error:
    if error == "BUSY":
        msg = (
            "Google ke servers abhi bohat busy hain. JARVIS ne kai models par kai baar koshish ki, "
            "lekin jawab nahi mila. 5-10 minute baad RUN JARVIS dobara dabayein. "
            "Pichla kamyab result (agar tha) neeche mehfooz hai."
        )
    else:
        msg = "Scan nahi ho saka. Detail: " + error[:300]
    st.markdown('<div class="status-line">' + esc(msg) + "</div>", unsafe_allow_html=True)
    log = st.session_state.get("error_log") or []
    if log:
        with st.expander("Technical detail (zaroori nahi)"):
            for line in log[-12:]:
                st.write(line)

products = st.session_state.get("products")
raw = st.session_state.get("raw")

if products:
    st.markdown(
        f'<div class="status-line">Scan mukammal. {len(products)} products mile. '
        f'Waqt: {esc(st.session_state.get("time"))}. Model: {esc(st.session_state.get("model_used"))}</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, p in enumerate(products):
        with cols[i % 2]:
            st.markdown(render_card(p), unsafe_allow_html=True)
    st.caption(
        "Yeh AI ki shortlist hai, guarantee nahi. Prices andaze hain. Test se pehle supplier aur "
        "UAE shipping khud check karein."
    )
elif raw:
    st.markdown(
        '<div class="status-line">Result ka format samajh nahi aaya, raw jawab neeche hai.</div>',
        unsafe_allow_html=True,
    )
    st.write(raw)
elif not error:
    st.markdown(
        '<div class="status-line">Taiyar hoon. Category chunein aur RUN JARVIS dabayein.</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------
# History section (date range + table + Excel / Word download)
# ---------------------------------------------------------------
st.markdown(
    '<div class="status-line"><b>HISTORY</b> - ab tak ke saare products, date ke hisaab se.</div>',
    unsafe_allow_html=True,
)

sheet_on = sheets_configured()
sheet_err = st.session_state.get("sheet_error")
if sheet_on and not sheet_err:
    st.caption("Storage: Google Sheet (hamesha ke liye mehfooz). Date Pakistan time ke hisaab se lagti hai.")
    sid = str(st.secrets["SHEET_ID"]).strip()
    st.markdown(f"[Google Sheet kholein](https://docs.google.com/spreadsheets/d/{sid})")
    if st.button("SHEET SE REFRESH"):
        st.session_state["history"] = load_history()
        st.rerun()
elif sheet_on and sheet_err:
    st.markdown(
        '<div class="status-line">Google Sheet se connect nahi ho saka, abhi temporary storage chal rahi hai. '
        "Detail: " + esc(sheet_err) + "</div>",
        unsafe_allow_html=True,
    )
else:
    st.caption(
        "Storage: temporary. Google Sheet abhi connect nahi hui, is liye app restart par history mit sakti hai. "
        "Excel download karke rakh lein."
    )
    uploaded = st.file_uploader(
        "Purani Jarvis Excel file wapas load karein (optional)", type=["xlsx"], key="history_upload"
    )
    if uploaded is not None:
        try:
            imported = read_excel(uploaded)
            st.session_state["history"] = merge_rows(st.session_state["history"], imported, override=True)
            save_history_file(st.session_state["history"])
            st.caption(f"{len(imported)} purani entries load ho gayin.")
        except Exception as e:
            st.markdown(
                '<div class="status-line">Excel file nahi parhi ja saki: ' + esc(str(e)[:200]) + "</div>",
                unsafe_allow_html=True,
            )

history = st.session_state["history"]
if not history:
    st.caption("Abhi history khali hai. Pehla scan chalayein, products khud save ho jayenge.")
else:
    today = now_pkt().date()
    PRESETS = ["Aaj", "Kal", "Pichle 3 din", "Pichle 5 din", "Pichle 7 din", "Pichle 30 din", "Sab dates", "Apni date range"]
    preset = st.selectbox("Kaunsa data chahiye", PRESETS, index=0)
    start = end = None
    if preset == "Aaj":
        start = end = today
    elif preset == "Kal":
        start = end = today - datetime.timedelta(days=1)
    elif preset.startswith("Pichle"):
        n = int(preset.split()[1])
        start, end = today - datetime.timedelta(days=n - 1), today
    elif preset == "Apni date range":
        picked = st.date_input("Se aur tak date chunein", value=(today - datetime.timedelta(days=4), today))
        if isinstance(picked, (tuple, list)) and len(picked) == 2:
            start, end = picked
        elif isinstance(picked, (tuple, list)) and len(picked) == 1:
            start = end = picked[0]
        else:
            start = end = picked

    shown = filter_rows(history, start, end)
    shown = sorted(shown, key=lambda r: (str(r.get("Date", "")), str(r.get("Time", ""))), reverse=True)

    if not shown:
        st.caption("Is date range mein koi data nahi mila. Doosri range chun kar dekhein.")
    else:
        st.caption(f"{len(shown)} products mile.")
        st.dataframe([{c: r.get(c, "") for c in SHOW_COLUMNS} for r in shown], hide_index=True)
        label = "all" if start is None else (str(start) if start == end else f"{start}_to_{end}")
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "EXCEL DOWNLOAD",
                data=build_excel(shown),
                file_name=f"jarvis_products_{label}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        with d2:
            st.download_button(
                "WORD DOWNLOAD",
                data=build_word(shown),
                file_name=f"jarvis_products_{label}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
    st.caption(
        "Status aur Notes (maslan Tested, Winner, Rejected) aap seedha Google Sheet mein bhar sakte hain. "
        "Sheet mein Date column ko haath se mat badlein."
    )
