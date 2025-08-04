import streamlit as st
import pytesseract
import cv2
import sqlite3
import numpy as np
from PIL import Image
import tempfile
import re
import os

# Konfigurasi jika di Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Ganti sesuai path

# === Fungsi bantu ===
def load_image(image_file):
    img = Image.open(image_file)
    return img

def extract_text(image: Image.Image):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return pytesseract.image_to_string(img_cv)

def extract_amount(text: str):
    match = re.findall(r'Rp[\s\.]*([\d\.]+)', text, re.IGNORECASE)
    if match:
        try:
            return float(match[0].replace(".", "").replace(",", "."))
        except:
            return None
    return None

def extract_name(text: str):
    lines = text.strip().split("\n")
    for line in lines:
        if len(line.strip()) > 5 and not re.search(r'\d', line):
            return line.strip()
    return None

def match_to_database(name: str, amount: float, db_path="receipts.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM receipts WHERE name LIKE ? AND ABS(amount - ?) < 1", (f"%{name}%", amount))
    result = cur.fetchall()
    conn.close()
    return result

# === Streamlit UI ===
st.set_page_config(page_title="Ekstraksi Kwitansi", layout="centered")
st.title("📤 Upload Kwitansi & Ekstrak Informasi")

uploaded_file = st.file_uploader("Unggah gambar kwitansi (.jpg, .png)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = load_image(uploaded_file)
    st.image(img, caption="Gambar Kwitansi", use_column_width=True)

    with st.spinner("🔍 Mengekstrak teks..."):
        text_result = extract_text(img)
        extracted_name = extract_name(text_result)
        extracted_amount = extract_amount(text_result)

    st.subheader("📑 Hasil Ekstraksi")
    st.text_area("Teks OCR:", value=text_result, height=150)
    st.write("**Nama yang Dideteksi:**", extracted_name or "❌ Tidak ditemukan")
    st.write("**Jumlah Uang:**", f"Rp {extracted_amount:,.0f}" if extracted_amount else "❌ Tidak ditemukan")

    if extracted_name and extracted_amount:
        st.subheader("🔗 Pencocokan Database")
        results = match_to_database(extracted_name, extracted_amount)

        if results:
            st.success(f"✅ Ditemukan {len(results)} hasil di database:")
            for row in results:
                st.write(f"- ID: {row[0]}, Nama: {row[1]}, Jumlah: Rp {row[2]:,.0f}")
        else:
            st.warning("⚠️ Tidak ditemukan data yang cocok di database.")

