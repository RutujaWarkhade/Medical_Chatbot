import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import io
import hashlib
import json
import os
import re

from llm_engine import get_qa_chain
from symptom_extractor import extract_symptoms_llm
from hospital_finder import find_hospitals_osm

from deep_translator import GoogleTranslator
from gtts import gTTS
from pydub import AudioSegment
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import tempfile
import time
from datetime import datetime

from chat_storage import (
    load_user_chats,
    create_chat_session,
    add_chat_message,
    delete_chat_session
)


# ===== Page Config =====
st.set_page_config(
    page_title="MediSense AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== Inject Custom CSS =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root Variables ───────────────────────────────────────────── */
:root {
    --teal:       #0d9488;
    --teal-light: #14b8a6;
    --teal-dark:  #0f766e;
    --navy:       #0f172a;
    --navy-mid:   #1e293b;
    --navy-soft:  #334155;
    --ivory:      #f8fafc;
    --muted:      #94a3b8;
    --card-bg:    rgba(30,41,59,0.85);
    --border:     rgba(148,163,184,0.12);
    --accent:     #f59e0b;
    --danger:     #ef4444;
    --success:    #10b981;
    --radius:     14px;
    --shadow:     0 8px 32px rgba(0,0,0,0.32);
}

/* ── Global Reset ─────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--navy) !important;
    color: var(--ivory) !important;
}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #111827 50%, #0c1a2e 100%) !important;
}

/* Subtle animated grain */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
    opacity: 0.4;
}

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1521 0%, #0f1e2e 100%) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] > div {
    padding-top: 1.5rem !important;
}

/* ── Hide default Streamlit chrome ───────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── Typography ───────────────────────────────────────────────── */
h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* ── Buttons ──────────────────────────────────────────────────── */
.stButton > button {
    background: var(--navy-mid) !important;
    color: var(--ivory) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
    padding: 0.5rem 1rem !important;
}

.stButton > button:hover {
    background: var(--teal-dark) !important;
    border-color: var(--teal) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(13,148,136,0.25) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--teal) 0%, var(--teal-dark) 100%) !important;
    border-color: var(--teal) !important;
    color: white !important;
    box-shadow: 0 4px 16px rgba(13,148,136,0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--teal-light) 0%, var(--teal) 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(13,148,136,0.45) !important;
}

/* ── Inputs ───────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--ivory) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s ease !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 3px rgba(13,148,136,0.15) !important;
}

input[type="password"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--ivory) !important;
}

/* ── Selectbox ────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--ivory) !important;
}

/* ── Chat messages ────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 0.5rem 0 !important;
}

[data-testid="stChatMessage"][data-testid*="user"] .stMarkdown {
    background: linear-gradient(135deg, rgba(13,148,136,0.18) 0%, rgba(15,118,110,0.12) 100%);
    border: 1px solid rgba(13,148,136,0.25);
    border-radius: 18px 18px 4px 18px;
    padding: 1rem 1.25rem;
}

[data-testid="stChatMessage"] .stMarkdown {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 4px 18px 18px 18px;
    padding: 1rem 1.25rem;
    backdrop-filter: blur(8px);
}

/* ── Chat input ───────────────────────────────────────────────── */
[data-testid="stChatInput"] > div {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(12px) !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--ivory) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Alerts ───────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border: none !important;
    backdrop-filter: blur(8px) !important;
}

.element-container .stAlert[data-baseweb="notification"] {
    background: rgba(30,41,59,0.9) !important;
}

/* ── Expander ─────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(15,23,42,0.6) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}

/* ── Spinner ──────────────────────────────────────────────────── */
[data-testid="stSpinner"] > div {
    border-top-color: var(--teal) !important;
}

/* ── Divider ──────────────────────────────────────────────────── */
hr {
    border-color: var(--border) !important;
    margin: 1rem 0 !important;
}

/* ── Caption / Small text ─────────────────────────────────────── */
.stCaption, small {
    color: var(--muted) !important;
    font-size: 0.78rem !important;
}

/* ── Custom Cards ─────────────────────────────────────────────── */
.medisense-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
    transition: border-color 0.2s ease;
}

.medisense-card:hover {
    border-color: rgba(13,148,136,0.3);
}

/* ── Logo / Brand ─────────────────────────────────────────────── */
.brand-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 0.25rem;
}

.brand-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #14b8a6, #f59e0b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.brand-tagline {
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: -4px;
}

/* ── Session buttons ──────────────────────────────────────────── */
.session-item {
    position: relative;
}

/* ── Stat badges ──────────────────────────────────────────────── */
.stat-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(13,148,136,0.12);
    border: 1px solid rgba(13,148,136,0.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    color: var(--teal-light);
    font-weight: 500;
}

/* ── Auth Form Container ──────────────────────────────────────── */
.auth-container {
    max-width: 420px;
    margin: 0 auto;
}

/* ── Section Labels ───────────────────────────────────────────── */
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.5rem;
    padding-left: 0.25rem;
}

/* ── Pill tab selector ────────────────────────────────────────── */
.stRadio > div {
    background: rgba(15,23,42,0.8) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
    gap: 4px !important;
}

.stRadio > div > label {
    border-radius: 8px !important;
    padding: 6px 16px !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

.stRadio > div > label[data-checked="true"] {
    background: var(--teal) !important;
    color: white !important;
}

/* ── Progress / loading bar ───────────────────────────────────── */
.stProgress > div > div {
    background: linear-gradient(90deg, var(--teal), var(--teal-light)) !important;
    border-radius: 4px !important;
}

/* ── Success / error inline ──────────────────────────────────── */
.inline-success {
    color: var(--success);
    font-size: 0.82rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

.inline-error {
    color: var(--danger);
    font-size: 0.82rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Animations ───────────────────────────────────────────────── */
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0);    }
}

.fade-in {
    animation: fadeSlideUp 0.4s ease forwards;
}

@keyframes pulse-teal {
    0%, 100% { box-shadow: 0 0 0 0 rgba(13,148,136,0.4); }
    50%       { box-shadow: 0 0 0 8px rgba(13,148,136,0); }
}

.pulse {
    animation: pulse-teal 2s infinite;
}

/* ── Welcome banner ───────────────────────────────────────────── */
.welcome-banner {
    background: linear-gradient(135deg, rgba(13,148,136,0.15) 0%, rgba(15,118,110,0.08) 100%);
    border: 1px solid rgba(13,148,136,0.2);
    border-radius: 18px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 12px;
}

/* ── Main title area ──────────────────────────────────────────── */
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(135deg, #f8fafc 30%, #14b8a6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}

.main-subtitle {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 0.3rem;
}

/* ── Symptom chip ─────────────────────────────────────────────── */
.symptom-chip {
    display: inline-block;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.3);
    color: #34d399;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 2px;
}

/* ── Hospital card ────────────────────────────────────────────── */
.hosp-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.75rem 1rem;
    background: rgba(15,23,42,0.7);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s ease;
}

.hosp-card:hover {
    border-color: rgba(13,148,136,0.4);
}

.hosp-num {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, var(--teal), var(--teal-dark));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
}

/* ── User avatar in sidebar ───────────────────────────────────── */
.user-avatar-box {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.75rem 0.9rem;
    background: rgba(13,148,136,0.1);
    border: 1px solid rgba(13,148,136,0.2);
    border-radius: 12px;
    margin-bottom: 0.5rem;
}

.avatar-circle {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, var(--teal), #f59e0b);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.9rem;
    color: white;
    flex-shrink: 0;
}

.avatar-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--ivory);
    line-height: 1.2;
}

.avatar-email {
    font-size: 0.7rem;
    color: var(--muted);
}

/* ── Auth page specific ───────────────────────────────────────── */
.auth-hero {
    text-align: center;
    margin-bottom: 2.5rem;
}

.auth-hero-icon {
    font-size: 3.5rem;
    margin-bottom: 0.75rem;
    display: block;
}

.auth-hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #f8fafc 20%, #14b8a6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}

.auth-hero-sub {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

.auth-card {
    background: rgba(22,33,50,0.9);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 2rem 2.25rem;
    backdrop-filter: blur(20px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

/* Feature badges on auth page */
.feature-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-top: 2rem;
}

.feature-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 0.85rem;
    background: rgba(15,23,42,0.7);
    border: 1px solid var(--border);
    border-radius: 12px;
}

.feature-icon {
    font-size: 1.2rem;
    margin-top: 1px;
    flex-shrink: 0;
}

.feature-text {
    font-size: 0.78rem;
    color: var(--muted);
    line-height: 1.4;
}

.feature-text strong {
    color: var(--ivory);
    display: block;
    font-size: 0.82rem;
    margin-bottom: 2px;
}

/* Disclaimer box */
.disclaimer-box {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.2);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    font-size: 0.78rem;
    color: #fbbf24;
    line-height: 1.5;
}

</style>
""", unsafe_allow_html=True)

# ===================================================================
# USER DATABASE (file-based for portability — swap with DB for prod)
# ===================================================================
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    return re.match(r"^[^@]+@[^@]+\.[^@]+$", email) is not None

def validate_password(password):
    return len(password) >= 6

def register_user(name, email, password):
    users = load_users()
    email = email.lower().strip()
    if email in users:
        return False, "An account with this email already exists."
    users[email] = {
        "name": name.strip(),
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.now().isoformat(),
    }
    save_users(users)
    return True, "Account created successfully!"

def login_user(email, password):
    users = load_users()
    email = email.lower().strip()
    if email not in users:
        return False, None, "No account found with this email."
    if users[email]["password"] != hash_password(password):
        return False, None, "Incorrect password."
    return True, users[email], "Welcome back!"


# ===================================================================
# SESSION STATE INIT
# ===================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"   # "login" | "signup"
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = get_qa_chain()
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "chat"
if "hospital_result" not in st.session_state:
    st.session_state.hospital_result = None


# ===================================================================
# HELPER FUNCTIONS  (all original logic preserved)
# ===================================================================
# ================================================================
# CHAT STORAGE FUNCTIONS
# ================================================================

def create_new_session():

    user_email = st.session_state.user_info["email"]

    session_id = create_chat_session(user_email)

    # Reload chats from JSON storage
    st.session_state.chat_sessions = load_user_chats(user_email)

    st.session_state.current_session_id = session_id

    return session_id

def get_current_messages():

    sid = st.session_state.current_session_id

    if sid and sid in st.session_state.chat_sessions:
        return st.session_state.chat_sessions[sid]["messages"]

    return []

def add_message(role, content, extra=None):

    sid = st.session_state.current_session_id

    if sid:

        user_email = st.session_state.user_info["email"]

        add_chat_message(
            user_email=user_email,
            session_id=sid,
            role=role,
            content=content,
            extra=extra
        )

        # Reload updated chats
        st.session_state.chat_sessions = load_user_chats(user_email)

def translate_to_en(text, source_lang="auto"):
    try:
        result = GoogleTranslator(source=source_lang, target="en").translate(text)
        if not result or not result.strip():
            return text, False
        return result.strip(), True
    except Exception as e:
        st.warning(f"⚠️ Could not translate input: {e}")
        return text, False

def translate_from_en(text, lang_code):
    if lang_code == "en":
        return text, True
    try:
        result = GoogleTranslator(source="en", target=lang_code).translate(text)
        if not result or not result.strip():
            return text, False
        return result.strip(), True
    except Exception as e:
        st.warning(f"⚠️ Could not translate answer: {e}")
        return text, False

GTTS_LANG_MAP = {"en": "en", "hi": "hi", "mr": "mr"}

def generate_tts(text, lang_code):
    gtts_lang = GTTS_LANG_MAP.get(lang_code, "en")
    audio_path = os.path.join(tempfile.gettempdir(), f"output_{int(time.time())}.mp3")
    try:
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(audio_path)
        return audio_path
    except Exception:
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(audio_path)
            return audio_path
        except:
            pass
    return None

def transcribe_audio(audio, lang_code="en"):
    sr_lang_map = {"en": "en-IN", "hi": "hi-IN", "mr": "mr-IN"}
    sr_language = sr_lang_map.get(lang_code, "en-IN")
    recognizer = sr.Recognizer()
    try:
        audio_bytes = io.BytesIO(audio["bytes"])
        sound = AudioSegment.from_file(audio_bytes)
        wav_path = os.path.join(tempfile.gettempdir(), f"mic_{int(time.time())}.wav")
        sound.export(wav_path, format="wav")
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=sr_language)
            return text
    except sr.UnknownValueError:
        st.error("Voice not clear, please try again.")
    except sr.RequestError as e:
        st.error(f"Speech recognition service error: {e}")
    except Exception as e:
        st.error(f"Audio processing error: {e}. Ensure ffmpeg is installed.")
    return ""

def geocode_city(query):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": 1}
        headers = {"User-Agent": "MediSenseAI/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", query)
        return None, None, None
    except:
        return None, None, None

def parse_sources(source_documents):
    sources = []
    seen = set()
    for doc in source_documents:
        meta = doc.metadata or {}
        source = meta.get("source", meta.get("file_path", "Unknown Document"))
        page = meta.get("page", None)
        snippet = doc.page_content.strip()[:300]
        source_name = os.path.basename(source) if source != "Unknown Document" else source
        key = f"{source_name}_{page}"
        if key not in seen:
            seen.add(key)
            sources.append({"source": source_name, "page": page, "snippet": snippet})
    return sources

def render_hospital_map(lat, lon, city, hospitals, map_key="hmap"):
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB dark_matter")
    folium.Marker(
        [lat, lon],
        tooltip="📍 You are here",
        popup="Your Location",
        icon=folium.Icon(color="blue", icon="home", prefix="fa")
    ).add_to(m)
    if hospitals:
        for h in hospitals:
            folium.Marker(
                [h["lat"], h["lon"]],
                tooltip=h["name"],
                popup=h["name"],
                icon=folium.Icon(color="red", icon="plus-sign")
            ).add_to(m)
    st_folium(m, width="100%", height=420, key=map_key)

def render_message(msg, index=0):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        extra = msg.get("extra", {})
        sources = extra.get("sources", [])
        if sources:
            with st.expander(f"📚 {len(sources)} Source(s) referenced"):
                for i, s in enumerate(sources):
                    page_info = f" — Page {s['page']}" if s["page"] is not None else ""
                    st.markdown(f"**📄 Source {i+1}:** `{s['source']}`{page_info}")
                    st.caption(f"*…{s['snippet']}…*")
                    if i < len(sources) - 1:
                        st.divider()
        if extra.get("symptoms"):
            st.markdown(f'<div class="symptom-chip">🧠 {extra["symptoms"]}</div>', unsafe_allow_html=True)
        if extra.get("audio_path") and os.path.exists(extra["audio_path"]):
            st.audio(extra["audio_path"])
        if extra.get("lang_used") and extra["lang_used"] != "en":
            st.caption(f"🌍 Translated to {extra['lang_used']}")


# ===================================================================
# AUTH PAGE  (shown when not logged in)
# ===================================================================
if not st.session_state.logged_in:

    # Centred layout using columns
    col_left, col_center, col_right = st.columns([1, 1.6, 1])
    with col_center:
        # Hero
        st.markdown("""
        <div class="auth-hero fade-in">
            <span class="auth-hero-icon">🩺</span>
            <h1 class="auth-hero-title">MediSense AI</h1>
            <p class="auth-hero-sub">Your intelligent medical companion — powered by AI</p>
        </div>
        """, unsafe_allow_html=True)

        # Tab toggle
        tab_col1, tab_col2, tab_col3 = st.columns([1, 2, 1])
        with tab_col2:
            mode = st.radio(
                "auth_mode",
                ["Sign In", "Create Account"],
                horizontal=True,
                label_visibility="collapsed",
                index=0 if st.session_state.auth_mode == "login" else 1,
                key="auth_tab_toggle"
            )
            st.session_state.auth_mode = "login" if mode == "Sign In" else "signup"

        st.markdown("")   # spacer

        # Auth card
        st.markdown('<div class="auth-card fade-in">', unsafe_allow_html=True)

        if st.session_state.auth_mode == "login":
            # ── LOGIN FORM ──────────────────────────────────────────
            st.markdown('<p class="section-label">Email Address</p>', unsafe_allow_html=True)
            login_email = st.text_input("email_login", placeholder="you@example.com", label_visibility="collapsed")

            st.markdown('<p class="section-label" style="margin-top:0.85rem">Password</p>', unsafe_allow_html=True)
            login_pass  = st.text_input("pass_login", placeholder="Enter your password", type="password", label_visibility="collapsed")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Sign In  →", use_container_width=True, type="primary", key="login_btn"):
                if not login_email or not login_pass:
                    st.error("Please fill in all fields.")
                elif not validate_email(login_email):
                    st.error("Please enter a valid email address.")
                else:
                    ok, user, msg = login_user(login_email, login_pass)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user

                        # LOAD PREVIOUS CHAT HISTORY
                        st.session_state.chat_sessions = load_user_chats(user["email"])

                        # LOAD LAST SESSION IF AVAILABLE
                        if st.session_state.chat_sessions:
                            latest_session = sorted(
                                st.session_state.chat_sessions.keys(),
                                reverse=True
                            )[0]

                            st.session_state.current_session_id = latest_session

                        st.success(f"✅ {msg}")
                        time.sleep(0.6)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                '<p style="text-align:center;color:var(--muted);font-size:0.82rem">'
                'Don\'t have an account? Switch to <strong>Create Account</strong> above.</p>',
                unsafe_allow_html=True
            )

        else:
            # ── SIGNUP FORM ─────────────────────────────────────────
            st.markdown('<p class="section-label">Full Name</p>', unsafe_allow_html=True)
            reg_name  = st.text_input("reg_name",  placeholder="Dr. Jane Smith", label_visibility="collapsed")

            st.markdown('<p class="section-label" style="margin-top:0.85rem">Email Address</p>', unsafe_allow_html=True)
            reg_email = st.text_input("reg_email", placeholder="you@example.com", label_visibility="collapsed")

            st.markdown('<p class="section-label" style="margin-top:0.85rem">Password</p>', unsafe_allow_html=True)
            reg_pass  = st.text_input("reg_pass",  placeholder="Minimum 6 characters", type="password", label_visibility="collapsed")

            st.markdown('<p class="section-label" style="margin-top:0.85rem">Confirm Password</p>', unsafe_allow_html=True)
            reg_pass2 = st.text_input("reg_pass2", placeholder="Re-enter your password", type="password", label_visibility="collapsed")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account  →", use_container_width=True, type="primary", key="signup_btn"):
                if not all([reg_name, reg_email, reg_pass, reg_pass2]):
                    st.error("Please fill in all fields.")
                elif not validate_email(reg_email):
                    st.error("Please enter a valid email address.")
                elif not validate_password(reg_pass):
                    st.error("Password must be at least 6 characters.")
                elif reg_pass != reg_pass2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(reg_name, reg_email, reg_pass)
                    if ok:
                        st.success(f"✅ {msg} Please sign in.")
                        time.sleep(1)
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        st.markdown('</div>', unsafe_allow_html=True)  # close auth-card

        # Feature grid
        st.markdown("""
        <div class="feature-grid fade-in" style="margin-top:1.5rem">
            <div class="feature-item">
                <span class="feature-icon">🔍</span>
                <div class="feature-text">
                    <strong>RAG-Powered</strong>
                    Answers from verified medical documents
                </div>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🌍</span>
                <div class="feature-text">
                    <strong>Multilingual</strong>
                    English, Hindi &amp; Marathi support
                </div>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🎤</span>
                <div class="feature-text">
                    <strong>Voice Input</strong>
                    Speak your health questions
                </div>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🏥</span>
                <div class="feature-text">
                    <strong>Hospital Finder</strong>
                    Locate nearby hospitals on map
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="disclaimer-box fade-in">
            ⚠️ <strong>Medical Disclaimer:</strong> MediSense AI provides information for educational
            purposes only and is <em>not</em> a substitute for professional medical advice,
            diagnosis, or treatment.
        </div>
        """, unsafe_allow_html=True)

    st.stop()


# ===================================================================
# SIDEBAR  (shown after login)
# ===================================================================
user = st.session_state.user_info
initials = "".join([w[0].upper() for w in user["name"].split()][:2])

with st.sidebar:
    # Brand
    st.markdown("""
    <div class="brand-logo">
        <span style="font-size:1.6rem">🩺</span>
        <div>
            <div class="brand-name">MediSense AI</div>
            <div class="brand-tagline">Intelligent Health Companion</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:0.75rem 0'>", unsafe_allow_html=True)

    # User avatar block
    st.markdown(f"""
    <div class="user-avatar-box">
        <div class="avatar-circle">{initials}</div>
        <div>
            <div class="avatar-name">{user["name"]}</div>
            <div class="avatar-email">{user["email"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:0.75rem 0'>", unsafe_allow_html=True)

    # Language
    st.markdown('<div class="section-label">🌍 Language</div>', unsafe_allow_html=True)
    lang = st.selectbox(
        "Language", ["English", "Hindi", "Marathi"],
        label_visibility="collapsed"
    )
    lang_map = {"English": "en", "Hindi": "hi", "Marathi": "mr"}
    selected_lang_code = lang_map[lang]

    st.markdown("<hr style='margin:0.75rem 0'>", unsafe_allow_html=True)

    # Action buttons
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
            create_new_session()
            st.session_state.active_tab = "chat"
            st.rerun()
    with col_b:
        if st.button("🏥 Hospitals", use_container_width=True, key="hosp_tab_btn"):
            st.session_state.active_tab = "hospital"
            st.session_state.hospital_result = None
            st.rerun()

    st.markdown("<hr style='margin:0.75rem 0'>", unsafe_allow_html=True)

    # Chat history
    # Chat history
    st.markdown(
        '<div class="section-label">💬 Chat History</div>',
        unsafe_allow_html=True
    )

    sessions = sorted(
        st.session_state.chat_sessions.items(),
        key=lambda x: x[0],
        reverse=True
    )

    for sid, session in sessions:

        is_active = (
            sid == st.session_state.current_session_id
            and st.session_state.active_tab == "chat"
        )

        col1, col2 = st.columns([5, 1])

        with col1:

            icon = "🟢" if is_active else "💬"

            if st.button(
                f"{icon} {session['title']}",
                key=f"btn_{sid}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):

                st.session_state.current_session_id = sid
                st.session_state.active_tab = "chat"

                st.rerun()

        with col2:

            if st.button(
                "🗑",
                key=f"del_{sid}",
                help="Delete session"
            ):

                delete_chat_session(user["email"], sid)

                st.session_state.chat_sessions = load_user_chats(
                    user["email"]
                )

                if st.session_state.current_session_id == sid:

                    remaining_sessions = list(
                        st.session_state.chat_sessions.keys()
                    )

                    if remaining_sessions:

                        st.session_state.current_session_id = sorted(
                            remaining_sessions,
                            reverse=True
                        )[0]

                    else:
                        st.session_state.current_session_id = None

                st.rerun()

    if not sessions:
        st.caption("No chats yet — click ➕ New Chat!")


# ===================================================================
# MAIN CONTENT AREA
# ===================================================================

# ── Page header ──────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem">
    <div>
        <h1 class="main-title">
            {"🏥 Hospital Finder" if st.session_state.active_tab == "hospital" else "🩺 Medical Assistant"}
        </h1>
        <p class="main-subtitle">
            {"Locate hospitals and clinics near you" if st.session_state.active_tab == "hospital"
             else f"Welcome back, {user['name'].split()[0]}! How can I help you today?"}
        </p>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
        <span class="stat-badge">🌍 {lang}</span>
        <span class="stat-badge">💬 {len(st.session_state.chat_sessions)} session(s)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────
# HOSPITAL TAB
# ────────────────────────────────────────────────────────────────────
if st.session_state.active_tab == "hospital":

    st.markdown("""
    <div class="medisense-card fade-in">
        <p style="margin:0;font-size:0.88rem;color:var(--muted)">
            Enter your <strong style="color:var(--ivory)">city, area, or full address</strong>
            to locate hospitals and clinics near you on the map.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col1:
        location_input = st.text_input(
            "location",
            placeholder="e.g.  Aurangabad, Maharashtra   or   Bandra, Mumbai",
            label_visibility="collapsed",
            key="hosp_location_input"
        )
    with col2:
        search_btn = st.button("🔍 Search", use_container_width=True, key="hosp_search_btn", type="primary")

    if search_btn:
        if not location_input.strip():
            st.error("Please enter a location first.")
        else:
            with st.spinner(f"📍 Locating '{location_input}'…"):
                lat, lon, display_name = geocode_city(location_input.strip())
            if lat and lon:
                with st.spinner("🏥 Searching for nearby hospitals…"):
                    hospitals = find_hospitals_osm(lat, lon, radius=5000)
                st.session_state.hospital_result = {
                    "lat": lat, "lon": lon,
                    "city": display_name,
                    "hospitals": hospitals
                }
            else:
                st.error(f"❌ Could not find **'{location_input}'**. Try a more specific name.")
                st.session_state.hospital_result = None

    if st.session_state.hospital_result:
        r = st.session_state.hospital_result

        # Summary cards
        found = r["hospitals"]
        c1, c2 = st.columns(2)
        c1.metric("📍 Location", r["city"][:50] + ("…" if len(r["city"]) > 50 else ""))
        c2.metric("🏥 Hospitals found", len(found))

        # Hospital list
        if found:
            st.markdown('<div class="section-label" style="margin-top:1rem">Nearby Hospitals</div>', unsafe_allow_html=True)
            for i, h in enumerate(found, 1):
                st.markdown(f"""
                <div class="hosp-card fade-in">
                    <div class="hosp-num">{i}</div>
                    <span style="font-size:0.88rem;font-weight:500">{h['name']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No hospitals found in this area. Try a broader location name.")

        # Map
        st.markdown('<div class="section-label" style="margin-top:1rem">Map View</div>', unsafe_allow_html=True)
        render_hospital_map(r["lat"], r["lon"], r["city"], found, map_key="hosp_main_map")

    st.stop()


# ────────────────────────────────────────────────────────────────────
# CHAT TAB
# ────────────────────────────────────────────────────────────────────
if st.session_state.current_session_id is None:

    if not st.session_state.chat_sessions:
        create_new_session()
        st.rerun()

    st.markdown("""
    <div class="medisense-card fade-in" style="text-align:center;padding:3rem 2rem">
        <div style="font-size:3rem;margin-bottom:1rem">💬</div>
        <h3 style="font-family:'Playfair Display',serif;margin:0 0 0.5rem">Select a Conversation</h3>
        <p style="color:var(--muted);margin:0;font-size:0.88rem">
            Choose a previous chat from sidebar or create a new one.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# Medical disclaimer (inline, compact)
st.markdown("""
<div class="disclaimer-box" style="margin-bottom:1rem;font-size:0.76rem">
    ⚠️ Educational purposes only — not a substitute for professional medical advice.
</div>
""", unsafe_allow_html=True)

# Render history
for i, msg in enumerate(get_current_messages()):
    render_message(msg, index=i)

# ── Voice Input ───────────────────────────────────────────────────────
st.markdown('<div class="section-label">🎤 Voice Input</div>', unsafe_allow_html=True)
audio = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="⏹ Stop", key="mic")
user_input = ""

if audio:
    with st.spinner("🎧 Transcribing voice…"):
        user_input = transcribe_audio(audio, lang_code=selected_lang_code)
    if user_input:
        st.toast(f"🎤 Heard: {user_input}")

# ── Text Input ────────────────────────────────────────────────────────
text_input = st.chat_input(
    "अपना स्वास्थ्य प्रश्न पूछें / आपला आरोग्य प्रश्न विचारा / Ask your health question…"
)
if text_input:
    user_input = text_input

# ── Process Query ─────────────────────────────────────────────────────
if user_input:
    add_message("user", user_input)
    with st.chat_message("user"):
        st.write(user_input)

    input_en, translated_ok = translate_to_en(user_input)
    if not translated_ok and selected_lang_code != "en":
        st.info("ℹ️ Using original text for search (translation unavailable).")

    with st.spinner("🔍 Searching medical documents…"):
        response = st.session_state.qa_chain.invoke({"query": input_en})

    answer_en      = response["result"]
    source_docs    = response.get("source_documents", [])
    parsed_sources = parse_sources(source_docs)

    answer, _ = translate_from_en(answer_en, selected_lang_code)
    audio_path = generate_tts(answer, selected_lang_code)
    symptoms   = extract_symptoms_llm(input_en)

    extra = {
        "sources":    parsed_sources,
        "symptoms":   symptoms if symptoms else None,
        "audio_path": audio_path,
        "lang_used":  selected_lang_code,
    }
    add_message("assistant", answer, extra=extra)

    with st.chat_message("assistant"):
        st.write(answer)

        if parsed_sources:
            with st.expander(f"📚 {len(parsed_sources)} Source(s) referenced"):
                for i, s in enumerate(parsed_sources):
                    page_info = f" — Page {s['page']}" if s["page"] is not None else ""
                    st.markdown(f"**📄 Source {i+1}:** `{s['source']}`{page_info}")
                    st.caption(f"*…{s['snippet']}…*")
                    if i < len(parsed_sources) - 1:
                        st.divider()

        if symptoms:
            chips = " ".join([f'<span class="symptom-chip">🧠 {s.strip()}</span>'
                               for s in symptoms.split(",") if s.strip()])
            st.markdown(chips, unsafe_allow_html=True)

        if audio_path and os.path.exists(audio_path):
            st.audio(audio_path)

        if selected_lang_code != "en":
            st.caption(f"🌍 Answer translated to {lang}")

        st.markdown("---")
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1:
            st.markdown(
                '<span style="font-size:0.85rem;color:var(--muted)">Need in-person care?</span>',
                unsafe_allow_html=True
            )
        with col_h2:
            if st.button("🏥 Find Hospital", key=f"goto_hosp_{int(time.time())}", type="primary"):
                st.session_state.active_tab = "hospital"
                st.session_state.hospital_result = None
                st.rerun()

    st.rerun()
