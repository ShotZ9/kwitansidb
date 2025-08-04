import streamlit as st
import pytesseract
import cv2
import sqlite3
import numpy as np
from PIL import Image
import re
import os

# === Fungsi bantu ===
def load_image(image_file):
    img = Image.open(image_file)
    return img

def extract_text(image: Image.Image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    st.image(thresh, caption="🔍 Gambar Threshold (OCR Input)", use_container_width=True, channels="GRAY")

    return pytesseract.image_to_string(thresh)

def extract_amount_from_image(image: Image.Image):
    img = np.array(image)
    h, w = img.shape[:2]
    cropped = img[int(h*0.65):h, int(w*0.5):w]

    gray = cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    st.image(thresh, caption="🧾 Area Jumlah Uang (Cropped)", use_container_width=True, channels="GRAY")

    text = pytesseract.image_to_string(thresh)
    match = re.search(r'[\d\.,]+', text)
    if match:
        try:
            raw = match.group(0).replace(".", "").replace(",", ".")
            return float(raw)
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

def detect_logo_name(image: Image.Image, template_dir="assets/logo", threshold=0.8):
    img_rgb = np.array(image.convert("RGB"))
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    for filename in os.listdir(template_dir):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        template_path = os.path.join(template_dir, filename)
        template = cv2.imread(template_path, 0)
        if template is None:
            continue

        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        if max_val >= threshold:
            return os.path.splitext(filename)[0]
    return None

# === Streamlit UI ===
st.set_page_config(page_title="Ekstraksi Kwitansi", layout="centered")
st.title("📤 Upload Kwitansi & Ekstrak Informasi")

uploaded_file = st.file_uploader("Unggah gambar kwitansi (.jpg, .png)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = load_image(uploaded_file)
    st.image(img, caption="🖼️ Gambar Kwitansi", use_container_width=True)

    with st.spinner("🔍 Mengekstrak informasi..."):
        text_result = extract_text(img)
        extracted_name = extract_name(text_result)
        extracted_amount = extract_amount_from_image(img)
        detected_logo = detect_logo_name(img)

    st.subheader("📑 Hasil Ekstraksi")
    st.text_area("📄 Hasil OCR (seluruh gambar):", value=text_result, height=150)

    st.write("**🏷️ Nama yang Dideteksi:**", extracted_name or "❌ Tidak ditemukan")
    st.write("**💰 Jumlah Uang:**", f"Rp {extracted_amount:,.0f}" if extracted_amount else "❌ Tidak ditemukan")
    if detected_logo:
        st.write("**🏢 Logo Terdeteksi:**", detected_logo)

    # Manual override
    st.markdown("### ✏️ Koreksi Manual (Opsional)")
    manual_name = st.text_input("Nama pengirim (jika OCR salah):", value=extracted_name or "")
    manual_amount = st.number_input("Jumlah uang (jika OCR salah):", value=extracted_amount or 0.0, step=1000.0)

    if st.button("🔍 Cocokkan ke Database"):
        if manual_name and manual_amount:
            results = match_to_database(manual_name, manual_amount)

            st.subheader("🔗 Pencocokan Database")
            if results:
                st.success(f"✅ Ditemukan {len(results)} hasil:")
                for row in results:
                    st.write(f"- ID: {row[0]}, Nama: {row[1]}, Jumlah: Rp {row[2]:,.0f}")
            else:
                st.warning("⚠️ Tidak ditemukan data yang cocok di database.")
        else:
            st.error("❌ Nama dan jumlah harus diisi untuk pencocokan.")
