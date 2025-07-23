import streamlit as st
from create_a_sigma_rule import SigmaRuleGenerator 

def run_sigma_creator_page():
    st.set_page_config(page_title="✍️ Sigma Kural Oluştur", layout="wide")
    st.title("✍️ Sigma Kuralı Oluşturma")

    st.markdown("Belirli bir güvenlik davranışı fikrine göre Sigma kuralı oluşturmak için aşağıya fikri yazın.")

    idea_input = st.text_area("💡 Fikir Girin", 
        placeholder="Örn: PowerShell ile base64 kodlu komut çalıştırılması",
        height=200)

    if st.button("🚀 Kuralı Oluştur"):
        if idea_input.strip() == "":
            st.warning("Lütfen bir fikir girin.")
        else:
            with st.spinner("🧠 Sigma kuralı AI ile oluşturuluyor..."):
                try:
                    generator = SigmaRuleGenerator()
                    rule = generator.generate(idea_input)
                    st.success("✅ Sigma kuralı başarıyla oluşturuldu.")
                    st.code(rule, language="yaml")
                except Exception as e:
                    st.error(f"❌ Hata oluştu: {e}")
