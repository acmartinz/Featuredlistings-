import os
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import re
import pandas as pd
from flask import Flask, render_template, request, send_file

# Setup tesseract path if needed (adjust for your system)

pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"  # or /usr/local/bin/tesseract
app = Flask(__name__, template_folder="templates")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Regex for city and address
ADDRESS_PATTERN = r"\d{4,6}\s[A-Z\s]+(?:DRIVE|ROAD|STREET|HWY|AVENUE|PLACE|LANE|BLVD|TERRACE|COURT|CIRCLE|WAY|CANYON|COLONY|COAST|TRAIL|GLEN|HILLSIDE|MILLER|PORT|RD|ST|DR|LN|PL|CT|HWY|BLVD|ROAD|MALIBU|PACIFIC|ELLLICE|BROAD BEACH|WILDLIFE)"
EXCLUDE_WORDS = {"NEW LISTING", "PM", "AM", "BD", "BA", "LISTING", "OPEN", "TUESDAY", "MARCH", "WEB#", "$", "CAROLWOODRE.COM", "THEALTMANBROTHERS"}

def extract_text_from_pdf(pdf_path):
    """Text extraction via PyMuPDF"""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

def extract_text_with_ocr(pdf_path):
    """Fallback OCR if no text is found"""
    images = convert_from_path(pdf_path)
    return "\n".join(pytesseract.image_to_string(img) for img in images)


def extract_addresses(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        text = extract_text_with_ocr(pdf_path)

    text = text.replace("\n", " ")

    with open("extracted_text_debug.txt", "w") as f:
        f.write(text)

    # NEW: just extract street addresses from all caps format
    matches = re.findall(ADDRESS_PATTERN, text, re.IGNORECASE)

    clean_list = list(set(match.strip().title() for match in matches if match.strip()))
    structured = [{"City": "", "Address": addr} for addr in clean_list]

    return structured, clean_list, text

@app.route("/", methods=["GET", "POST"])
def upload_file():
    structured_addresses = []
    plain_address_list = []
    raw_text = ""

    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename.endswith(".pdf"):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            structured_addresses, plain_address_list, raw_text = extract_addresses(file_path)

            if not plain_address_list:
                return render_template("upload.html", message="⚠️ No addresses found. Check extracted_text_debug.txt.")

    return render_template("upload.html", addresses=structured_addresses, copy_list=plain_address_list, raw_text=raw_text)

@app.route("/download_csv", methods=["POST"])
def download_csv():
    selected_addresses = request.form.getlist("selected_addresses")
    csv_path = os.path.join(UPLOAD_FOLDER, "selected_addresses.csv")
    data = []

    for item in selected_addresses:
        if " | " in item:
            _, address = item.split(" | ", 1)
            data.append({"Address": address.strip()})
        else:
            print(f"⚠️ Skipping malformed entry: {item}")

    if data:
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return send_file(csv_path, as_attachment=True)

    return "⚠️ No valid addresses selected for download."

if __name__ == "__main__":
    app.run(debug=True)
