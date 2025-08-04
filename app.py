import streamlit as st
from extract import extract_info
from match import match_with_db

st.set_page_config(page_title="📄 Kwitansi Extractor", layout="wide")

st.title("📤 Sistem Ekstraksi Kwitansi")

uploaded_file = st.file_uploader("Unggah gambar atau PDF kwitansi", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    with st.spinner("🔍 Mengekstrak informasi..."):
        logo, name, amount = extract_info(uploaded_file)
    
    st.success("✅ Ekstraksi selesai!")
    
    st.subheader("📌 Hasil Ekstraksi:")
    st.write(f"**Nama:** {name}")
    st.write(f"**Jumlah Uang:** {amount}")
    if logo:
        st.image(logo, caption="Logo yang terdeteksi", width=150)

    st.subheader("🔗 Pencocokan dengan Database:")
    result = match_with_db(name, amount)
    if result:
        st.success("🎯 Kecocokan ditemukan di database!")
        st.json(result)
    else:
        st.error("❌ Tidak ditemukan kecocokan di database.")
