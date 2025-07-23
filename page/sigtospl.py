import streamlit as st
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
import yaml
import requests
from datetime import datetime

def send_to_n8n_and_save(sigma_rule_text):
    webhook_url = "http://localhost:5678/webhook-test/ca8c3573-28d7-4145-a186-a8af119e9e4a"
    receive_api_url = "http://localhost:5000/receive"

    if 'timestamp' not in st.session_state:
        st.session_state.timestamp = datetime.now().isoformat()

    payload = {
        "sigma_rule": sigma_rule_text,
        "timestamp": st.session_state.timestamp,
        "user_action": "sigma_conversion_request"
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        converted_query = (
            result.get("converted_query", "") or
            result.get("spl_query", "") or
            result.get("query", "") or
            ""
        )

        second_payload = {
            "spl_query": converted_query,
            "timestamp": st.session_state.timestamp,
            "source": "n8n_webhook"
        }

        system_response = requests.post(receive_api_url, json=second_payload, timeout=10)
        system_response.raise_for_status()

        if converted_query:
            return True, "✅ n8n'den dönen sonuç sistemine başarıyla gönderildi!", converted_query
        else:
            return True, "⚠️ n8n'den veri alındı ancak sorgu boş.", ""

    except Exception as e:
        return False, f"❌ Hata: {str(e)}", ""

def get_latest_data():
    try:
        response = requests.get("http://localhost:5000/latest", timeout=5)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"❌ Bağlantı hatası: {str(e)}"

def run_sigma_to_splunk_converter():
    st.set_page_config(page_title="Sigma to Splunk", layout="wide")
    st.title("🧪 Sigma → Splunk Query Converter")
    st.markdown("""
    <style>
    .stTextArea textarea {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #555;
    }
    .stTextInput input {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .stCodeBlock {
        background-color: #2e2e2e;
        border-radius: 10px;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='color: #b00020; font-weight: bold;'>by venoox</div>", unsafe_allow_html=True)

    if 'timestamp' not in st.session_state:
        st.session_state.timestamp = datetime.now().isoformat()

    sigma_input = st.text_area("📄 Sigma Kuralını Yapıştır", height=300, help="YAML formatında Sigma kuralını buraya yapıştırın")

    col1, col2, col3 = st.columns(3)

    with col1:
        convert_locally = st.button("🔄 Yerel Splunk Query Oluştur")
    with col2:
        send_to_n8n_btn = st.button("📤 n8n'e Gönder")
    with col3:
        show_latest = st.button("📊 Son SPL Query'i Göster")

    if convert_locally:
        if not sigma_input.strip():
            st.warning("⚠️ Lütfen bir Sigma kuralı girin.")
        else:
            try:
                sigma_dict = yaml.safe_load(sigma_input)
                if not sigma_dict:
                    st.error("❌ Geçersiz YAML formatı.")
                    return
                sigma_rule = SigmaRule.from_dict(sigma_dict)
                collection = SigmaCollection([sigma_rule])
                backend = SplunkBackend()
                queries = backend.convert(collection)
                st.success("✅ Sigma kuralı başarıyla Splunk sorgusuna dönüştürüldü!")
                for i, query in enumerate(queries, 1):
                    st.subheader(f"🔍 Splunk Query {i}:")
                    st.code(query, language='splunk')
                    st.text_area(f"📋 Kopyala (Query {i})", value=query, height=100, key=f"copy_area_{i}")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")

    if send_to_n8n_btn:
        if not sigma_input.strip():
            st.warning("⚠️ Lütfen bir Sigma kuralı girin.")
        else:
            with st.spinner("n8n'e gönderiliyor..."):
                success, message, converted_query = send_to_n8n_and_save(sigma_input)
                if success:
                    st.success(message)
                    if converted_query:
                        st.subheader("🔍 n8n’den Dönüşümlü Splunk Query:")
                        st.code(converted_query, language="splunk")
                        st.text_area("📋 Kopyala", value=converted_query, height=100, key="n8n_copy_area")
                else:
                    st.error(message)

    if show_latest:
        with st.spinner("Son SPL Query getiriliyor..."):
            latest_query = get_latest_data()
            if latest_query.startswith("❌"):
                st.error(latest_query)
            else:
                st.success("✅ Son SPL Query başarıyla getirildi!")
                st.subheader("📊 Son SPL Query:")
                st.code(latest_query, language="splunk")
                st.text_area("📋 Kopyala", value=latest_query, height=100, key="latest_copy_area")

if __name__ == "__main__":
    run_sigma_to_splunk_converter()
