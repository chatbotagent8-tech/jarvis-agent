import csv
import hashlib
import hmac
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
    page_title="J.A.R.V.I.S. | AI Dropshipping Agent",
    page_icon="🔵",
    layout="wide",
)

MODEL_NAME = "gemini-3.8-flash"

# ---------------------------------------------------------------
# Jarvis OS styling
# ---------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');

:root {
    --rgb: 0,229,255; --lt: #aef4ff;
    --ac: rgb(var(--rgb)); --line: rgba(var(--rgb),0.36); --line2: rgba(var(--rgb),0.18);
    --txt: #d3e4ea; --mut: #86a0ac; --ok: #5dffb0; --warn: #ffb454; --bad: #ff6b6b;
    --panel: rgba(11,18,25,0.9);
}

.stApp {
    background:
        radial-gradient(ellipse at 50% -10%, rgba(var(--rgb),0.14) 0%, rgba(8,12,16,0) 55%),
        repeating-linear-gradient(0deg, rgba(var(--rgb),0.045) 0 1px, transparent 1px 44px),
        repeating-linear-gradient(90deg, rgba(var(--rgb),0.045) 0 1px, transparent 1px 44px),
        #070b0f;
    color: var(--txt);
    font-family: 'Chakra Petch', 'Rajdhani', sans-serif;
}
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background: repeating-linear-gradient(0deg, rgba(0,0,0,0) 0 2px, rgba(var(--rgb),0.025) 2px 3px);
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1280px; padding-top: 1.2rem; }

.scanband {
    position: fixed; left: 0; right: 0; top: -20%; height: 18%; pointer-events: none; z-index: 0;
    background: linear-gradient(180deg, transparent, rgba(var(--rgb),0.05), transparent);
    animation: scanband 10s linear infinite;
}
@keyframes scanband { to { top: 110%; } }
.corner {
    position: fixed; width: 34px; height: 34px; border: 2px solid var(--ac); opacity: 0.7;
    pointer-events: none; z-index: 50; filter: drop-shadow(0 0 6px var(--ac));
}
.c-tl { top: 10px; left: 10px; border-right: 0; border-bottom: 0; }
.c-tr { top: 10px; right: 10px; border-left: 0; border-bottom: 0; }
.c-bl { bottom: 10px; left: 10px; border-right: 0; border-top: 0; }
.c-br { bottom: 10px; right: 10px; border-left: 0; border-top: 0; }

/* ---------- Top bar ---------- */
.topbar {
    display: flex; justify-content: space-between; align-items: flex-end; gap: 16px;
    padding: 4px 6px 12px 6px; margin-bottom: 8px; border-bottom: 1px solid var(--line2);
    position: relative; z-index: 2;
}
.b1 { font-weight: 700; letter-spacing: 0.34em; font-size: 1.2rem; color: var(--lt); text-shadow: 0 0 14px rgba(var(--rgb),0.6); }
.b2 { font-family: 'Share Tech Mono', monospace; font-size: 0.75rem; letter-spacing: 0.2em; color: var(--mut); margin-top: 2px; }
.clock { text-align: right; }
.clock .c1 { font-family: 'Share Tech Mono', monospace; font-size: 1.5rem; color: #ffffff; line-height: 1.1; }
.clock .c2 { font-family: 'Share Tech Mono', monospace; font-size: 0.72rem; letter-spacing: 0.16em; color: var(--mut); }

/* ---------- Tabs (navigation) ---------- */
div[data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line2); }
button[data-baseweb="tab"] {
    font-family: 'Share Tech Mono', monospace; letter-spacing: 0.2em; color: var(--mut);
    background: transparent; padding: 10px 18px;
}
button[data-baseweb="tab"] p { color: inherit; font-family: inherit; letter-spacing: inherit; font-size: 0.85rem; margin: 0; }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--lt); background: rgba(var(--rgb),0.1); }
div[data-baseweb="tab-highlight"] { background-color: var(--ac) !important; height: 2px; }
div[data-baseweb="tab-border"] { background-color: transparent !important; }

/* ---------- Palette switch ---------- */
div[data-testid="stRadio"] div[role="radiogroup"] { gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
div[data-testid="stRadio"] label {
    border: 1px solid var(--line2); padding: 3px 10px; background: rgba(11,18,25,0.7); margin: 0; cursor: pointer;
}
div[data-testid="stRadio"] label > div:first-child { display: none; }
div[data-testid="stRadio"] label p {
    font-family: 'Share Tech Mono', monospace; font-size: 0.72rem; letter-spacing: 0.14em; color: var(--lt); margin: 0;
}
div[data-testid="stRadio"] label:has(input:checked) { background: var(--ac); }
div[data-testid="stRadio"] label:has(input:checked) p { color: #02121b; }

/* ---------- Section headings, status lines ---------- */
.sec {
    font-family: 'Share Tech Mono', monospace; letter-spacing: 0.26em; font-size: 0.85rem; color: var(--lt);
    margin: 22px 0 12px 0; display: flex; align-items: center; gap: 12px; position: relative; z-index: 2;
}
.sec b { color: var(--ac); }
.sec::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, var(--line), transparent); }
.status-line {
    border: 1px solid var(--line); border-left: 4px solid var(--ac);
    background: rgba(11,24,32,0.75); padding: 10px 16px; margin: 10px 0 16px 0;
    color: #cfe9f0; font-size: 1.02rem; position: relative; z-index: 2;
}

/* ---------- OS panels (overview) ---------- */
.panel {
    position: relative; z-index: 2; margin-bottom: 16px; background: var(--line);
    padding: 1px;
    clip-path: polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px));
}
.pin {
    background: var(--panel);
    clip-path: polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px));
}
.ph {
    display: flex; align-items: center; gap: 10px; padding: 9px 14px;
    border-bottom: 1px solid var(--line2); background: rgba(var(--rgb),0.05);
}
.pid { font-family: 'Share Tech Mono', monospace; font-size: 0.75rem; letter-spacing: 0.12em; color: var(--ac); }
.pt { font-family: 'Share Tech Mono', monospace; font-size: 0.78rem; letter-spacing: 0.16em; color: var(--lt); flex: 1; }
.pchip {
    font-family: 'Share Tech Mono', monospace; font-size: 0.68rem; letter-spacing: 0.14em; padding: 1px 7px;
    border: 1px solid var(--ac); color: var(--lt);
}
.pchip.ok { border-color: var(--ok); color: var(--ok); }
.pchip.warn { border-color: var(--warn); color: var(--warn); }
.pchip.bad { border-color: var(--bad); color: var(--bad); }
.pb { padding: 12px 14px 14px 14px; }
.kv { display: flex; justify-content: space-between; gap: 12px; padding: 5px 0; border-bottom: 1px dashed rgba(var(--rgb),0.12); }
.kv:last-child { border-bottom: 0; }
.kv .k { font-family: 'Share Tech Mono', monospace; font-size: 0.78rem; letter-spacing: 0.1em; color: var(--mut); }
.kv .v { font-family: 'Share Tech Mono', monospace; font-size: 0.9rem; color: #ffffff; text-align: right; }
.v.ok, .lt.ok { color: var(--ok); } .v.warn, .lt.warn { color: var(--warn); } .v.bad, .lt.bad { color: var(--bad); }
.trow { display: grid; grid-template-columns: 1fr auto; gap: 4px 10px; padding: 5px 0; }
.tn { font-size: 0.95rem; color: #e6f3f8; }
.ts { font-family: 'Share Tech Mono', monospace; color: var(--lt); }
.tb { grid-column: 1 / 3; height: 4px; background: rgba(var(--rgb),0.14); }
.tb i { display: block; height: 100%; background: var(--ac); box-shadow: 0 0 8px rgba(var(--rgb),0.8); }
.rk { display: grid; grid-template-columns: 56px 1fr 70px; align-items: center; gap: 10px; padding: 6px 0; }
.rbar { display: flex; height: 8px; background: rgba(var(--rgb),0.12); }
.rbar i { display: block; }
.rbar i.lo { background: var(--ok); } .rbar i.md { background: var(--warn); } .rbar i.hi { background: var(--bad); }
.rv { font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; color: var(--lt); text-align: right; }
.logrow { display: grid; grid-template-columns: 62px 1fr; gap: 10px; padding: 6px 0; border-bottom: 1px dashed rgba(var(--rgb),0.12); }
.logrow:last-child { border-bottom: 0; }
.lt { font-family: 'Share Tech Mono', monospace; font-size: 0.74rem; letter-spacing: 0.1em; color: var(--ac); }
.lm { font-size: 0.95rem; color: #d3e4ea; line-height: 1.3; }
.dnote { color: var(--mut); font-size: 0.92rem; }

/* ---------- Center ring ---------- */
.center-hud { display: flex; flex-direction: column; align-items: center; position: relative; z-index: 2; padding-top: 6px; }
.greet { font-size: 2rem; font-weight: 600; color: #ffffff; margin-top: 14px; text-align: center; }
.greet em { font-style: normal; color: var(--ac); }
.gsub { color: var(--mut); text-align: center; margin: 4px 0 8px 0; font-size: 1.02rem; }
.ringwrap { position: relative; width: 300px; height: 300px; }
.rg { position: absolute; border-radius: 50%; }
.rg-ticks {
    inset: 0;
    background: repeating-conic-gradient(rgba(var(--rgb),0.8) 0 0.7deg, transparent 0.7deg 6deg);
    -webkit-mask: radial-gradient(circle closest-side, transparent 0 141px, #000 142px 148px, transparent 149px);
            mask: radial-gradient(circle closest-side, transparent 0 141px, #000 142px 148px, transparent 149px);
    animation: spin 90s linear infinite reverse;
}
.rg-seg {
    inset: 0;
    background: repeating-conic-gradient(from 6deg, rgba(var(--rgb),0.34) 0 31deg, transparent 31deg 40deg);
    -webkit-mask: radial-gradient(circle closest-side, transparent 0 108px, #000 109px 136px, transparent 137px);
            mask: radial-gradient(circle closest-side, transparent 0 108px, #000 109px 136px, transparent 137px);
    animation: spin 70s linear infinite;
}
.rg-hi {
    inset: 0;
    background: conic-gradient(transparent 0 16deg, rgba(var(--rgb),1) 16deg 46deg, transparent 46deg 196deg,
                rgba(var(--rgb),1) 196deg 226deg, transparent 226deg 360deg);
    -webkit-mask: radial-gradient(circle closest-side, transparent 0 108px, #000 109px 136px, transparent 137px);
            mask: radial-gradient(circle closest-side, transparent 0 108px, #000 109px 136px, transparent 137px);
    filter: drop-shadow(0 0 8px rgba(var(--rgb),0.7));
    animation: spin 40s linear infinite reverse;
}
.rg-dash { inset: 50px; border: 3px dashed rgba(var(--rgb),0.85); animation: spin 22s linear infinite reverse; }
.rg-thin { inset: 64px; border: 1px solid rgba(var(--rgb),0.5); }
.rg-core {
    inset: 80px; display: flex; flex-direction: column; align-items: center; justify-content: center;
    background: radial-gradient(circle, #0b1218 55%, #050a0e 100%);
    border: 1px solid var(--line); box-shadow: 0 0 40px rgba(var(--rgb),0.35), inset 0 0 26px rgba(var(--rgb),0.18);
}
.rg-core .cl { font-family: 'Share Tech Mono', monospace; font-size: 0.62rem; letter-spacing: 0.18em; color: var(--mut); }
.rg-core .cn { font-family: 'Share Tech Mono', monospace; font-size: 3.1rem; color: #ffffff; line-height: 1.05; }
.rg-core .cs { font-family: 'Share Tech Mono', monospace; font-size: 0.66rem; letter-spacing: 0.14em; color: var(--lt); }
@keyframes spin { to { transform: rotate(360deg); } }

/* ---------- Product cards ---------- */
.card {
    position: relative; z-index: 2; border: 1px solid var(--line);
    background: linear-gradient(160deg, rgba(var(--rgb),0.10), rgba(8,14,20,0.92));
    padding: 16px 20px 18px 20px; margin-bottom: 18px;
    box-shadow: 0 0 22px rgba(var(--rgb),0.10), inset 0 0 24px rgba(var(--rgb),0.04);
    clip-path: polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 20px 100%, 0 calc(100% - 20px));
    animation: rise 0.55s ease both; animation-delay: var(--d, 0s);
}
.card::before { content: ""; position: absolute; top: 0; left: 0; right: 20px; height: 2px; background: linear-gradient(90deg, var(--ac), transparent); }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
.card-top { display: flex; justify-content: space-between; margin-bottom: 8px; }
.tag { font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; letter-spacing: 0.18em; color: var(--ac); }
.tag.dim { color: var(--mut); }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 14px; }
.pname { font-size: 1.1rem; font-weight: 600; color: #e6f7fc; letter-spacing: 0.03em; line-height: 1.35; flex: 1; }
.pimg { width: 84px; height: 84px; object-fit: contain; background: #ffffff; padding: 3px; border: 1px solid var(--line); flex: 0 0 auto; }
.gauge {
    position: relative; width: 66px; height: 66px; border-radius: 50%; flex: 0 0 auto; display: grid; place-items: center;
    background: conic-gradient(var(--ac) calc(var(--p) * 1%), rgba(var(--rgb),0.15) 0);
    box-shadow: 0 0 18px rgba(var(--rgb),0.45);
}
.gauge::before { content: ""; position: absolute; inset: 6px; border-radius: 50%; background: #071017; }
.gauge span { position: relative; font-family: 'Share Tech Mono', monospace; font-weight: 700; font-size: 1.4rem; color: #ffffff; line-height: 1; margin-top: -7px; }
.gauge small { position: absolute; bottom: 11px; font-size: 0.62rem; color: var(--mut); letter-spacing: 0.05em; }
.seg { display: flex; gap: 4px; margin: 12px 0 14px 0; }
.seg i { flex: 1; height: 8px; background: rgba(var(--rgb),0.14); }
.seg i.on { background: var(--ac); box-shadow: 0 0 10px rgba(var(--rgb),0.8); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 12px; }
.stat { border: 1px solid var(--line2); padding: 8px 10px; background: rgba(8,16,22,0.7); }
.stat .k { color: var(--mut); font-size: 0.85rem; letter-spacing: 0.04em; }
.stat .v { color: #ffffff; font-family: 'Share Tech Mono', monospace; font-size: 1.25rem; }
.line { margin: 6px 0; color: #c8dde5; font-size: 1.02rem; line-height: 1.4; }
.line b { color: var(--lt); font-weight: 700; letter-spacing: 0.03em; }
.risk-low { color: var(--ok); } .risk-med { color: var(--warn); } .risk-high { color: var(--bad); }

.verify { margin-top: 12px; padding-top: 10px; border-top: 1px dashed rgba(var(--rgb),0.3); }
.vtitle { font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; letter-spacing: 0.16em; color: var(--ac); }
.vlinks { margin-top: 4px; }
.vlink {
    display: inline-block; margin: 6px 8px 0 0; padding: 7px 12px;
    font-family: 'Share Tech Mono', monospace; font-size: 0.82rem; letter-spacing: 0.08em;
    color: var(--lt) !important; text-decoration: none !important;
    border: 1px solid var(--line); background: rgba(11,24,32,0.7); transition: all 0.15s ease;
}
.vlink:hover { background: var(--ac); color: #02121b !important; box-shadow: 0 0 14px rgba(var(--rgb),0.8); }
.vlink:focus-visible { outline: 2px solid #ffffff; outline-offset: 2px; }
.vhint { margin-top: 8px; color: var(--mut); font-size: 0.92rem; line-height: 1.35; }
.lrow { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; margin-top: 8px; }
.lstore { font-weight: 700; color: var(--lt); min-width: 90px; }
.lprice { font-family: 'Share Tech Mono', monospace; color: #ffffff; }
.lrate { color: var(--mut); font-size: 0.95rem; }
.lrow .vlink { margin: 0; padding: 4px 10px; }

.bubble { position: relative; z-index: 2; margin: 8px 0; padding: 10px 14px; max-width: 86%; border: 1px solid var(--line); line-height: 1.4; font-size: 1.05rem; }
.bubble.user { margin-left: auto; background: rgba(var(--rgb),0.12); border-right: 3px solid var(--ac); }
.bubble.jarvis { background: rgba(11,24,32,0.8); border-left: 3px solid var(--ac); }
.bubble .who { display: block; margin-bottom: 2px; font-family: 'Share Tech Mono', monospace; font-size: 0.75rem; letter-spacing: 0.18em; color: var(--ac); }

/* ---------- Controls ---------- */
div.stButton > button, div.stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
    font-family: 'Share Tech Mono', monospace; letter-spacing: 0.2em; font-weight: 700;
    background: rgba(11,24,32,0.7); color: var(--lt); border: 2px solid var(--ac); border-radius: 0;
    padding: 0.7rem 1.5rem; box-shadow: 0 0 18px rgba(var(--rgb),0.4), inset 0 0 14px rgba(var(--rgb),0.1);
    transition: all 0.2s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--ac); color: #02121b; box-shadow: 0 0 32px rgba(var(--rgb),0.9);
}
div.stButton > button:active, div.stDownloadButton > button:active { transform: scale(0.98); }
div.stButton > button:focus-visible, div.stDownloadButton > button:focus-visible { outline: 3px solid #ffffff; outline-offset: 2px; }
div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea, .stDateInput input {
    background: rgba(8,16,22,0.8) !important; color: #e6f3f8 !important;
    border: 1px solid var(--line) !important; border-radius: 0 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus { box-shadow: 0 0 14px rgba(var(--rgb),0.5) !important; }
div[data-testid="stExpander"] { border: 1px solid var(--line) !important; background: rgba(8,16,22,0.6); border-radius: 0 !important; }
div[data-testid="stCaptionContainer"] { color: var(--mut); }
label, .stSelectbox label, .stTextInput label { color: var(--lt) !important; }

@media (max-width: 640px) {
    .b1 { font-size: 1rem; letter-spacing: 0.22em; }
    .clock .c1 { font-size: 1.2rem; }
    .corner { display: none; }
    .greet { font-size: 1.5rem; }
    .pname { font-size: 1rem; }
}
@media (prefers-reduced-motion: reduce) {
    .rg, .scanband, .card { animation: none; }
}
</style>
"""

PALETTES = {
    "CYAN": ("0,229,255", "#aef4ff"),
    "BLUE": ("74,168,255", "#b3d9ff"),
    "EMBER": ("255,170,100", "#ffd2ae"),
    "ICE": ("214,228,240", "#ffffff"),
}
_pal = st.session_state.get("palette", "CYAN")
if _pal not in PALETTES:
    _pal = "CYAN"
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    f"<style>:root {{ --rgb: {PALETTES[_pal][0]}; --lt: {PALETTES[_pal][1]}; }}</style>",
    unsafe_allow_html=True,
)

PKT = datetime.timezone(datetime.timedelta(hours=5))  # Pakistan time


def now_pkt():
    return datetime.datetime.now(PKT)


_t = now_pkt()
st.markdown(
    '<div class="scanband"></div>'
    '<div class="corner c-tl"></div><div class="corner c-tr"></div>'
    '<div class="corner c-bl"></div><div class="corner c-br"></div>'
    '<div class="topbar"><div class="brand"><div class="b1">JARVIS OS</div>'
    '<div class="b2">AI AGENT FOR DROPSHIPPING</div></div>'
    f'<div class="clock"><div class="c1">{_t.strftime("%H:%M")}</div>'
    f'<div class="c2">{_t.strftime("%a %d %b %Y").upper()} · PKT</div></div></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Login: Google (Gmail) ya owner password. Login ke baghair app band rehti hai.
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


def _app_password():
    try:
        return str(st.secrets.get("APP_PASSWORD") or "")
    except Exception:
        return ""


_user = getattr(st, "user", None)
_google_ready = _user is not None and _auth_ready()
_pw_secret = _app_password()
_via_google = _google_ready and bool(getattr(_user, "is_logged_in", False))
_pw_ok = bool(st.session_state.get("pw_ok"))

if not _google_ready and not _pw_secret:
    st.markdown(
        '<div class="status-line">Login abhi set nahi hua, is liye app band hai. '
        "Owner Secrets mein APP_PASSWORD (ya [auth] wali settings) lagayein.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

if not _via_google and not _pw_ok:
    st.markdown('<div class="sec"><b>//</b> ACCESS CONTROL</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="status-line">Jarvis istemal karne ke liye login karein. Owner password daalein'
        + (", ya apne Google (Gmail) account se login karein." if _google_ready else ".")
        + "</div>",
        unsafe_allow_html=True,
    )
    if _pw_secret:
        with st.form("pw_form"):
            _typed_pw = st.text_input("Owner password", type="password")
            _unlock = st.form_submit_button("UNLOCK")
        if _unlock:
            _tries = int(st.session_state.get("pw_tries", 0))
            if _tries >= 5:
                st.markdown(
                    '<div class="status-line">Bohat zyada ghalat koshishen. Page band karke dobara kholein.</div>',
                    unsafe_allow_html=True,
                )
            elif hmac.compare_digest(str(_typed_pw).encode("utf-8"), _pw_secret.encode("utf-8")):
                st.session_state["pw_ok"] = True
                st.session_state["pw_tries"] = 0
                st.rerun()
            else:
                st.session_state["pw_tries"] = _tries + 1
                time.sleep(1.5)
                st.markdown('<div class="status-line">Password ghalat hai.</div>', unsafe_allow_html=True)
    if _google_ready:
        st.button("LOGIN WITH GOOGLE", on_click=st.login)
    st.stop()

if _via_google:
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
    LOGIN_MODE = "GOOGLE"
else:
    USER_EMAIL = "owner-password"
    USER_NAME = "Owner"
    IS_ADMIN = True
    LOGIN_MODE = "PASSWORD"

if st.session_state.get("active_user") != USER_EMAIL:
    # koi aur banda isi browser mein login kare to pichle user ka data saaf
    for _k in ("history", "products", "raw", "error", "error_log", "model_used", "sources", "time",
               "sheet_error", "user_gemini_key", "user_serper_key", "history_upload", "chat",
               "last_audio_hash", "speak_now", "last_source", "ads_rows", "ads_rows_err", "acct_rows",
               "acct_rows_err", "ads_analysis", "content_out"):
        st.session_state.pop(_k, None)
    st.session_state["active_user"] = USER_EMAIL
st.session_state["is_admin"] = IS_ADMIN


def _do_logout():
    st.session_state.pop("pw_ok", None)
    if _via_google:
        st.logout()


_c1, _c2, _c3 = st.columns([3, 3, 1])
with _c1:
    st.caption(f"Login: {USER_NAME or USER_EMAIL} ({'Owner' if IS_ADMIN else 'User'})")
with _c2:
    st.radio("Palette", list(PALETTES), horizontal=True, key="palette", label_visibility="collapsed")
with _c3:
    st.button("LOGOUT", on_click=_do_logout)

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

tab_ov, tab_scan, tab_talk, tab_ads, tab_social, tab_arch = st.tabs(
    ["OVERVIEW", "SCAN", "TALK", "ADS LAB", "SOCIAL", "ARCHIVE"]
)

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

with tab_scan:
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
with tab_scan:
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
                st.session_state["last_source"] = (
                    "PASTED LIST" if pasted.strip() else ("LIVE SEARCH" if use_search else "AI KNOWLEDGE")
                )
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
with tab_talk:
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
with tab_arch:
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
# OVERVIEW (home screen): sirf asli data
# ---------------------------------------------------------------
def _clip(text, n=90):
    t = " ".join(str(text or "").split())
    return t if len(t) <= n else t[: n - 1] + "…"


def _panel(pid, title, chip, body, kind=""):
    chip_html = f'<span class="pchip {kind}">{esc(chip)}</span>' if chip else ""
    return (
        '<div class="panel"><div class="pin"><div class="ph">'
        f'<span class="pid">{esc(pid)}</span><span class="pt">{esc(title)}</span>{chip_html}</div>'
        f'<div class="pb">{body}</div></div></div>'
    )


def _kv(k, v, kind=""):
    return f'<div class="kv"><span class="k">{esc(k)}</span><span class="v {kind}">{esc(v)}</span></div>'


def _risk_counts(items, key):
    c = {"lo": 0, "md": 0, "hi": 0}
    for it in items:
        v = str(it.get(key, "")).strip().lower()
        c["lo" if v.startswith("low") else ("hi" if v.startswith("high") else "md")] += 1
    return c


def _risk_row(label, c):
    return (
        f'<div class="rk"><span class="k">{label}</span><div class="rbar">'
        f'<i class="lo" style="flex:{c["lo"]}"></i><i class="md" style="flex:{c["md"]}"></i>'
        f'<i class="hi" style="flex:{c["hi"]}"></i></div>'
        f'<span class="rv">{c["lo"]}/{c["md"]}/{c["hi"]}</span></div>'
    )


def _date_of(row):
    try:
        return datetime.datetime.strptime(str(row.get("Date", "")), "%Y-%m-%d").date()
    except ValueError:
        return None


def build_overview():
    hist = st.session_state.get("history", []) or []
    today = now_pkt().date()
    today_rows = [r for r in hist if _date_of(r) == today]
    week_rows = [r for r in hist if _date_of(r) and 0 <= (today - _date_of(r)).days <= 6]
    cur = st.session_state.get("products") or []
    targets = cur or [
        {"name": r.get("Product"), "score": r.get("Score"), "cod_risk": r.get("COD risk"),
         "shipping_risk": r.get("Shipping risk")}
        for r in today_rows
    ]
    best = int(max([to_num(r.get("Score"), 0) for r in today_rows] or [0]))
    sheet_err = st.session_state.get("sheet_error")

    flags = []
    if not api_key:
        flags.append("Gemini key nahi hai, scan nahi chalega.")
    if not serper_key():
        flags.append("Asli listings aur product photo band hain (Serper key nahi lagi).")
    if sheet_err:
        flags.append("Google Sheet se connect nahi ho saka.")
    elif not IS_ADMIN:
        flags.append("Aap ka data sirf is session mein hai. Excel download karke rakhein.")
    elif not sheets_configured():
        flags.append("Google Sheet connect nahi, history temporary hai.")
    if not today_rows:
        flags.append("Aaj ka scan abhi nahi hua.")

    hour = now_pkt().hour
    greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
    who = USER_NAME.split()[0] if (USER_NAME and not IS_ADMIN) else "sir"
    sub = "All systems ready." if not flags else f"{len(flags)} item{'s' if len(flags) != 1 else ''} flagged for your attention."
    center = (
        '<div class="center-hud"><div class="ringwrap">'
        '<div class="rg rg-ticks"></div><div class="rg rg-seg"></div><div class="rg rg-hi"></div>'
        '<div class="rg rg-dash"></div><div class="rg rg-thin"></div>'
        f'<div class="rg rg-core"><span class="cl">TARGETS TODAY</span><span class="cn">{len(today_rows)}</span>'
        f'<span class="cs">BEST {best}/10</span></div></div>'
        f'<div class="greet">{esc(greet)}, <em>{esc(who)}.</em></div><div class="gsub">{esc(sub)}</div></div>'
    )

    # SCN.01 last scan
    if cur:
        scan_body = (
            _kv("TIME", st.session_state.get("time") or "-")
            + _kv("TARGETS", len(cur))
            + _kv("MODEL", str(st.session_state.get("model_used") or "-").upper())
            + _kv("SOURCE", st.session_state.get("last_source") or "-")
        )
        scan_panel = _panel("SCN.01", "LAST SCAN", "DONE", scan_body, "ok")
    else:
        scan_panel = _panel("SCN.01", "LAST SCAN", "NONE", '<div class="dnote">Abhi is session mein koi scan nahi hua.</div>')

    # ARC.02 archive
    counts = {}
    for r in hist:
        d = str(r.get("Date", ""))
        counts[d] = counts.get(d, 0) + 1
    recent = sorted(counts.items(), reverse=True)[:5]
    top_n = max([n for _, n in recent] or [1])
    storage = "SESSION ONLY" if not IS_ADMIN else ("GOOGLE SHEET" if sheets_configured() and not sheet_err else "TEMPORARY")
    arc_body = (
        _kv("RECORDS", len(hist)) + _kv("TODAY", len(today_rows)) + _kv("LAST 7 DAYS", len(week_rows))
        + _kv("STORAGE", storage, "ok" if storage == "GOOGLE SHEET" else "warn")
    )
    for d, n in recent:
        arc_body += (
            f'<div class="trow"><span class="tn">{esc(d)}</span><span class="ts">{n}</span>'
            f'<div class="tb"><i style="width:{int(100 * n / top_n)}%"></i></div></div>'
        )
    arc_panel = _panel("ARC.02", "ARCHIVE", "LIVE" if hist else "EMPTY", arc_body, "ok" if hist else "warn")

    # SYS.03 system
    gem = ("OWNER KEY" if IS_ADMIN else "YOUR KEY") if api_key else "MISSING"
    sys_body = (
        _kv("GEMINI", gem, "ok" if api_key else "bad")
        + _kv("LISTINGS", "ON" if serper_key() else "OFF", "ok" if serper_key() else "warn")
        + _kv("ARCHIVE", storage, "ok" if storage == "GOOGLE SHEET" else "warn")
        + _kv("LOGIN", LOGIN_MODE)
        + _kv("VOICE", "BROWSER TTS")
    )
    bad_sys = (not api_key)
    sys_panel = _panel("SYS.03", "SYSTEM STATUS", "ERROR" if bad_sys else "ONLINE", sys_body, "bad" if bad_sys else "ok")

    # TGT.04 top targets
    ranked = sorted(targets, key=lambda p: to_num(p.get("score"), 0), reverse=True)[:5]
    if ranked:
        tgt_body = "".join(
            f'<div class="trow"><span class="tn">{esc(_clip(p.get("name"), 38))}</span>'
            f'<span class="ts">{int(to_num(p.get("score"), 0))}/10</span>'
            f'<div class="tb"><i style="width:{int(max(0, min(10, to_num(p.get("score"), 0))) * 10)}%"></i></div></div>'
            for p in ranked
        )
    else:
        tgt_body = '<div class="dnote">Scan ke baad yahan top products nazar aayenge.</div>'
    tgt_panel = _panel("TGT.04", "TOP TARGETS", str(len(targets)) if targets else "NONE", tgt_body)

    # RSK.05 risk mix
    if targets:
        rsk_body = (
            _risk_row("COD", _risk_counts(targets, "cod_risk"))
            + _risk_row("SHIP", _risk_counts(targets, "shipping_risk"))
            + '<div class="dnote">Low / Medium / High ki ginti.</div>'
        )
    else:
        rsk_body = '<div class="dnote">Scan ke baad risk ka hisab yahan aayega.</div>'
    rsk_panel = _panel("RSK.05", "RISK MIX", None, rsk_body)

    # LOG.06 jarvis log
    events = []
    if cur:
        events.append(("SCAN", f"{len(cur)} targets, {str(st.session_state.get('model_used') or '-').upper()}", ""))
    for m in (st.session_state.get("chat") or [])[-4:]:
        events.append(("JARVIS" if m.get("role") == "jarvis" else "AAP", _clip(m.get("text"), 90), ""))
    log_body = "".join(
        f'<div class="logrow"><span class="lt">{esc(t)}</span><span class="lm">{esc(msg)}</span></div>'
        for t, msg, _ in reversed(events)
    ) or '<div class="dnote">Abhi koi activity nahi.</div>'
    log_panel = _panel("LOG.06", "JARVIS LOG", "LISTENING" if events else None, log_body)

    # ALR.07 alerts
    alr_body = "".join(
        f'<div class="logrow"><span class="lt warn">WARN</span><span class="lm">{esc(f)}</span></div>' for f in flags
    ) or '<div class="logrow"><span class="lt ok">OK</span><span class="lm">Koi alert nahi.</span></div>'
    alr_panel = _panel("ALR.07", "ALERTS", str(len(flags)) if flags else "CLEAR", alr_body, "warn" if flags else "ok")

    return scan_panel + arc_panel + sys_panel, center, tgt_panel + rsk_panel + log_panel + alr_panel


# ---------------------------------------------------------------
# ADS LAB (ads report upload + analysis) and SOCIAL (accounts list + content planner)
# ---------------------------------------------------------------
ADS_COLUMNS = [
    "Upload date", "Platform", "Campaign", "Spend", "Impressions", "Clicks", "Purchases", "Revenue",
    "CTR (%)", "CPC", "CPA", "ROAS", "Flag", "Notes",
]
ACCT_COLUMNS = ["Platform", "Handle", "URL", "Notes", "Added"]
ADS_PLATFORMS = ["Meta (Facebook / Instagram)", "TikTok", "Snapchat", "Google Ads", "Other"]
SOCIAL_PLATFORMS = ["Instagram", "TikTok", "Facebook", "YouTube", "Snapchat", "WhatsApp Business", "Other"]
NONE_OPT = "(nahi hai)"
ADS_SHOW = ["Campaign", "Spend", "Impressions", "Clicks", "Purchases", "Revenue", "CTR (%)", "CPC", "CPA", "ROAS", "Flag"]

ADS_SYSTEM = """ROLE: ADS ANALYST. You analyse Meta / TikTok ad campaign data for a small UAE dropshipping store that sells with cash on delivery.
Answer in __LANG__. Be practical and short: 8 to 12 bullet points in 3 sections called "Kya kaam kar raha hai", "Kya band ya theek karein", "Agla test".
Use ONLY the numbers given. Never invent numbers, benchmarks or results. Spend and revenue are in the ad account currency. If spend is very low or purchases are few, say that the conclusion is weak.
COD returns, shipping cost and product cost are not in the data, so break-even is only an estimate.
Plain text only, no tables."""

CONTENT_SYSTEM = """ROLE: CONTENT CREATOR. You write short-form social content (TikTok, Instagram Reels, Facebook) for a UAE dropshipping store that sells with cash on delivery.
Write in __LANG__. Tone: __TONE__.
Output plain text with these sections: HOOKS (3 options for the first 3 seconds), SCRIPT (15 to 30 seconds, scene by scene), CAPTION, HASHTAGS (8 to 12), CTA.
Rules: no medical or health claims, no brand or trademark names, no fake discounts, fake countdowns or fake scarcity, no invented reviews or numbers. Keep it respectful for UAE culture."""


def gemini_error_msg(e):
    t = str(e)
    if "API key not valid" in t or "API_KEY_INVALID" in t:
        return "Gemini ne key qabool nahi ki. Key dobara paste karein."
    if t == "BUSY" or is_busy_error(e):
        return "Google ke servers abhi busy hain. Thori der baad dobara try karein."
    return "Jarvis jawab nahi de saka. Detail: " + t[:200]


def ask_text(prompt, system):
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000))
    models = candidate_models(client)[:4]
    started = time.time()
    last_error = None
    for round_no in range(2):
        for model in models:
            if time.time() - started > 100:
                break
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[prompt],
                    config=types.GenerateContentConfig(system_instruction=system, temperature=0.5),
                )
                text = (response.text or "").strip()
                if text:
                    st.session_state["model_used"] = model
                    return text
                last_error = RuntimeError("Khali jawab aaya")
            except Exception as e:
                last_error = e
                if not is_busy_error(e):
                    raise
        if round_no == 0:
            time.sleep(3)
    raise last_error or RuntimeError("BUSY")


# ---------- extra Google Sheet tabs (owner only) ----------
def aux_sheet(name, headers):
    sh = get_sheet().spreadsheet
    try:
        return sh.worksheet(name)
    except Exception:
        w = sh.add_worksheet(title=name, rows=500, cols=max(len(headers), 10))
        w.append_row(headers, value_input_option="RAW")
        return w


def aux_rows(key, name, headers, refresh=False):
    if refresh or key not in st.session_state:
        rows = []
        st.session_state[key + "_err"] = None
        if sheets_configured():
            try:
                for r in aux_sheet(name, headers).get_all_records():
                    d = {h: ("" if r.get(h) is None else r.get(h)) for h in headers}
                    if any(str(v).strip() for v in d.values()):
                        rows.append(d)
            except Exception as e:
                st.session_state[key + "_err"] = str(e)[:200]
        st.session_state[key] = rows
    return st.session_state[key]


def aux_add(key, name, headers, new_rows, keyfn):
    cur = aux_rows(key, name, headers)
    known = {keyfn(r) for r in cur}
    fresh = []
    for r in new_rows:
        k = keyfn(r)
        if k not in known:
            known.add(k)
            fresh.append(r)
    if not fresh:
        return 0
    st.session_state[key] = cur + fresh
    if sheets_configured():
        try:
            aux_sheet(name, headers).append_rows(
                [[r.get(h, "") for h in headers] for r in fresh], value_input_option="RAW"
            )
            st.session_state[key + "_err"] = None
        except Exception as e:
            st.session_state[key + "_err"] = str(e)[:200]
    return len(fresh)


def aux_remove(key, name, headers, idx):
    cur = aux_rows(key, name, headers)
    if not (0 <= idx < len(cur)):
        return
    if sheets_configured():
        try:
            aux_sheet(name, headers).delete_rows(idx + 2)
            st.session_state[key + "_err"] = None
        except Exception as e:
            st.session_state[key + "_err"] = str(e)[:200]
    cur.pop(idx)


# ---------- reading and understanding an ads export ----------
def _norm(h):
    return re.sub(r"[^a-z0-9]+", "", str(h).lower())


def to_float(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or s in ("-", "—", "–") or s.lower() in ("n/a", "na", "nan", "null"):
        return None
    s = re.sub(r"[^0-9.,\-]", "", s)
    if not s or s in ("-", ".", ","):
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        s = s.replace(",", ".") if len(parts) == 2 and len(parts[1]) in (1, 2) else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def read_table(uploaded):
    name = str(getattr(uploaded, "name", "")).lower()
    data = uploaded.getvalue()
    if len(data) > 5_000_000:
        raise ValueError("File 5 MB se bari hai")
    raw_rows = []
    if name.endswith(".xlsx"):
        from openpyxl import load_workbook

        ws = load_workbook(io.BytesIO(data), data_only=True, read_only=True).active
        for r in ws.iter_rows(values_only=True):
            raw_rows.append(list(r))
            if len(raw_rows) > 5001:
                break
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        sample = text[:4096]
        delim = max([",", ";", "\t"], key=sample.count)
        for r in csv.reader(io.StringIO(text), delimiter=delim):
            raw_rows.append(r)
            if len(raw_rows) > 5001:
                break
    if not raw_rows:
        raise ValueError("File khali hai")
    head = [str(h).strip() if h is not None else "" for h in raw_rows[0]]
    keep, seen = [], set()
    for i, h in enumerate(head):
        if h and h not in seen:
            seen.add(h)
            keep.append((i, h))
    rows = []
    for r in raw_rows[1:]:
        if not r or all(c is None or str(c).strip() == "" for c in r):
            continue
        rows.append({h: (r[i] if i < len(r) else None) for i, h in keep})
    if not keep or not rows:
        raise ValueError("File mein data nahi mila")
    return [h for _, h in keep], rows


def guess_columns(headers):
    norm = [(h, _norm(h)) for h in headers]

    def find(tests):
        for t in tests:
            for h, n in norm:
                if t(n):
                    return h
        return None

    def clean(n):
        return not any(x in n for x in ("roas", "cost", "value", "rate", "per"))

    return {
        "campaign": find([
            lambda n: n == "campaignname", lambda n: n == "campaign", lambda n: n == "adsetname",
            lambda n: n == "adgroupname", lambda n: n == "adname", lambda n: n.endswith("name"),
        ]),
        "spend": find([
            lambda n: n.startswith("amountspent"),
            lambda n: n in ("spend", "totalspend", "cost", "totalcost", "spendaed", "costaed"),
        ]),
        "impressions": find([
            lambda n: n == "impressions",
            lambda n: "impressions" in n and "cost" not in n and "per" not in n,
        ]),
        "clicks": find([
            lambda n: n.startswith("linkclicks") and "cost" not in n and "ctr" not in n,
            lambda n: n in ("clicks", "clicksall", "clicksdestination"),
            lambda n: n.startswith("clicks") and "cost" not in n and "ctr" not in n,
        ]),
        "purchases": find([
            lambda n: n in ("purchases", "websitepurchases"),
            lambda n: n.startswith("purchases") and clean(n),
            lambda n: n in ("conversions", "results"),
            lambda n: n.startswith("conversions") and clean(n),
            lambda n: "completepayment" in n and clean(n),
        ]),
        "revenue": find([
            lambda n: "purchaseconversionvalue" in n,
            lambda n: n == "conversionvalue",
            lambda n: "purchasevalue" in n,
            lambda n: "conversionvalue" in n,
            lambda n: n in ("revenue", "totalrevenue"),
        ]),
    }


def aggregate_ads(rows, mapping):
    agg = {}
    for r in rows:
        name = str(r.get(mapping["campaign"]) or "").strip()
        nn = _norm(name)
        if not name or nn in ("total", "totals", "summary") or nn.startswith("resultsfrom"):
            continue
        a = agg.setdefault(name, {"spend": 0.0, "impressions": 0.0, "clicks": 0.0, "purchases": 0.0,
                                  "revenue": 0.0, "has_rev": False})
        for k in ("spend", "impressions", "clicks", "purchases", "revenue"):
            col = mapping.get(k)
            v = to_float(r.get(col)) if col else None
            if v is not None:
                a[k] += v
                if k == "revenue":
                    a["has_rev"] = True
    return agg


def ads_flag(spend, pur, roas, cpa, be_roas, be_cpa):
    if spend <= 0:
        return "No spend"
    if pur <= 0:
        return "No purchases"
    if roas is not None and be_roas:
        if roas < be_roas:
            return "Below break-even"
        return "Strong" if roas >= be_roas * 1.5 else "OK"
    if cpa is not None and be_cpa:
        if cpa > be_cpa:
            return "CPA high"
        return "Strong" if cpa <= be_cpa * 0.67 else "OK"
    return "OK"


def _r2(x):
    return None if x is None else round(x, 2)


def ads_metrics(agg, margin_pct, aov):
    be_roas = 100.0 / margin_pct if margin_pct and margin_pct > 0 else None
    be_cpa = aov * margin_pct / 100.0 if aov and aov > 0 and margin_pct and margin_pct > 0 else None
    out = []
    for name, a in agg.items():
        spend, imp, clk, pur, rev = a["spend"], a["impressions"], a["clicks"], a["purchases"], a["revenue"]
        ctr = clk / imp * 100 if imp else None
        cpc = spend / clk if clk else None
        cpa = spend / pur if pur else None
        roas = rev / spend if (a["has_rev"] and spend) else None
        out.append({
            "Campaign": name, "Spend": _r2(spend), "Impressions": int(imp), "Clicks": int(clk),
            "Purchases": int(pur) if float(pur).is_integer() else _r2(pur),
            "Revenue": _r2(rev) if a["has_rev"] else "", "CTR (%)": _r2(ctr), "CPC": _r2(cpc),
            "CPA": _r2(cpa), "ROAS": _r2(roas), "Flag": ads_flag(spend, pur, roas, cpa, be_roas, be_cpa),
        })
    out.sort(key=lambda r: -(r["Spend"] or 0))
    tot = {k: sum(a[k] for a in agg.values()) for k in ("spend", "impressions", "clicks", "purchases", "revenue")}
    has_rev = any(a["has_rev"] for a in agg.values())
    totals = {
        "spend": tot["spend"], "purchases": tot["purchases"], "impressions": tot["impressions"],
        "clicks": tot["clicks"], "revenue": tot["revenue"] if has_rev else None,
        "ctr": tot["clicks"] / tot["impressions"] * 100 if tot["impressions"] else None,
        "cpc": tot["spend"] / tot["clicks"] if tot["clicks"] else None,
        "cpa": tot["spend"] / tot["purchases"] if tot["purchases"] else None,
        "roas": tot["revenue"] / tot["spend"] if (has_rev and tot["spend"]) else None,
        "be_roas": be_roas, "be_cpa": be_cpa,
    }
    return out, totals


def fmt_n(x, d=2):
    if x is None or x == "":
        return "-"
    try:
        return f"{float(x):,.{d}f}"
    except (TypeError, ValueError):
        return str(x)


def ads_prompt(platform, margin_pct, aov, totals, rows):
    lines = [
        f"Platform: {platform}",
        f"Product margin estimate: {margin_pct}% (break-even ROAS about {fmt_n(totals['be_roas'])})",
        f"Average selling price: {aov if aov else 'not given'}",
        "Totals: spend {}, purchases {}, revenue {}, ROAS {}, CPA {}, CTR {}%".format(
            fmt_n(totals["spend"]), fmt_n(totals["purchases"], 0), fmt_n(totals["revenue"]),
            fmt_n(totals["roas"]), fmt_n(totals["cpa"]), fmt_n(totals["ctr"])),
        "Campaigns (top by spend):",
    ]
    for r in rows[:15]:
        lines.append(
            f"- {r['Campaign']} | spend {r['Spend']} | impressions {r['Impressions']} | clicks {r['Clicks']} | "
            f"purchases {r['Purchases']} | revenue {r['Revenue'] or 'n/a'} | CTR {r['CTR (%)']} | "
            f"CPA {r['CPA']} | ROAS {r['ROAS']} | flag {r['Flag']}"
        )
    return "\n".join(lines)


def build_table_excel(rows, columns, title="Jarvis"):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = title[:30]
    ws.append(columns)
    for r in rows:
        ws.append([r.get(c, "") for c in columns])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0B3A55")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    for i, c in enumerate(columns, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = max(12, min(40, len(str(c)) + 6))
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def preset_range(label, today):
    if label == "Aaj":
        return today, today
    if label == "Kal":
        y = today - datetime.timedelta(days=1)
        return y, y
    if label.startswith("Pichle"):
        n = int(label.split()[1])
        return today - datetime.timedelta(days=n - 1), today
    return None, None


def filter_by_date(rows, field, start, end):
    if start is None or end is None:
        return list(rows)
    out = []
    for r in rows:
        try:
            d = datetime.datetime.strptime(str(r.get(field, "")), "%Y-%m-%d").date()
        except ValueError:
            continue
        if start <= d <= end:
            out.append(r)
    return out


def accounts_html(rows):
    out = []
    for r in rows:
        url = safe_url(r.get("URL"))
        link = (
            f'<a class="vlink" href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">OPEN</a>'
            if url
            else ""
        )
        out.append(
            f'<div class="lrow"><span class="lstore">{esc(r.get("Platform"))}</span>'
            f'<span class="lprice">{esc(r.get("Handle"))}</span>{link}</div>'
        )
    return "".join(out)


def ai_box(text):
    return (
        '<div class="bubble jarvis"><span class="who">JARVIS</span>'
        + esc(text).replace("\n", "<br>")
        + "</div>"
    )


# ---------------------------------------------------------------
# ADS LAB tab
# ---------------------------------------------------------------
with tab_ads:
    st.markdown('<div class="sec"><b>//</b> ADS LAB</div>', unsafe_allow_html=True)
    st.caption(
        "Meta Ads Manager ya TikTok Ads Manager se report export karke (CSV ya Excel) yahan upload karein. "
        "Jarvis har campaign ka CTR, CPC, CPA aur ROAS nikal kar batata hai kaunsa theek chal raha hai. "
        "Export ka menu platform ke hisaab se badalta rehta hai, aam taur par Reports ya Reporting mein Export ya Download hota hai. "
        "Aap ke ads ka data analysis ke liye Google Gemini ko bheja jata hai."
    )
    _plat = st.selectbox("Platform", ADS_PLATFORMS, key="ads_platform")
    _up = st.file_uploader("Ads report (CSV ya Excel)", type=["csv", "xlsx"], key="ads_file")
    _ads_rows, _ads_tot = [], None
    if _up is not None:
        try:
            _headers, _raw = read_table(_up)
        except Exception as e:
            _headers, _raw = [], []
            st.markdown(
                '<div class="status-line">File nahi parhi ja saki: ' + esc(str(e)[:200]) + "</div>",
                unsafe_allow_html=True,
            )
        if _headers:
            _fid = hashlib.md5(_up.getvalue()).hexdigest()[:8]
            _guess = guess_columns(_headers)
            _opts = [NONE_OPT] + _headers
            st.caption("Jarvis ne columns apne andaze se chune hain. Galat lagen to neeche theek kar lein.")
            _m1, _m2, _m3 = st.columns(3)
            _pick = {}
            _labels = [("campaign", "Campaign ka naam"), ("spend", "Kharcha (spend)"), ("impressions", "Impressions"),
                       ("clicks", "Clicks"), ("purchases", "Purchases / orders"), ("revenue", "Revenue (sale ki value)")]
            for _i, (_k, _lab) in enumerate(_labels):
                with (_m1, _m2, _m3)[_i % 3]:
                    _pi = _opts.index(_guess[_k]) if _guess.get(_k) in _opts else 0
                    _v = st.selectbox(_lab, _opts, index=_pi, key=f"ads_map_{_k}_{_fid}")
                    _pick[_k] = None if _v == NONE_OPT else _v
            _n1, _n2 = st.columns(2)
            with _n1:
                _margin = st.number_input("Product margin % (andaza, break-even ke liye)", min_value=1.0, max_value=95.0,
                                          value=50.0, step=1.0)
            with _n2:
                _aov = st.number_input("Average selling price (optional)", min_value=0.0, value=0.0, step=1.0)
            if not _pick["campaign"] or not _pick["spend"]:
                st.markdown(
                    '<div class="status-line">Campaign aur Kharcha (spend) ke columns chunna zaroori hai.</div>',
                    unsafe_allow_html=True,
                )
            else:
                _agg = aggregate_ads(_raw, _pick)
                if not _agg:
                    st.markdown('<div class="status-line">Koi campaign row nahi mili.</div>', unsafe_allow_html=True)
                else:
                    _ads_rows, _ads_tot = ads_metrics(_agg, _margin, _aov)
    if _ads_tot:
        _cA, _cB, _cC = st.columns(3)
        with _cA:
            st.markdown(_panel("ADS.01", "Spend", f"{len(_ads_rows)} campaigns",
                               _kv("Spend", fmt_n(_ads_tot["spend"])) + _kv("Impressions", fmt_n(_ads_tot["impressions"], 0))
                               + _kv("Clicks", fmt_n(_ads_tot["clicks"], 0))), unsafe_allow_html=True)
        with _cB:
            st.markdown(_panel("ADS.02", "Results", "",
                               _kv("Purchases", fmt_n(_ads_tot["purchases"], 0)) + _kv("Revenue", fmt_n(_ads_tot["revenue"]))
                               + _kv("ROAS", fmt_n(_ads_tot["roas"]))), unsafe_allow_html=True)
        with _cC:
            st.markdown(_panel("ADS.03", "Costs", "",
                               _kv("CPA", fmt_n(_ads_tot["cpa"])) + _kv("CPC", fmt_n(_ads_tot["cpc"]))
                               + _kv("Break-even ROAS", fmt_n(_ads_tot["be_roas"]))), unsafe_allow_html=True)
        st.dataframe(_ads_rows, hide_index=True)
        st.caption(
            "Flags sirf andaza hain: COD ki wapsi, shipping aur product ki cost is data mein shamil nahi. "
            "Kam kharche ya kam orders par nateeja kamzor hota hai."
        )
        _b1, _b2, _b3 = st.columns(3)
        with _b1:
            _save = st.button("ARCHIVE MEIN SAVE KAREIN")
        with _b2:
            _lang_ads = st.selectbox("Analysis ki zubaan", ["Roman Urdu", "English"], key="ads_lang")
        with _b3:
            _analyse = st.button("JARVIS SE ANALYSIS")
        st.download_button(
            "EXCEL DOWNLOAD (is report ka)",
            data=build_table_excel(_ads_rows, ADS_SHOW, "Ads"),
            file_name="jarvis_ads_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if _save:
            _today = now_pkt().strftime("%Y-%m-%d")
            _new = [
                {"Upload date": _today, "Platform": _plat, "Campaign": r["Campaign"], "Spend": r["Spend"],
                 "Impressions": r["Impressions"], "Clicks": r["Clicks"], "Purchases": r["Purchases"],
                 "Revenue": r["Revenue"], "CTR (%)": r["CTR (%)"] if r["CTR (%)"] is not None else "",
                 "CPC": r["CPC"] if r["CPC"] is not None else "", "CPA": r["CPA"] if r["CPA"] is not None else "",
                 "ROAS": r["ROAS"] if r["ROAS"] is not None else "", "Flag": r["Flag"], "Notes": ""}
                for r in _ads_rows
            ]
            _added = aux_add("ads_rows", "Ads", ADS_COLUMNS, _new,
                             lambda r: (str(r.get("Upload date")), str(r.get("Platform")), str(r.get("Campaign")).lower()))
            _where = "Google Sheet ke Ads tab mein" if sheets_configured() else "is session mein"
            st.markdown(
                f'<div class="status-line">{_added} campaign rows save hui ({_where}). '
                "Same din ki same campaign dobara save nahi hoti.</div>",
                unsafe_allow_html=True,
            )
        if _analyse:
            if not api_key:
                st.markdown(
                    '<div class="status-line">Pehle apni Gemini API key daalein, phir analysis chalayein.</div>',
                    unsafe_allow_html=True,
                )
            else:
                with st.spinner("Jarvis ads ka analysis kar raha hai..."):
                    try:
                        st.session_state["ads_analysis"] = ask_text(
                            ads_prompt(_plat, _margin, _aov, _ads_tot, _ads_rows),
                            ADS_SYSTEM.replace("__LANG__", _lang_ads),
                        )
                    except Exception as e:
                        st.markdown('<div class="status-line">' + esc(gemini_error_msg(e)) + "</div>",
                                    unsafe_allow_html=True)
    if st.session_state.get("ads_analysis"):
        st.markdown(ai_box(st.session_state["ads_analysis"]), unsafe_allow_html=True)

    st.markdown('<div class="sec"><b>//</b> SAVED ADS DATA</div>', unsafe_allow_html=True)
    if sheets_configured() and st.button("ADS REFRESH (Sheet se)"):
        aux_rows("ads_rows", "Ads", ADS_COLUMNS, refresh=True)
    _saved = aux_rows("ads_rows", "Ads", ADS_COLUMNS)
    if st.session_state.get("ads_rows_err"):
        st.markdown(
            '<div class="status-line">Ads Sheet se connect nahi ho saka: ' + esc(st.session_state["ads_rows_err"]) + "</div>",
            unsafe_allow_html=True,
        )
    if not _saved:
        st.caption("Abhi koi ads data save nahi hua.")
    else:
        _ap = st.selectbox("Kaunsa data chahiye", ["Aaj", "Kal", "Pichle 3 din", "Pichle 7 din", "Pichle 30 din", "Sab dates"],
                           index=4, key="ads_preset")
        _s, _e = preset_range(_ap, now_pkt().date())
        _shown = sorted(filter_by_date(_saved, "Upload date", _s, _e), key=lambda r: str(r.get("Upload date")), reverse=True)
        st.caption(f"{len(_shown)} rows mili.")
        if _shown:
            st.dataframe([{c: r.get(c, "") for c in ADS_COLUMNS} for r in _shown], hide_index=True)
            st.download_button(
                "EXCEL DOWNLOAD (saved ads)",
                data=build_table_excel(_shown, ADS_COLUMNS, "Saved ads"),
                file_name="jarvis_saved_ads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        if not sheets_configured():
            st.caption("Yeh data sirf is session mein hai. Excel download karke rakhein.")


# ---------------------------------------------------------------
# SOCIAL tab
# ---------------------------------------------------------------
with tab_social:
    st.markdown('<div class="sec"><b>//</b> MY ACCOUNTS</div>', unsafe_allow_html=True)
    st.caption(
        "Yahan aap apne social accounts ki list (naam aur link) rakh sakte hain. Asli 'account link karna' "
        "(Meta ya TikTok ke login se post karna ya comments parhna) abhi nahi hai: us ke liye har platform ki "
        "official ijazat aur app review chahiye."
    )
    _accts = aux_rows("acct_rows", "Accounts", ACCT_COLUMNS)
    if st.session_state.get("acct_rows_err"):
        st.markdown(
            '<div class="status-line">Accounts Sheet se connect nahi ho saka: ' + esc(st.session_state["acct_rows_err"]) + "</div>",
            unsafe_allow_html=True,
        )
    with st.form("acct_form", clear_on_submit=True):
        _a1, _a2, _a3 = st.columns(3)
        with _a1:
            _ap_plat = st.selectbox("Platform", SOCIAL_PLATFORMS, key="acct_platform")
        with _a2:
            _ap_handle = st.text_input("Naam / handle (maslan @mystore)")
        with _a3:
            _ap_url = st.text_input("Link (optional)")
        _ap_add = st.form_submit_button("ACCOUNT ADD KAREIN")
    if _ap_add and _ap_handle.strip():
        aux_add(
            "acct_rows", "Accounts", ACCT_COLUMNS,
            [{"Platform": _ap_plat, "Handle": _ap_handle.strip(), "URL": safe_url(_ap_url), "Notes": "",
              "Added": now_pkt().strftime("%Y-%m-%d")}],
            lambda r: (str(r.get("Platform")), str(r.get("Handle")).lower()),
        )
        _accts = aux_rows("acct_rows", "Accounts", ACCT_COLUMNS)
    if _accts:
        st.markdown(accounts_html(_accts), unsafe_allow_html=True)
        _labels_ac = [f"{r.get('Platform')} · {r.get('Handle')}" for r in _accts]
        _rm = st.selectbox("Hatane ke liye chunein", _labels_ac, key="acct_remove_pick")
        if st.button("ACCOUNT HATAYEIN"):
            aux_remove("acct_rows", "Accounts", ACCT_COLUMNS, _labels_ac.index(_rm))
            st.rerun()
    else:
        st.caption("Abhi koi account add nahi hua.")

    st.markdown('<div class="sec"><b>//</b> CONTENT PLANNER</div>', unsafe_allow_html=True)
    st.caption(
        "Kisi product ke liye hooks, script, caption aur hashtags banwayein. Jarvis post nahi karta, sirf likh kar deta hai. "
        "AI ke likhe daawe post karne se pehle khud check karein."
    )
    _cur_names = [str(p.get("name")) for p in (st.session_state.get("products") or []) if p.get("name")]
    _hist_names = []
    for _r in (st.session_state.get("history") or [])[-40:]:
        _pn = str(_r.get("Product") or "")
        if _pn and _pn not in _cur_names and _pn not in _hist_names:
            _hist_names.append(_pn)
    _prod_opts = _cur_names + _hist_names + ["Apna product likhein"]
    _cp1, _cp2 = st.columns(2)
    with _cp1:
        _prod_pick = st.selectbox("Product", _prod_opts, key="content_product")
        _prod_custom = st.text_input("Apna product (agar upar 'Apna product likhein' chuna)", key="content_custom")
    with _cp2:
        _cplat = st.selectbox("Platform", ["TikTok", "Instagram Reels", "Facebook", "Snapchat"], key="content_platform")
        _clang = st.selectbox("Zubaan", ["Roman Urdu", "English"], key="content_lang")
        _ctone = st.selectbox("Andaz", ["Fun", "Premium", "Seedha aur sachcha"], key="content_tone")
    if st.button("IDEAS BANAYEIN"):
        _pname = _prod_custom.strip() if _prod_pick == "Apna product likhein" else _prod_pick
        if not _pname:
            st.markdown('<div class="status-line">Product ka naam chunein ya likhein.</div>', unsafe_allow_html=True)
        elif not api_key:
            st.markdown(
                '<div class="status-line">Pehle apni Gemini API key daalein, phir ideas banwayein.</div>',
                unsafe_allow_html=True,
            )
        else:
            _extra_info = ""
            for _p in (st.session_state.get("products") or []):
                if str(_p.get("name")) == _pname:
                    _extra_info = (f" Selling price {_p.get('sell_price_aed')} AED. Why it can sell: {_p.get('why_chosen', '')}")
            with st.spinner("Jarvis likh raha hai..."):
                try:
                    st.session_state["content_out"] = ask_text(
                        f"Product: {_pname}. Platform: {_cplat}.{_extra_info}",
                        CONTENT_SYSTEM.replace("__LANG__", _clang).replace("__TONE__", _ctone),
                    )
                except Exception as e:
                    st.markdown('<div class="status-line">' + esc(gemini_error_msg(e)) + "</div>", unsafe_allow_html=True)
    if st.session_state.get("content_out"):
        st.text_area("Jarvis ka likha hua (copy kar sakte hain)", value=st.session_state["content_out"], height=360)



with tab_ov:
    _left, _center, _right = build_overview()
    _colL, _colC, _colR = st.columns([1, 1.25, 1])
    with _colL:
        st.markdown(_left, unsafe_allow_html=True)
    with _colC:
        st.markdown(_center, unsafe_allow_html=True)
    with _colR:
        st.markdown(_right, unsafe_allow_html=True)
    st.caption("Naya scan chalane ke liye SCAN tab kholein. Is screen par sirf asli (aap ke apne) data ki halat dikhti hai.")
