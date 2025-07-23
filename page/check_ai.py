# file: page/ai_checker.py

import streamlit as st
import tempfile
import os
import time
from ollama_ai import OllamaAI

# Ana çalışma fonksiyonu (başka yerden çağırılabilir)
def run_ai_checker():
    # Tema ayarı
    st.set_page_config(page_title="🧠AI Checker", layout="wide")

    # Özel tema CSS
    st.markdown("""
    <style>
    body {
        background-color: #121212;
        color: #e0e0e0;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #1a1a1a;
    }
    h1, h2, h3, h4 {
        color: #ff0033;
    }
    .stSpinner {
        color: #ff0033 !important;
    }
    div.stButton > button {
        background-color: transparent;
        color: #ff0033;
        border: 2px solid #ff0033;
        padding: 10px;
        font-weight: bold;
        border-radius: 10px;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #ff0033;
        color: black;
    }
    code {
        background-color: #1e1e1e !important;
        color: #ff5c5c !important;
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("AI Checker")

    THRESHOLD_SCORE = 50
    ai = OllamaAI()

    uploaded_file = st.file_uploader("🔼 Karşılaştırmak istediğiniz Sigma YAML dosyasını yükleyin", type=["yaml", "yml"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yml") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        st.success("✅ YAML dosyası başarıyla yüklendi.")

        if st.button("🚀 Karşılaştırmayı Başlat"):
            with st.spinner("🧠 AI destekli karşılaştırma yapılıyor..."):
                try:
                    rule_from_file = ai.load_yaml(tmp_path)
                    rules = ai.fetch_latest_rules(limit=50)

                    benzer_kurallar = []

                    st.markdown("---")
                    st.subheader("📊 Karşılaştırma Sonuçları")

                    for idx, rule in enumerate(rules, 1):
                        result = ai.compare_rules_with_ai(rule_from_file, rule)
                        score = result["score"]
                        title = rule.get("title", f"Kural #{idx}")

                        if score >= THRESHOLD_SCORE:
                            benzer_kurallar.append((score, title, result["explanation"]))

                        st.markdown(f"**{idx}. Kural:** `{title}`")
                        st.markdown(f"- 🔺 **Benzerlik Skoru:** `{score}/100`")

                        if score >= THRESHOLD_SCORE:
                            st.markdown("**🧠 AI Açıklaması:**")
                            st.code(result["explanation"], language="markdown")
                            st.code(result["rule1"], language="yaml")
                            st.code(result["rule2"], language="yaml")

                        st.markdown("---")
                        time.sleep(0.5)

                    if not benzer_kurallar:
                        st.warning("⚠️ 50 puanın üzerinde benzer kural bulunamadı.")
                    else:
                        st.success(f"✅ Toplam {len(benzer_kurallar)} benzer kural bulundu.")

                except Exception as e:
                    st.error(f"❌ Hata oluştu: {e}")