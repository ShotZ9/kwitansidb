from PIL import Image
import pytesseract
import re
import io
import cv2
import numpy as np
from pdf2image import convert_from_bytes

def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text

def extract_info(file):
    # Convert PDF to image if needed
    if file.type == "application/pdf":
        images = convert_from_bytes(file.read())
        image = images[0]
    else:
        image = Image.open(file)

    # Ekstraksi teks
    text = extract_text_from_image(image)

    # Ekstrak jumlah uang
    amount_match = re.search(r'Rp[ .]*([\d.,]+)', text)
    amount = amount_match.group(1) if amount_match else "Tidak ditemukan"

    # Ekstrak nama (contoh: nama setelah kata 'Kepada' atau 'Dari')
    name_match = re.search(r'(Kepada|Dari|Untuk):?\s*([A-Za-z ]+)', text)
    name = name_match.group(2).strip() if name_match else "Tidak ditemukan"

    # Ekstrak logo (asumsi logo di kiri atas)
    # open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    # h, w, _ = open_cv_image.shape
    # logo_crop = open_cv_image[0:int(h * 0.2), 0:int(w * 0.2)]  # kiri atas
    # logo_pil = Image.fromarray(cv2.cvtColor(logo_crop, cv2.COLOR_BGR2RGB))
    w, h = image.size
    logo_crop = image.crop((0, 0, int(w * 0.2), int(h * 0.2)))

    return logo_pil, name, amount
