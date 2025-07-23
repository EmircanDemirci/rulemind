import streamlit as st
from page.Home import run_home
from page.check_ai import run_ai_checker
from page.similarity import run_streamlit_sigma_ui
from page.sigma_rule import run_sigma_creator_page
from page.sigtospl import run_sigma_to_splunk_converter

st.set_page_config(page_title="RuleMind", layout="wide")

# 🎨 Koyu Tema - Özel CSS
st.markdown("""
<style>
body {
    background-color: #121212;
    color: #ffffff;
}

[data-testid="stAppViewContainer"] {
    background-color: #1e1e1e;
}

[data-testid="stSidebar"] {
    background-color: #121212;
    padding-top: 30px;
}

.stButton > button {
    width: 100% !important;
    padding: 12px 20px;
    margin: 8px 0;
    border-radius: 10px;
    background-color: transparent;
    border: 2px solid #b00020;
    color: #b00020;
    font-weight: 600;
    font-size: 18px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background-color: #b00020;
    color: white;
}

.stButton > button:focus {
    outline: none;
    box-shadow: 0 0 8px 2px #b00020;
}

h1, h2, h3, h4, h5, h6, p, div, span {
    color: #e0e0e0;
}
</style>
""", unsafe_allow_html=True)

# 🧭 Sidebar Logo + Sayfa Seçimi
st.sidebar.markdown("# RuleMind", unsafe_allow_html=True)
st.sidebar.image("./media/logo.png", width=150)

# 📄 Sayfa Seçim Durumu
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Overview"

def set_page(page):
    st.session_state.selected_page = page

# 📑 Sayfa Listesi
pages = {
    "Overview": run_home,
    "AI Checker": run_ai_checker,
    "Similarity Check": run_streamlit_sigma_ui,
    "Create a Sigma Rule": run_sigma_creator_page,
    "Sigma to Splunk" : run_sigma_to_splunk_converter
}

# 🎛️ Sidebar Butonları
for page_name in pages:
    if st.sidebar.button(page_name):
        set_page(page_name)

# 🖥️ Seçilen Sayfanın Çalıştırılması
selected_func = pages.get(st.session_state.selected_page)
if selected_func:
    selected_func()
else:
    st.error("⚠️ Sayfa bulunamadı.")
