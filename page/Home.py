import streamlit as st

def run_home():
    st.set_page_config(layout="wide")

    st.markdown("""
    <style>
    /* Sayfa genel tema */
    body {
        background-color: #121212;
        color: #ffffff;
    }

    /* Ana container */
    [data-testid="stAppViewContainer"] {
        background-color: #1e1e1e;
        color: #e0e0e0;
        font-family: 'Courier New', monospace;
    }

    /* Terminal yazı efekti */
    .hacker-header {
        font-size: 40px;
        color: #00ff00;
        font-weight: bold;
        letter-spacing: 2px;
        text-shadow: 0 0 5px #00ff00, 0 0 10px #00ff00;
        animation: blink 1s infinite;
        margin-bottom: 20px;
    }

    @keyframes blink {
        0% {opacity: 1;}
        50% {opacity: 0.6;}
        100% {opacity: 1;}
    }

    /* Paragraf */
    .description-text {
        font-size: 20px;
        color: #f54257;
        background-color: #00000010;
        padding: 20px;
        border-left: 5px solid #ff0033;
        border-radius: 8px;
        margin-bottom: 30px;
    }

    /* Kutulu açıklama */
    .box {
        background-color: #2a2a2a;
        border: 1px solid #444;
        padding: 20px;
        border-radius: 10px;
        margin-top: 10px;
    }

    </style>
    """, unsafe_allow_html=True)

    # Başlık
    st.markdown('<div class="hacker-header">RuleMind v1.0</div>', unsafe_allow_html=True)


    # Açıklama
    st.markdown("""
    <div class="description-text">
    💀 <strong>Sigma Rule Similarity Engine</strong><br><br>
    Bu sistem, oluşturduğun yeni Sigma kurallarını <em>anlık olarak analiz eder</em>, daha önce yazılmış yüzlerce kural arasından <strong>en benzerlerini</strong> tespit eder.
    <br><br>
    Yinelenen kural yazımını önler, güvenlik analistlerinin iş yükünü azaltır ve gelecekte <span style="color: #fff;">AI destekli öneri sistemleri</span> için zemin hazırlar.
    </div>
    """, unsafe_allow_html=True)

    # Özellik kutuları
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="box">
        🧠 <strong>AI Assisted</strong><br>
        Ollama & LLM desteği ile kuralın diğer kurallarla mantıksal benzerliği analiz edilir.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="box">
        🔍 <strong>Multi-Layer Similarity</strong><br>
        Detection logic + field + value analizleri ile çok boyutlu karşılaştırma.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="box">
        🚀 <strong>Real-time Matching</strong><br>
        MongoDB'deki kurallar ile anlık karşılaştırma ve skor hesaplama.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="box">
        🛡️ <strong>Sigma Rule Creator</strong><br>
        İstediğin özellikteki bir sigma kuralını yapay zeka destekli sistem ile saniyeler içinde yarat!
        </div>
        """, unsafe_allow_html=True)
