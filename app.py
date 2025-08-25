import streamlit as st
import sqlite3
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv
import os

# ==== Konfigurasi API ====
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ==== Fungsi Gemini untuk ekstraksi kwitansi ====
def extract_receipt_info(pil_image):
    prompt = """
    Berikut adalah gambar kwitansi. Tolong ekstrak informasi berikut (jika ada):
    1. Nama toko atau penerima
    2. Logo (jika dapat dikenali, sebutkan nama brand/logo)
    3. Jumlah total uang dalam format Rupiah (contoh: Rp 120.000)

    Jawaban dalam format JSON seperti ini:
    {
      "nama": "...",
      "logo": "...",
      "jumlah": "..."
    }
    """

    try:
        response = model.generate_content(
            [prompt, pil_image],
            generation_config={"temperature": 0.2}
        )
        return response.text
    except Exception as e:
        return f"ERROR: {e}"

# ==== Setup database SQLite ====
def setup_db():
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logo TEXT,
            name TEXT,
            amount TEXT
        )
    """)
    # Tambah data dummy
    cursor.execute("INSERT OR IGNORE INTO receipts (id, logo, name, amount) VALUES (1, 'tokopedia', 'Tokopedia', 'Rp 123.000')")
    conn.commit()
    return conn

def check_match(conn, logo, name, amount):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM receipts WHERE logo=? AND name=? AND amount=?
    """, (logo, name, amount))
    return cursor.fetchone()

# ==== UI Streamlit ====
st.set_page_config(page_title="Ekstraksi Kwitansi LLM", layout="centered")
st.title("📄 Ekstraksi Kwitansi")

uploaded = st.file_uploader("Unggah gambar kwitansi (jpeg/png)", type=["jpg", "jpeg", "png"])

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption="Kwitansi yang Diunggah", use_container_width=True)

    with st.spinner("🔍 Mengekstrak..."):
        result_text = extract_receipt_info(image)

    st.subheader("📤 Hasil Ekstraksi:")
    st.code(result_text, language="json")

    if not result_text.startswith("ERROR"):
        import json
        import re
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        try:
            parsed = json.loads(json_match.group())
            logo = parsed.get("logo", "Tidak ditemukan")
            name = parsed.get("nama", "Tidak ditemukan")
            amount = parsed.get("jumlah", "Tidak ditemukan")

            st.write(f"**Logo**: {logo}")
            st.write(f"**Nama**: {name}")
            st.write(f"**Jumlah Uang**: {amount}")

            conn = setup_db()
            match = check_match(conn, logo, name, amount)

            if match:
                st.success("✅ Kecocokan ditemukan di database!")
            else:
                st.warning("❌ Tidak ada kecocokan di database.")

            if st.button("💾 Tambah ke Database"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO receipts (logo, name, amount) VALUES (?, ?, ?)", (logo, name, amount))
                conn.commit()
                st.success("📥 Data berhasil ditambahkan ke database.")
        except json.JSONDecodeError:
            st.error("❌ Format JSON tidak valid atau tidak bisa dibaca.")
    else:
        st.error(result_text)
