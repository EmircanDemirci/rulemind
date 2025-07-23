import streamlit as st
import tempfile
import time
from mongodb_connection import MongoConnector
from similarity_algorithm import SigmaRuleComparator
from dotenv import load_dotenv
import os

load_dotenv()

def run_streamlit_sigma_ui(mongo_url="mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/", db_name="sigmaDB", collection_name="rules"):
    st.set_page_config(page_title="Similarity Check", layout="wide")
    st.title("Similarity Check")

    # Dosya yükleme
    uploaded_file = st.file_uploader("🔼 Sigma YAML dosyası yükleyin", type=["yaml", "yml"])

    # Text area ile doğrudan YAML girme
    st.markdown("📝 Alternatif olarak YAML içeriğini aşağıya yapıştırabilirsiniz:")
    yaml_text_input = st.text_area("YAML İçeriği", height=250)

    file_provided = uploaded_file is not None
    text_provided = yaml_text_input.strip() != ""

    tmp_path = None

    if text_provided:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yml", mode="w", encoding="utf-8") as tmp:
            tmp.write(yaml_text_input)
            tmp_path = tmp.name
        st.success("✅ YAML içeriği başarıyla işlendi.")
    elif file_provided:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yml") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        st.success("✅ YAML dosyası başarıyla yüklendi.")

    if tmp_path and st.button("🚀 Karşılaştırmayı Başlat"):
        with st.spinner("🧠 Karşılaştırma yapılıyor..."):
            try:
                connector = MongoConnector(mongo_url, db_name, collection_name)
                collection = connector.connect()
                comparator = SigmaRuleComparator(collection)
                results = comparator.compare_with_mongodb(tmp_path, top_n=10)

                if not results:
                    st.warning("⚠️ 50 puanın üzerinde benzer kural bulunamadı.")
                else:
                    st.success(f"✅ Toplam {len(results)} benzer kural bulundu.")
                    st.markdown("---")
                    st.subheader("📊 En Benzer Kurallar")

                    for idx, match in enumerate(results, 1):
                        st.markdown(f"**{idx}. Kural:** `{match['title']}`")
                        st.markdown(f"- 📊 Toplam Benzerlik: `{match['weighted_similarity']:.1%}`")
                        st.markdown(f"- 🔤 Value Benzerliği: `{match['value_similarity']:.1%}`")
                        st.markdown(f"- 🏷️ Field Benzerliği: `{match['field_similarity']:.1%}`")

                        with st.expander("📂 Detaylar"):
                            st.code(f"Fields: {match['mongo_fields']}")
                            st.code(f"Values: {match['mongo_values'][:5]}...")
                            if 'full_rule' in match:
                                st.code(match['full_rule'], language="yaml")

                        st.markdown("---")
                        time.sleep(0.3)

            except Exception as e:
                st.error(f"❌ Hata oluştu: {e}")
