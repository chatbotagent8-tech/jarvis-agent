import hashlib
import io
import json
import re
import html
import time
import datetime
from urllib.parse import quote_plus

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
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');

:root {
    --cy: #00e5ff; --cy2: #7fe7ff; --line: rgba(0,212,255,0.38);
    --txt: #cfefff; --mut: #7fc2d6; --panel: rgba(0,38,58,0.55);
}

.stApp {
    background:
        radial-gradient(ellipse at 50% -10%, rgba(0,150,210,0.35) 0%, rgba(3,11,20,0) 55%),
        repeating-linear-gradient(0deg, rgba(0,212,255,0.045) 0 1px, transparent 1px 44px),
        repeating-linear-gradient(90deg, rgba(0,212,255,0.045) 0 1px, transparent 1px 44px),
        radial-gradient(ellipse at 50% 0%, #07243a 0%, #030b14 60%, #02060b 100%);
    color: var(--txt);
    font-family: 'Rajdhani', sans-serif;
}
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background: repeating-linear-gradient(0deg, rgba(0,0,0,0) 0 2px, rgba(0,212,255,0.03) 2px 3px);
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1180px; padding-top: 1.4rem; }

.scanband {
    position: fixed; left: 0; right: 0; top: -20%; height: 18%; pointer-events: none; z-index: 0;
    background: linear-gradient(180deg, transparent, rgba(0,229,255,0.06), transparent);
    animation: scanband 9s linear infinite;
}
@keyframes scanband { to { top: 110%; } }

.corner {
    position: fixed; width: 34px; height: 34px; border: 2px solid var(--cy); opacity: 0.75;
    pointer-events: none; z-index: 50; filter: drop-shadow(0 0 6px var(--cy));
}
.c-tl { top: 10px; left: 10px; border-right: 0; border-bottom: 0; }
.c-tr { top: 10px; right: 10px; border-left: 0; border-bottom: 0; }
.c-bl { bottom: 10px; left: 10px; border-right: 0; border-top: 0; }
.c-br { bottom: 10px; right: 10px; border-left: 0; border-top: 0; }

/* ---------- Header ---------- */
.hud-wrap { display: flex; flex-direction: column; align-items: center; margin: 4px 0 6px 0; position: relative; z-index: 2; }
.reactor { position: relative; width: 180px; height: 180px; margin: 10px 0 14px 0; }
.reactor > div { position: absolute; border-radius: 50%; }
.ticks {
    inset: 0;
    background: repeating-conic-gradient(rgba(0,229,255,0.8) 0 0.8deg, transparent 0.8deg 7.5deg);
    -webkit-mask: radial-gradient(circle closest-side, transparent 0 80px, #000 81px 88px, transparent 89px);
            mask: radial-gradient(circle closest-side, transparent 0 80px, #000 81px 88px, transparent 89px);
    animation: spin 40s linear infinite reverse;
}
.r1 { inset: 12px; border: 2px solid rgba(0,200,255,0.25); border-top-color: #00e5ff; border-right-color: #00e5ff; animation: spin 6s linear infinite; }
.r2 { inset: 28px; border: 2px dashed rgba(0,200,255,0.5); animation: spin 11s linear infinite reverse; }
.r3 { inset: 46px; border: 3px solid rgba(0,200,255,0.2); border-bottom-color: #5ee3ff; animation: spin 4s linear infinite; }
.sweep {
    inset: 12px;
    background: conic-gradient(from 0deg, rgba(0,229,255,0.38), rgba(0,229,255,0) 28%, rgba(0,229,255,0) 100%);
    -webkit-mask: radial-gradient(circle closest-side, transparent 0 26px, #000 27px);
            mask: radial-gradient(circle closest-side, transparent 0 26px, #000 27px);
    animation: spin 3.2s linear infinite;
}
.core {
    inset: 70px;
    background: radial-gradient(circle, #f2fdff 0%, #00e5ff 55%, #006a8a 100%);
    box-shadow: 0 0 34px #00e5ff, 0 0 80px rgba(0,229,255,0.6);
    animation: pulse 2.4s ease-in-out infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 0%,100% { opacity: 0.75; } 50% { opacity: 1; } }

.title {
    font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 2.5rem; letter-spacing: 0.42em;
    margin: 0 0 0 0.42em; text-align: center;
    background: linear-gradient(180deg, #f2fdff 10%, #38d6ff 90%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
    filter: drop-shadow(0 0 14px rgba(0,212,255,0.75));
}
.subtitle {
    color: var(--mut); letter-spacing: 0.32em; font-size: 0.95rem; margin: 6px 0 0 0.32em;
    text-align: center; font-weight: 600;
}
.rule {
    width: min(560px, 90%); height: 1px; margin: 14px 0 4px 0;
    background: linear-gradient(90deg, transparent, var(--cy), transparent);
    box-shadow: 0 0 12px var(--cy);
}

.telemetry { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 10px; margin: 8px 0 18px 0; position: relative; z-index: 2; }
.chip {
    font-family: 'Share Tech Mono', monospace; font-size: 0.82rem; letter-spacing: 0.08em; color: #aeeeff;
    border: 1px solid var(--line); background: rgba(0,35,55,0.6); padding: 4px 10px;
}
.dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 7px;
    background: #5dffb0; box-shadow: 0 0 8px #5dffb0; animation: pulse 1.8s ease-in-out infinite;
}

/* ---------- Section headings ---------- */
.sec {
    font-family: 'Orbitron', sans-serif; letter-spacing: 0.28em; font-size: 0.85rem; color: var(--cy2);
    margin: 26px 0 12px 0; display: flex; align-items: center; gap: 12px; position: relative; z-index: 2;
}
.sec b { color: var(--cy); }
.sec::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, var(--line), transparent); }

.status-line {
    border: 1px solid var(--line); border-left: 4px solid var(--cy);
    background: rgba(0,40,60,0.5); padding: 10px 16px; margin: 10px 0 18px 0;
    color: #aeeeff; font-size: 1.05rem; position: relative; z-index: 2;
}

/* ---------- Cards ---------- */
.card {
    position: relative; z-index: 2; border: 1px solid var(--line);
    background: linear-gradient(160deg, rgba(0,62,94,0.6), rgba(2,14,24,0.88));
    padding: 16px 20px 18px 20px; margin-bottom: 18px;
    box-shadow: 0 0 22px rgba(0,212,255,0.12), inset 0 0 24px rgba(0,212,255,0.05);
    clip-path: polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 20px 100%, 0 calc(100% - 20px));
    animation: rise 0.55s ease both; animation-delay: var(--d, 0s);
}
.card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 20px; height: 2px;
    background: linear-gradient(90deg, var(--cy), transparent);
}
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
.card-top { display: flex; justify-content: space-between; margin-bottom: 8px; }
.tag { font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; letter-spacing: 0.18em; color: var(--cy); }
.tag.dim { color: var(--mut); }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 14px; }
.pname { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: #8defff; letter-spacing: 0.04em; line-height: 1.35; }

.gauge {
    position: relative; width: 66px; height: 66px; border-radius: 50%; flex: 0 0 auto;
    display: grid; place-items: center;
    background: conic-gradient(var(--cy) calc(var(--p) * 1%), rgba(0,212,255,0.15) 0);
    box-shadow: 0 0 18px rgba(0,229,255,0.45);
}
.gauge::before { content: ""; position: absolute; inset: 6px; border-radius: 50%; background: #031420; }
.gauge span {
    position: relative; font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.4rem;
    color: #e6fbff; line-height: 1; margin-top: -7px;
}
.gauge small { position: absolute; bottom: 11px; font-size: 0.62rem; color: var(--mut); letter-spacing: 0.05em; }

.seg { display: flex; gap: 4px; margin: 12px 0 14px 0; }
.seg i { flex: 1; height: 8px; background: rgba(0,212,255,0.14); }
.seg i.on { background: linear-gradient(90deg, #0090b8, #00e5ff); box-shadow: 0 0 10px rgba(0,229,255,0.8); }

.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 12px; }
.stat { border: 1px solid rgba(0,212,255,0.25); padding: 8px 10px; background: rgba(0,25,40,0.65); }
.stat .k { color: var(--mut); font-size: 0.85rem; letter-spacing: 0.04em; }
.stat .v { color: #e6fbff; font-family: 'Share Tech Mono', monospace; font-size: 1.25rem; }
.line { margin: 6px 0; color: #bfe9f7; font-size: 1.05rem; line-height: 1.4; }
.line b { color: var(--cy2); font-weight: 700; letter-spacing: 0.03em; }
.risk-low { color: #5dffb0; text-shadow: 0 0 8px rgba(93,255,176,0.5); }
.risk-med { color: #ffd166; text-shadow: 0 0 8px rgba(255,209,102,0.45); }
.risk-high { color: #ff6b6b; text-shadow: 0 0 8px rgba(255,107,107,0.5); }

.verify { margin-top: 12px; padding-top: 10px; border-top: 1px dashed rgba(0,212,255,0.3); }
.vtitle { font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; letter-spacing: 0.16em; color: var(--cy); }
.vlinks { margin-top: 4px; }
.vlink {
    display: inline-block; margin: 6px 8px 0 0; padding: 7px 12px;
    font-family: 'Share Tech Mono', monospace; font-size: 0.82rem; letter-spacing: 0.08em;
    color: #aeeeff !important; text-decoration: none !important;
    border: 1px solid var(--line); background: rgba(0,35,55,0.65); transition: all 0.15s ease;
}
.vlink:hover { background: var(--cy); color: #02121b !important; box-shadow: 0 0 14px rgba(0,229,255,0.8); }
.vlink:focus-visible { outline: 2px solid #ffffff; outline-offset: 2px; }
.vhint { margin-top: 8px; color: var(--mut); font-size: 0.92rem; line-height: 1.35; }

.pimg {
    width: 84px; height: 84px; object-fit: contain; background: #ffffff; padding: 3px;
    border: 1px solid var(--line); flex: 0 0 auto;
}
.lrow { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; margin-top: 8px; }
.lstore { font-weight: 700; color: var(--cy2); min-width: 90px; }
.lprice { font-family: 'Share Tech Mono', monospace; color: #e6fbff; }
.lrate { color: var(--mut); font-size: 0.95rem; }
.lrow .vlink { margin: 0; padding: 4px 10px; }

.bubble {
    position: relative; z-index: 2; margin: 8px 0; padding: 10px 14px; max-width: 86%;
    border: 1px solid var(--line); line-height: 1.4; font-size: 1.05rem;
}
.bubble.user { margin-left: auto; background: rgba(0,60,90,0.5); border-right: 3px solid var(--cy); }
.bubble.jarvis { background: rgba(0,30,48,0.7); border-left: 3px solid var(--cy); }
.bubble .who {
    display: block; margin-bottom: 2px; font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem; letter-spacing: 0.18em; color: var(--cy);
}

/* ---------- Controls ---------- */
div.stButton > button, div.stDownloadButton > button {
    font-family: 'Orbitron', sans-serif; letter-spacing: 0.2em; font-weight: 700;
    background: rgba(0,35,55,0.5); color: #7fe7ff; border: 2px solid #00d4ff; border-radius: 0;
    padding: 0.7rem 1.5rem; box-shadow: 0 0 18px rgba(0,212,255,0.45), inset 0 0 14px rgba(0,212,255,0.12);
    transition: all 0.2s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover { background: #00d4ff; color: #02121b; box-shadow: 0 0 32px rgba(0,212,255,0.95); }
div.stButton > button:active, div.stDownloadButton > button:active { transform: scale(0.98); }
div.stButton > button:focus-visible, div.stDownloadButton > button:focus-visible { outline: 3px solid #ffffff; outline-offset: 2px; }

div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea, .stDateInput input {
    background: rgba(0,28,44,0.75) !important; color: #dff8ff !important;
    border: 1px solid rgba(0,212,255,0.45) !important; border-radius: 0 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus { box-shadow: 0 0 14px rgba(0,229,255,0.55) !important; }
div[data-testid="stExpander"] { border: 1px solid var(--line) !important; background: rgba(0,25,40,0.5); border-radius: 0 !important; }
div[data-testid="stCaptionContainer"] { color: var(--mut); }
label, .stSelectbox label, .stTextInput label { color: #8fd8ee !important; }

@media (max-width: 640px) {
    .title { font-size: 1.55rem; letter-spacing: 0.24em; margin-left: 0.24em; }
    .subtitle { letter-spacing: 0.16em; font-size: 0.85rem; }
    .corner { display: none; }
    .pname { font-size: 1rem; }
}
@media (prefers-reduced-motion: reduce) {
    .ticks, .r1, .r2, .r3, .sweep, .core, .dot, .scanband, .card { animation: none; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    '<div class="scanband"></div>'
    '<div class="corner c-tl"></div><div class="corner c-tr"></div>'
    '<div class="corner c-bl"></div><div class="corner c-br"></div>'
    '<div class="hud-wrap">'
    '<div class="reactor"><div class="ticks"></div><div class="r1"></div><div class="r2"></div>'
    '<div class="r3"></div><div class="sweep"></div><div class="core"></div></div>'
    '<p class="title">J.A.R.V.I.S.</p>'
    '<p class="subtitle">UAE WINNING PRODUCT HUNTER</p>'
    '<div class="rule"></div>'
    '</div>',
    unsafe_allow_html=True,
)
telemetry = st.empty()

# ---------------------------------------------------------------
# Login (Google): sirf login karne wale hi app use kar sakte hain
# ---------------------------------------------------------------
def _auth_ready():
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def _admin_emails():
    try:
        raw = str(st.secrets.get("ADMIN_EMAILS") or "")
    except Exception:
        raw = ""
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


_user = getattr(st, "user", None)
if _user is None or not _auth_ready():
    st.markdown(
        '<div class="status-line">Login abhi set nahi hua, is liye app band hai. '
        "Owner Secrets mein [auth] wali settings lagayein.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

if not getattr(_user, "is_logged_in", False):
    st.markdown('<div class="sec"><b>//</b> ACCESS CONTROL</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="status-line">Jarvis istemal karne ke liye apne Google (Gmail) account se login karein. '
        "Login ke liye Google aap ka naam aur email Jarvis ko deta hai.</div>",
        unsafe_allow_html=True,
    )
    st.button("LOGIN WITH GOOGLE", on_click=st.login)
    st.stop()

USER_EMAIL = str(getattr(_user, "email", "") or "").strip().lower()
USER_NAME = str(getattr(_user, "name", "") or "").strip()
if not USER_EMAIL or getattr(_user, "email_verified", True) is False:
    st.markdown(
        '<div class="status-line">Is Google account ka email verify nahi hua, is liye login qabool nahi hua.</div>',
        unsafe_allow_html=True,
    )
    st.button("LOGOUT", on_click=st.logout)
    st.stop()

IS_ADMIN = USER_EMAIL in _admin_emails()
if st.session_state.get("active_user") != USER_EMAIL:
    # koi aur banda isi browser mein login kare to pichle user ka data saaf
    for _k in ("history", "products", "raw", "error", "error_log", "model_used", "sources", "time",
               "sheet_error", "user_gemini_key", "user_serper_key", "history_upload", "chat",
               "last_audio_hash", "speak_now"):
        st.session_state.pop(_k, None)
    st.session_state["active_user"] = USER_EMAIL
st.session_state["is_admin"] = IS_ADMIN

_c1, _c2 = st.columns([4, 1])
with _c1:
    st.caption(f"Login: {USER_NAME or USER_EMAIL} ({'Owner' if IS_ADMIN else 'User'})")
with _c2:
    st.button("LOGOUT", on_click=st.logout)

# ---------------------------------------------------------------
# API key
# ---------------------------------------------------------------
api_key = None
if IS_ADMIN:
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
else:
    st.markdown('<div class="sec"><b>//</b> YOUR API KEYS</div>', unsafe_allow_html=True)
    st.caption(
        "Har user apni free Gemini key istemal karta hai, taake limit aap ki apni ho. Key sirf is session mein "
        "rehti hai, kahin save nahi hoti. Free key aistudio.google.com par Get API key se milti hai."
    )
    _gk = st.text_input("Apni Gemini API key", type="password", key="user_gemini_key")
    st.text_input(
        "Serper API key (optional, asli listings aur product photo ke liye)", type="password", key="user_serper_key"
    )
    api_key = (_gk or "").strip() or None

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

st.markdown('<div class="sec"><b>//</b> MISSION PARAMETERS</div>', unsafe_allow_html=True)
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
- Never invent URLs, sales numbers, order counts or review counts.

Return ONLY a valid JSON array (no markdown, no extra text) with exactly 5 objects. Each object must have these keys:
"name": product name,
"why_trending": one or two sentences on why it is trending in the UAE now,
"sell_price_aed": number, estimated selling price in AED,
"supplier_cost_aed": number, estimated landed supplier cost in AED,
"margin_percent": number, estimated gross margin percent,
"cod_risk": "Low" or "Medium" or "High",
"shipping_risk": "Low" or "Medium" or "High",
"ad_angle": the best ad angle or hook for TikTok/Instagram in the UAE,
"why_chosen": two sentences on why this product can sell in the UAE (who buys it, what problem it solves, why it suits COD and a short video),
"potential": "High" or "Medium" or "Low", followed by a dash and a short reason,
"likely_platforms": where it most likely sells in the UAE (for example Amazon.ae, Noon, TikTok Shop, Instagram stores, Talabat). These are guesses for the user to verify,
"search_keyword": a short generic 2 to 4 word product search phrase with no brand names, that works on Amazon.ae, Noon and AliExpress,
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
    tokens = (
        "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded", "404", "NOT_FOUND",
        "504", "DEADLINE_EXCEEDED", "INTERNAL", "timed out", "Timeout", "timeout", "ConnectError",
    )
    return any(t in text for t in tokens)


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
    # Har request 60 second tak rukay, phir agla model try ho
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000))
    search_on = bool(use_search) and not (pasted and pasted.strip())
    config_kwargs = {"temperature": 0.6}
    if search_on:
        config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    prompt = build_prompt(category, extra, pasted, search_on)

    models = candidate_models(client)
    started = time.time()
    time_budget = 170  # seconds
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
                sources = []
                if search_on:
                    try:
                        gm = response.candidates[0].grounding_metadata
                        for ch in (gm.grounding_chunks or []):
                            w = getattr(ch, "web", None)
                            if w is not None and getattr(w, "uri", None):
                                sources.append((getattr(w, "title", None) or w.uri, w.uri))
                    except Exception:
                        sources = []
                st.session_state["sources"] = sources
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


VERIFY_HINT = (
    "Amazon.ae, Noon aur AliExpress par dekhein ke product listed hai ya nahi, aur reviews ya orders ki "
    "ginti kya hai. TikTok par videos aur views, Meta Ads par kitne ads aur kab se chal rahe hain. "
    "Yeh search ke nateejay hain, seedha product page nahi, isliye pehla sahi match khud chunein."
)


def verify_links(p):
    term = str(p.get("search_keyword") or p.get("name") or "").strip()
    if not term:
        return []
    q = quote_plus(term)
    return [
        ("AMAZON.AE", f"https://www.amazon.ae/s?k={q}"),
        ("NOON", f"https://www.noon.com/uae-en/search/?q={q}"),
        ("ALIEXPRESS", f"https://www.aliexpress.com/wholesale?SearchText={q}"),
        ("TIKTOK", f"https://www.tiktok.com/search?q={q}"),
        ("META ADS", "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=AE"
                     f"&q={q}&search_type=keyword_unordered&media_type=all"),
        ("TALABAT", "https://www.google.com/search?q=" + quote_plus("site:talabat.com " + term)),
        ("TRENDS UAE", f"https://trends.google.com/trends/explore?geo=AE&q={q}"),
        ("IMAGES", f"https://www.google.com/search?tbm=isch&q={q}"),
    ]


def verify_html(p):
    links = verify_links(p)
    if not links:
        return ""
    chips = "".join(
        f'<a class="vlink" href="{html.escape(u, quote=True)}" target="_blank" rel="noopener noreferrer">{lab}</a>'
        for lab, u in links
    )
    return (
        '<div class="verify"><div class="vtitle">VERIFY · LISTING, SALES, ADS</div>'
        f'<div class="vlinks">{chips}</div><div class="vhint">{esc(VERIFY_HINT)}</div></div>'
    )


def fmt_reviews(n):
    try:
        return f"{int(float(str(n).replace(',', ''))):,}"
    except Exception:
        return str(n) if n else ""


def listings_html(p):
    items = p.get("_listings") or []
    err = p.get("_listing_err") or ""
    if not items:
        if err:
            return (
                '<div class="verify"><div class="vtitle">LIVE LISTINGS · GOOGLE SHOPPING UAE</div>'
                f'<div class="vhint">{esc(err)}</div></div>'
            )
        return ""
    rows = []
    for it in items[:6]:
        rate = ""
        if it.get("rating"):
            rate = f'★{esc(it.get("rating"))}'
            if it.get("reviews"):
                rate += f' ({esc(fmt_reviews(it.get("reviews")))})'
        rows.append(
            '<div class="lrow">'
            f'<span class="lstore">{esc(it.get("source") or "Store")}</span>'
            f'<span class="lprice">{esc(it.get("price"))}</span>'
            f'<span class="lrate">{rate}</span>'
            f'<a class="vlink" href="{html.escape(it["link"], quote=True)}" target="_blank" '
            'rel="noopener noreferrer">OPEN</a></div>'
        )
    return (
        '<div class="verify"><div class="vtitle">LIVE LISTINGS · GOOGLE SHOPPING UAE</div>'
        + "".join(rows)
        + '<div class="vhint">Reviews ki ginti demand ka andaza deti hai, asli sales ka number nahi. '
        "Listing ka pehla match khud check karein.</div></div>"
    )


def render_card(p, idx=0):
    score = int(to_num(p.get("score"), 0))
    score = max(0, min(10, score))
    segs = "".join('<i class="on"></i>' if n < score else "<i></i>" for n in range(10))
    img = safe_url(p.get("_image"))
    img_html = (
        f'<img class="pimg" src="{html.escape(img, quote=True)}" alt="{esc(p.get("name"))} ki photo" '
        'loading="lazy" referrerpolicy="no-referrer">'
        if img
        else ""
    )

    def line(label, key):
        return f'<div class="line"><b>{label}:</b> {esc(p.get(key))}</div>' if p.get(key) else ""

    parts = [
        f'<div class="card" style="--d:{idx * 0.12:.2f}s">',
        f'<div class="card-top"><span class="tag">TARGET {idx + 1:02d}</span><span class="tag dim">UAE MARKET</span></div>',
        '<div class="card-head">',
        img_html,
        f'<div class="pname">{esc(p.get("name"))}</div>',
        f'<div class="gauge" style="--p:{score * 10}"><span>{score}</span><small>/10</small></div>',
        "</div>",
        f'<div class="seg">{segs}</div>',
        '<div class="grid">',
        f'<div class="stat"><div class="k">Selling price</div><div class="v">{esc(p.get("sell_price_aed"))} AED</div></div>',
        f'<div class="stat"><div class="k">Supplier cost</div><div class="v">{esc(p.get("supplier_cost_aed"))} AED</div></div>',
        f'<div class="stat"><div class="k">Margin</div><div class="v">{esc(p.get("margin_percent"))}%</div></div>',
        f'<div class="stat"><div class="k">COD risk</div><div class="v {risk_class(p.get("cod_risk"))}">{esc(p.get("cod_risk"))}</div></div>',
        f'<div class="stat"><div class="k">Shipping risk</div><div class="v {risk_class(p.get("shipping_risk"))}">{esc(p.get("shipping_risk"))}</div></div>',
        "</div>",
        line("Kyun trend kar raha hai", "why_trending"),
        line("Kyun chuna", "why_chosen"),
        line("Potential", "potential"),
        line("Kahan bik sakta hai (AI ka andaza, khud verify karein)", "likely_platforms"),
        line("Ad angle", "ad_angle"),
        line("Supplier search keyword", "search_keyword"),
        listings_html(p),
        verify_html(p),
        "</div>",
    ]
    return "".join(parts)


# ---------------------------------------------------------------
# Voice: Jarvis speaks the results (browser text-to-speech, free, no key)
# ---------------------------------------------------------------
def build_speech_text(products):
    def say(v, default="unknown"):
        s = str(v).strip() if v is not None else ""
        return s if s else default

    lines = [f"Sir, scan complete. {len(products)} targets acquired."]
    for i, p in enumerate(products, start=1):
        lines.append(
            f"Target {i}. {say(p.get('name'))}. "
            f"Score {say(p.get('score'))} out of 10. "
            f"Selling price {say(p.get('sell_price_aed'))} dirhams. "
            f"Supplier cost {say(p.get('supplier_cost_aed'))} dirhams. "
            f"Margin {say(p.get('margin_percent'))} percent. "
            f"C O D risk {say(p.get('cod_risk'))}. "
            f"Shipping risk {say(p.get('shipping_risk'))}."
        )
    lines.append("These figures are estimates, sir. Please verify the supplier and shipping before you spend.")
    return " ".join(lines)


SPEAKER_TEMPLATE = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');
body { margin: 0; background: transparent; font-family: sans-serif; }
button {
  font-family: 'Orbitron', sans-serif; letter-spacing: 0.18em; font-weight: 700; font-size: 13px;
  background: rgba(0,35,55,0.6); color: #7fe7ff; border: 2px solid #00d4ff; border-radius: 0;
  padding: 12px 20px; margin-right: 10px; cursor: pointer;
  box-shadow: 0 0 16px rgba(0,212,255,0.45), inset 0 0 12px rgba(0,212,255,0.12);
}
button:hover { background: #00d4ff; color: #02121b; }
button:focus-visible { outline: 3px solid #ffffff; outline-offset: 2px; }
#msg { color: #7fc2d6; font-size: 13px; margin-top: 8px; }
</style>
<button id="go" aria-label="Jarvis ka jawab sunein">&#9654; JARVIS BOLO</button>
<button id="stop" aria-label="Awaaz band karein">&#9632; STOP</button>
<div id="msg"></div>
<script>
const P = __PAYLOAD__;
const AUTOPLAY = __AUTOPLAY__;
const msg = document.getElementById('msg');
function vs() { return window.speechSynthesis.getVoices(); }
function byLang(prefix) {
  return vs().find(function (v) { return v.lang && v.lang.toLowerCase().replace('_', '-').indexOf(prefix) === 0; }) || null;
}
function enVoice() {
  return vs().find(function (x) { return /UK English Male/i.test(x.name); }) || byLang('en-gb') || byLang('en');
}
function say(text, voice, lang) {
  const parts = text.split(/(?<=[.!?\u06d4\u0964])\s+/);
  parts.forEach(function (part, i) {
    if (!part.trim()) { return; }
    const u = new SpeechSynthesisUtterance(part);
    if (voice) { u.voice = voice; u.lang = voice.lang; } else { u.lang = lang; }
    u.rate = 0.95; u.pitch = 0.9;
    if (i === 0) { u.onerror = function () { msg.textContent = 'Awaaz shuru nahi hui. JARVIS BOLO button dabayein.'; }; }
    window.speechSynthesis.speak(u);
  });
}
function go() {
  if (!('speechSynthesis' in window)) { msg.textContent = 'Is browser mein awaaz available nahi.'; return; }
  window.speechSynthesis.cancel();
  if (P.kind === 'roman_urdu') {
    const ur = byLang('ur');
    if (ur && P.ur) { say(P.ur, ur, 'ur-PK'); msg.textContent = 'Voice: ' + ur.name; return; }
    const hi = byLang('hi');
    if (hi && P.hi) { say(P.hi, hi, 'hi-IN'); msg.textContent = 'Voice: ' + hi.name + ' (Hindi awaaz)'; return; }
    say(P.rom || '', enVoice(), 'en-GB');
    msg.textContent = 'Urdu ya Hindi awaaz nahi mili, angrezi awaaz istemal ho rahi hai.';
    return;
  }
  const v = enVoice();
  say(P.text || '', v, 'en-GB');
  msg.textContent = v ? 'Voice: ' + v.name : 'Default awaaz istemal ho rahi hai.';
}
document.getElementById('go').onclick = go;
document.getElementById('stop').onclick = function () { window.speechSynthesis.cancel(); msg.textContent = ''; };
if ('speechSynthesis' in window) {
  window.speechSynthesis.getVoices();
  if (AUTOPLAY) { setTimeout(go, 700); }
}
</script>
"""


def speaker_html(payload, autoplay=False):
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return SPEAKER_TEMPLATE.replace("__PAYLOAD__", data).replace("__AUTOPLAY__", "true" if autoplay else "false")


def voice_player_html(text):
    return speaker_html({"kind": "en", "text": text}, False)


def render_voice(products):
    try:
        import streamlit.components.v1 as components

        components.html(voice_player_html(build_speech_text(products)), height=96)
    except Exception:
        st.caption("Awaaz wala button is Streamlit version mein abhi available nahi.")


# ---------------------------------------------------------------
# Talk to Jarvis (mic ya text, Roman Urdu / English)
# ---------------------------------------------------------------
CHAT_SYSTEM = """You are J.A.R.V.I.S., a calm, polite and slightly witty assistant (like a British butler) for a person who runs a dropshipping / e-commerce business in the UAE.
The user may speak or write in Roman Urdu (Urdu written in English letters) or in English.
Reply in the SAME language the user used. Keep every reply short: 2 to 5 sentences, because it will be read aloud.
Use the scan context below when the user asks about the products. Never invent prices, sales numbers, order counts, review counts or links. If you do not know something, say so and say how the user can check it.
Output ONLY a valid JSON object (no markdown, no extra text) with these keys:
"transcript": what the user said (the exact words if it was audio, otherwise the typed text),
"reply": your answer text,
"lang": "roman_urdu" or "english",
"spoken_ur": the same reply written in Urdu script (only when lang is roman_urdu, otherwise empty string),
"spoken_hi": the same reply written in Hindi Devanagari script (only when lang is roman_urdu, otherwise empty string)."""


def chat_context():
    prods = st.session_state.get("products") or []
    lines = []
    for p in prods[:8]:
        lines.append(
            f"- {p.get('name')}: sell {p.get('sell_price_aed')} AED, supplier cost {p.get('supplier_cost_aed')} AED, "
            f"margin {p.get('margin_percent')}%, COD risk {p.get('cod_risk')}, shipping risk {p.get('shipping_risk')}, "
            f"potential {p.get('potential', '')}"
        )
    recent = (st.session_state.get("chat") or [])[-6:]
    hist = "\n".join(f"{'User' if m.get('role') == 'user' else 'Jarvis'}: {m.get('text', '')}" for m in recent)
    return "Latest scan:\n" + ("\n".join(lines) or "none yet") + "\n\nRecent conversation:\n" + (hist or "none")


def parse_chat_json(text):
    cleaned = (text or "").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(cleaned[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) and str(data.get("reply", "")).strip() else None


def ask_jarvis(user_text=None, audio_bytes=None):
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=45000))
    instruction = CHAT_SYSTEM + "\n\n" + chat_context()
    if audio_bytes:
        parts = [
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            "The user spoke the audio above. Answer as instructed.",
        ]
    else:
        parts = ["User message: " + str(user_text)]
    models = candidate_models(client)[:4]
    started = time.time()
    last_error = None
    for round_no in range(2):
        for model in models:
            if time.time() - started > 90:
                break
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=parts,
                    config=types.GenerateContentConfig(system_instruction=instruction, temperature=0.5),
                )
                data = parse_chat_json(response.text or "")
                if data:
                    st.session_state["model_used"] = model
                    return data
                last_error = RuntimeError("Jawab ka format theek nahi tha")
            except Exception as e:
                last_error = e
                if not is_busy_error(e):
                    raise
        if round_no == 0:
            time.sleep(3)
    raise last_error or RuntimeError("BUSY")


def render_speaker(msg, autoplay=False):
    try:
        import streamlit.components.v1 as components

        if msg.get("lang") == "roman_urdu":
            payload = {"kind": "roman_urdu", "rom": msg.get("text", ""), "ur": msg.get("ur", ""), "hi": msg.get("hi", "")}
        else:
            payload = {"kind": "en", "text": msg.get("text", "")}
        components.html(speaker_html(payload, autoplay), height=96)
    except Exception:
        st.caption("Awaaz wala button is Streamlit version mein abhi available nahi.")


# ---------------------------------------------------------------
# History: permanent storage (Google Sheet), real listings (Serper), Excel / Word export
# ---------------------------------------------------------------
HISTORY_FILE = "jarvis_history.json"
PKT = datetime.timezone(datetime.timedelta(hours=5))  # Pakistan time


def now_pkt():
    return datetime.datetime.now(PKT)


COLUMNS = [
    "Date", "Time", "Category", "Product", "Score", "Sell price (AED)", "Supplier cost (AED)",
    "Margin (%)", "COD risk", "Shipping risk", "Why trending", "Ad angle", "Supplier keyword",
    "Source", "Status", "Notes",
    "Why chosen", "Potential", "Likely platforms",
    "Amazon.ae listing", "Noon listing", "Talabat listing", "Top listings",
    "Image URL", "Image",
    "Amazon.ae search", "Noon search", "AliExpress search", "TikTok search", "Meta Ads search",
    "Talabat search", "Trends UAE", "Images search",
    "Listing data",
]
LINK_COLS = {
    "AMAZON.AE": "Amazon.ae search", "NOON": "Noon search", "ALIEXPRESS": "AliExpress search",
    "TIKTOK": "TikTok search", "META ADS": "Meta Ads search", "TALABAT": "Talabat search",
    "TRENDS UAE": "Trends UAE", "IMAGES": "Images search",
}
URL_COLUMNS = ["Amazon.ae listing", "Noon listing", "Talabat listing", "Image URL"] + list(LINK_COLS.values())
EXPORT_COLUMNS = [c for c in COLUMNS if c != "Image"]
SHOW_COLUMNS = [
    "Date", "Product", "Score", "Potential", "Sell price (AED)", "Supplier cost (AED)", "Margin (%)",
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


def search_link_fields(keyword):
    out = {}
    for label, url in verify_links({"search_keyword": keyword}):
        col = LINK_COLS.get(label)
        if col:
            out[col] = url
    return out


def normalize_row(r):
    d = {}
    for c in COLUMNS:
        val = r.get(c, "")
        d[c] = "" if val is None else val
    d["Date"] = norm_date(d["Date"])
    keyword = d.get("Supplier keyword") or d.get("Product")
    if keyword:
        for col, url in search_link_fields(keyword).items():
            if not d.get(col):
                d[col] = url
    return d


def sheets_configured():
    if not st.session_state.get("is_admin"):
        return False
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
    first = [str(x).strip() for x in ws.row_values(1)]
    if first != COLUMNS:
        if first != COLUMNS[: len(first)]:
            raise ValueError("Sheet ki pehli row (header) Jarvis ke format se match nahi karti")
        if ws.col_count < len(COLUMNS):
            ws.add_cols(len(COLUMNS) - ws.col_count)
        ws.update(range_name="A1", values=[COLUMNS])
    return ws


def col_letter(n):
    s = ""
    while n:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def load_history_file():
    if not st.session_state.get("is_admin"):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [normalize_row(r) for r in data] if isinstance(data, list) else []
    except Exception:
        return []


def save_history_file(rows):
    if not st.session_state.get("is_admin"):
        return
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


# ---------- Real listings (Google Shopping UAE via Serper, free credits) ----------
def serper_key():
    if not st.session_state.get("is_admin"):
        return str(st.session_state.get("user_serper_key") or "").strip()
    try:
        return str(st.secrets.get("SERPER_API_KEY") or "").strip()
    except Exception:
        return ""


def safe_url(u):
    u = str(u or "").strip()
    return u if u.lower().startswith(("http://", "https://")) else ""


def fetch_listings(term, key):
    import requests

    try:
        r = requests.post(
            "https://google.serper.dev/shopping",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": term, "gl": "ae", "hl": "en", "num": 10},
            timeout=20,
        )
    except Exception as e:
        return [], "Listings nahi mile (connection): " + str(e)[:80]
    if r.status_code in (401, 403):
        return [], "Serper ne key qabool nahi ki. SERPER_API_KEY check karein."
    if r.status_code in (402, 429):
        return [], "Serper ke free credits khatam ya limit lag gayi."
    if r.status_code != 200:
        return [], f"Serper error {r.status_code}."
    try:
        items = r.json().get("shopping") or []
    except Exception:
        return [], "Serper ka jawab samajh nahi aaya."
    out = []
    for it in items:
        link = safe_url(it.get("link"))
        if not link:
            continue
        out.append({
            "title": str(it.get("title", "")),
            "source": str(it.get("source", "")),
            "price": str(it.get("price", "")),
            "rating": it.get("rating", ""),
            "reviews": it.get("ratingCount") or it.get("reviews") or "",
            "link": link,
            "image": safe_url(it.get("imageUrl") or it.get("thumbnail")),
        })
    out = out[:10]
    return out, ("" if out else "Is keyword par koi listing nahi mili.")


def enrich_products(products):
    key = serper_key()
    if not key:
        return
    from concurrent.futures import ThreadPoolExecutor

    terms = [str(p.get("search_keyword") or p.get("name") or "").strip() for p in products]
    try:
        with ThreadPoolExecutor(max_workers=5) as ex:
            results = list(ex.map(lambda t: fetch_listings(t, key) if t else ([], ""), terms))
    except Exception as e:
        results = [([], "Listings nahi mile: " + str(e)[:80])] * len(products)
    for p, (items, err) in zip(products, results):
        p["_listings"] = items
        p["_listing_err"] = err
        p["_image"] = next((i["image"] for i in items if i.get("image")), "")


def listing_site(item):
    host = re.sub(r"^https?://", "", str(item.get("link", ""))).split("/")[0]
    text = (str(item.get("source", "")) + " " + host).lower()
    if "amazon" in text:
        return "amazon"
    if "noon" in text:
        return "noon"
    if "talabat" in text:
        return "talabat"
    return "other"


def listing_line(it):
    bits = [str(it.get("source", "")) or "Store", str(it.get("price", ""))]
    if it.get("rating"):
        rate = "rating " + str(it["rating"])
        if it.get("reviews"):
            rate += f" ({it['reviews']} reviews)"
        bits.append(rate)
    bits.append(str(it.get("link", "")))
    return " | ".join(b for b in bits if b)


def split_listings(items):
    found = {"amazon": "", "noon": "", "talabat": ""}
    for it in items:
        site = listing_site(it)
        if site in found and not found[site]:
            found[site] = it.get("link", "")
    found["top"] = "\n".join(listing_line(it) for it in items[:6])
    return found


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
        items = p.get("_listings") or []
        split = split_listings(items)
        row = {
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
            "Why chosen": str(p.get("why_chosen", "")),
            "Potential": str(p.get("potential", "")),
            "Likely platforms": str(p.get("likely_platforms", "")),
            "Amazon.ae listing": split["amazon"],
            "Noon listing": split["noon"],
            "Talabat listing": split["talabat"],
            "Top listings": split["top"],
            "Image URL": str(p.get("_image", "")),
            "Image": "",
            "Listing data": "Google Shopping UAE (Serper)" if items else "Search links only",
        }
        row.update(search_link_fields(p.get("search_keyword") or p.get("name")))
        rows.append(row)
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
            res = ws.append_rows([[r.get(c, "") for c in COLUMNS] for r in fresh], value_input_option="RAW")
            st.session_state["sheet_error"] = None
            try:
                m = re.search(r"!\$?[A-Z]+\$?(\d+):\$?[A-Z]+\$?(\d+)", str(res["updates"]["updatedRange"]))
                if m:
                    first_row = int(m.group(1))
                    col = col_letter(COLUMNS.index("Image") + 1)
                    for k, r in enumerate(fresh):
                        url = str(r.get("Image URL", "")).replace('"', "%22")
                        if url.startswith("http"):
                            ws.update(
                                range_name=f"{col}{first_row + k}",
                                values=[[f'=IMAGE("{url}")']],
                                value_input_option="USER_ENTERED",
                            )
                    try:
                        img_col = COLUMNS.index("Image")
                        ws.spreadsheet.batch_update({"requests": [
                            {"updateDimensionProperties": {
                                "range": {"sheetId": ws.id, "dimension": "ROWS",
                                          "startIndex": first_row - 1, "endIndex": first_row - 1 + len(fresh)},
                                "properties": {"pixelSize": 90}, "fields": "pixelSize"}},
                            {"updateDimensionProperties": {
                                "range": {"sheetId": ws.id, "dimension": "COLUMNS",
                                          "startIndex": img_col, "endIndex": img_col + 1},
                                "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
                        ]})
                    except Exception:
                        pass
            except Exception:
                pass
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
    ws.append(EXPORT_COLUMNS)
    for r in rows:
        ws.append([r.get(c, "") for c in EXPORT_COLUMNS])
        row_no = ws.max_row
        for j, c in enumerate(EXPORT_COLUMNS, start=1):
            v = str(r.get(c, ""))
            if c in URL_COLUMNS and v.startswith("http"):
                cell = ws.cell(row=row_no, column=j)
                cell.hyperlink = v
                cell.font = Font(color="0563C1", underline="single")
    head_fill = PatternFill("solid", fgColor="0B3A55")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head_fill
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    widths = {
        "Date": 12, "Time": 8, "Category": 18, "Product": 34, "Score": 8, "Sell price (AED)": 14,
        "Supplier cost (AED)": 16, "Margin (%)": 11, "COD risk": 11, "Shipping risk": 13,
        "Why trending": 50, "Ad angle": 50, "Supplier keyword": 28, "Source": 14, "Status": 14, "Notes": 30,
        "Why chosen": 50, "Potential": 24, "Likely platforms": 30, "Top listings": 60, "Listing data": 24,
    }
    for i, c in enumerate(EXPORT_COLUMNS, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = widths.get(c, 18)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            header = ws.cell(row=1, column=cell.column).value
            cell.alignment = Alignment(wrap_text=header not in URL_COLUMNS, vertical="top")
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
                ("Potential", "Potential"),
                ("Supplier keyword", "Supplier keyword"),
                ("Status", "Status"),
            ]:
                cells = table.add_row().cells
                cells[0].text = label
                cells[1].text = str(r.get(key, ""))
            for label, key in [
                ("Why trending", "Why trending"), ("Why chosen", "Why chosen"),
                ("Likely platforms", "Likely platforms"), ("Ad angle", "Ad angle"),
                ("Amazon.ae listing", "Amazon.ae listing"), ("Noon listing", "Noon listing"),
                ("Talabat listing", "Talabat listing"), ("Image", "Image URL"),
            ]:
                if r.get(key):
                    doc.add_paragraph(f"{label}: {r.get(key)}")
            if r.get("Top listings"):
                doc.add_paragraph("Top listings:\n" + str(r.get("Top listings")))
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
if run and not api_key:
    st.session_state["error"] = "NOKEY"
elif run:
    with st.spinner("JARVIS UAE market scan kar raha hai..."):
        try:
            raw = run_jarvis(category, extra, pasted, use_search)
            products = parse_products(raw)
            if products:
                enrich_products(products)
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
    elif error == "NOKEY":
        msg = (
            "Pehle upar apni Gemini API key daalein (aistudio.google.com se free key milti hai), "
            "phir RUN JARVIS dabayein."
        )
    elif "API key not valid" in error or "API_KEY_INVALID" in error:
        msg = "Gemini ne key qabool nahi ki. Key dobara copy karke paste karein, ya nayi key banayein."
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
    st.markdown('<div class="sec"><b>//</b> TARGETS ACQUIRED</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="status-line">Scan mukammal. {len(products)} products mile. '
        f'Waqt: {esc(st.session_state.get("time"))}. Model: {esc(st.session_state.get("model_used"))}</div>',
        unsafe_allow_html=True,
    )
    if not serper_key():
        st.markdown(
            '<div class="status-line">Asli listings, qeemat, reviews aur product photo abhi nahi aa rahe, kyun ke '
            "SERPER_API_KEY lagi nahi hai. Neeche wale search links phir bhi kaam karte hain.</div>",
            unsafe_allow_html=True,
        )
    render_voice(products)
    cols = st.columns(2)
    for i, p in enumerate(products):
        with cols[i % 2]:
            st.markdown(render_card(p, i), unsafe_allow_html=True)
    sources = st.session_state.get("sources") or []
    if sources:
        with st.expander("Sources (Google Search se mile asli links)"):
            for title, uri in sources[:15]:
                safe = str(title).replace("[", "(").replace("]", ")")
                st.markdown(f"- [{safe}]({uri})")
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
# Talk to Jarvis section
# ---------------------------------------------------------------
st.markdown('<div class="sec"><b>//</b> TALK TO JARVIS</div>', unsafe_allow_html=True)
st.caption(
    "Mic dabake Roman Urdu ya English mein bolein, ya neeche likhein. Yeh live streaming nahi hai: har baar "
    "bolne ke baad Jarvis kuch second mein jawab deta hai. Aap ki awaaz aur text jawab ke liye Google Gemini "
    "ko bheje jate hain."
)
chat = st.session_state.setdefault("chat", [])
audio = st.audio_input("Mic se bolein") if hasattr(st, "audio_input") else None
with st.form("chat_form", clear_on_submit=True):
    typed = st.text_input("Ya yahan likhein")
    sent = st.form_submit_button("SEND")

new_turn = None
if audio is not None:
    _bytes = audio.getvalue()
    _h = hashlib.md5(_bytes).hexdigest()
    if _h != st.session_state.get("last_audio_hash"):
        st.session_state["last_audio_hash"] = _h
        if len(_bytes) > 3_000_000:
            st.markdown(
                '<div class="status-line">Awaaz bohat lambi hai. Chhoti baat (1 minute se kam) record karein.</div>',
                unsafe_allow_html=True,
            )
        else:
            new_turn = ("audio", _bytes)
if sent and typed.strip():
    new_turn = ("text", typed.strip())

if new_turn:
    if not api_key:
        st.markdown(
            '<div class="status-line">Pehle upar apni Gemini API key daalein, phir Jarvis se baat karein.</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.spinner("Jarvis soch raha hai..."):
            try:
                if new_turn[0] == "audio":
                    data = ask_jarvis(audio_bytes=new_turn[1])
                else:
                    data = ask_jarvis(user_text=new_turn[1])
                _said = str(data.get("transcript") or "").strip()
                if not _said:
                    _said = new_turn[1] if new_turn[0] == "text" else "(awaaz)"
                chat.append({"role": "user", "text": _said})
                chat.append({
                    "role": "jarvis",
                    "text": str(data.get("reply", "")),
                    "lang": "roman_urdu" if data.get("lang") == "roman_urdu" else "english",
                    "ur": str(data.get("spoken_ur", "")),
                    "hi": str(data.get("spoken_hi", "")),
                })
                st.session_state["speak_now"] = True
            except Exception as e:
                _t = str(e)
                if "API key not valid" in _t or "API_KEY_INVALID" in _t:
                    _m = "Gemini ne key qabool nahi ki. Key dobara paste karein."
                elif _t == "BUSY" or is_busy_error(e):
                    _m = "Google ke servers abhi busy hain. Thori der baad dobara bolein."
                else:
                    _m = "Jarvis jawab nahi de saka. Detail: " + _t[:200]
                st.markdown('<div class="status-line">' + esc(_m) + "</div>", unsafe_allow_html=True)

for _msg in chat[-8:]:
    _who = "AAP" if _msg["role"] == "user" else "JARVIS"
    _cls = "user" if _msg["role"] == "user" else "jarvis"
    st.markdown(
        f'<div class="bubble {_cls}"><span class="who">{_who}</span>{esc(_msg.get("text", ""))}</div>',
        unsafe_allow_html=True,
    )
if chat and chat[-1]["role"] == "jarvis":
    render_speaker(chat[-1], autoplay=bool(st.session_state.pop("speak_now", False)))


# ---------------------------------------------------------------
# History section (date range + table + Excel / Word download)
# ---------------------------------------------------------------
st.markdown(
    '<div class="sec"><b>//</b> ARCHIVE · HISTORY</div>',
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
    if IS_ADMIN:
        st.caption(
            "Storage: temporary. Google Sheet abhi connect nahi hui, is liye app restart par history mit sakti hai. "
            "Excel download karke rakh lein."
        )
    else:
        st.caption(
            "Aap ka data sirf is session mein rehta hai, owner ki Google Sheet ya kisi shared file mein save nahi hota. "
            "Page refresh ya logout par mit jata hai, is liye Excel download karke rakhein, aur dobara upload karke "
            "history wapas laayein."
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

# ---------------------------------------------------------------
# Top status chips (real values only)
# ---------------------------------------------------------------
_stamp = now_pkt()
_engine = str(st.session_state.get("model_used") or "STANDBY").upper()
if not IS_ADMIN:
    _archive = "SESSION ONLY"
elif sheets_configured() and not st.session_state.get("sheet_error"):
    _archive = "GOOGLE SHEET"
else:
    _archive = "TEMPORARY"
telemetry.markdown(
    '<div class="telemetry">'
    '<span class="chip"><i class="dot"></i>SYSTEM ONLINE</span>'
    '<span class="chip">REGION · UAE</span>'
    f'<span class="chip">{_stamp.strftime("%d %b %Y · %H:%M")} PKT</span>'
    f'<span class="chip">ENGINE · {esc(_engine)}</span>'
    f'<span class="chip">USER · {esc(USER_NAME or USER_EMAIL)}</span>'
    f'<span class="chip">ARCHIVE · {_archive}</span>'
    f'<span class="chip">RECORDS · {len(st.session_state.get("history", []))}</span>'
    "</div>",
    unsafe_allow_html=True,
)
