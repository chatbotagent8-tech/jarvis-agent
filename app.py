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

div.stButton > button {
    font-family: 'Orbitron', sans-serif; letter-spacing: 0.18em;
    background: transparent; color: #7fe7ff; border: 2px solid #00d4ff; border-radius: 0;
    padding: 0.7rem 1.4rem; box-shadow: 0 0 18px rgba(0,212,255,0.45);
    transition: all 0.2s ease;
}
div.stButton > button:hover { background: #00d4ff; color: #02121b; box-shadow: 0 0 30px rgba(0,212,255,0.9); }
div.stButton > button:focus-visible { outline: 3px solid #ffffff; outline-offset: 2px; }

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
    client = genai.Client(api_key=api_key)
    search_on = bool(use_search) and not (pasted and pasted.strip())
    config_kwargs = {"temperature": 0.6}
    if search_on:
        config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    prompt = build_prompt(category, extra, pasted, search_on)

    last_error = None
    for model in candidate_models(client):
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                st.session_state["model_used"] = model
                return response.text or ""
            except Exception as e:
                last_error = e
                if not is_busy_error(e):
                    raise
                time.sleep(3 if attempt == 0 else 0)
    raise last_error


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
# Run + show
# ---------------------------------------------------------------
if run:
    with st.spinner("JARVIS UAE market scan kar raha hai..."):
        try:
            raw = run_jarvis(category, extra, pasted, use_search)
            products = parse_products(raw)
            st.session_state["raw"] = raw
            st.session_state["products"] = products
            st.session_state["time"] = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
            st.session_state["error"] = None
        except Exception as e:
            st.session_state["error"] = str(e)

error = st.session_state.get("error")
if error:
    st.markdown(
        '<div class="status-line">Scan nahi ho saka. Agar yeh quota/limit ka masla hai to thori der baad '
        "dobara try karein. Detail: " + esc(error[:300]) + "</div>",
        unsafe_allow_html=True,
    )

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
