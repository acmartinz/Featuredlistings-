import os
import fitz  # PyMuPDF for text extraction
import pytesseract
from pdf2image import convert_from_path
import re
import pandas as pd
from flask import Flask, render_template, request, send_file

app = Flask(__name__, template_folder="templates")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Updated regex pattern to ensure correct city + address extraction
ADDRESS_PATTERN = r"\b([A-Z][a-zA-Z\s]+)\s*\|\s*(\d{1,6}\s[\w\s]+(?:St\.?|Street|Ave\.?|Avenue|Dr\.?|Drive|Rd\.?|Road|Ln\.?|Lane|Blvd\.?|Boulevard|Way|Ct\.?|Court|Pl\.?|Place|Terrace|Circle|Pkwy|Highway|Loop|Trail|Square|Canyon|Valley|Hills))"

# Words to exclude from city names
EXCLUDE_WORDS = {"NEW LISTING", "PM", "AM", "BD", "BA", "LISTING", "OPEN", "TUESDAY", "MARCH", "WEB#", "$", "CAROLWOODRE.COM", "THEALTMANBROTHERS"}

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using PyMuPDF."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

def extract_text_with_ocr(pdf_path):
    """Extracts text from scanned PDFs using OCR (pytesseract)."""
    images = convert_from_path(pdf_path)
    text = "\n".join(pytesseract.image_to_string(img) for img in images)
    return text.strip()

def extract_addresses(pdf_path):
    """Extracts valid city-address pairs from a PDF while filtering out extra details."""
    
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        text = extract_text_with_ocr(pdf_path)

    # Normalize text to fix multi-line addresses
    text = text.replace("\n", " ")

    # Save extracted text for debugging
    with open("extracted_text_debug.txt", "w") as f:
        f.write(text)

    # Extract city-address pairs using regex
    matches = re.findall(ADDRESS_PATTERN, text, re.MULTILINE)

    extracted_data = []
    for city, address in matches:
        city = city.strip()
        address = address.strip()

        # Ensure address starts with a number
        if not address[0].isdigit():
            continue

        extracted_data.append({"City": city, "Address": address})

    return extracted_data, text  # Returns both structured addresses & raw text

@app.route("/", methods=["GET", "POST"])
def upload_file():
    addresses = []
    raw_text = ""

    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename.endswith(".pdf"):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # Extract addresses and raw text
            addresses, raw_text = extract_addresses(file_path)

            if not addresses:
                return render_template("upload.html", message="⚠️ No valid addresses found. Check extracted_text_debug.txt.", addresses=[], raw_text=raw_text)

    return render_template("upload.html", addresses=addresses, raw_text=raw_text)
@app.route("/download_csv", methods=["POST"])
def download_csv():
    """Generate and download the CSV file with only addresses (excluding city names)."""
    selected_addresses = request.form.getlist("selected_addresses")  # Get user-selected addresses

    csv_path = os.path.join(UPLOAD_FOLDER, "selected_addresses.csv")
    data = []

    for item in selected_addresses:
        if " | " in item:  # Ensure correct format before splitting
            _, address = item.split(" | ", 1)  # Extract only the address part
            data.append({"Address": address.strip()})  # Save address only
        else:
            print(f"⚠️ Skipping malformed entry: {item}")  # Debugging log

    if data:
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return send_file(csv_path, as_attachment=True)

    return "⚠️ No valid addresses selected for download."
if __name__ == "__main__":
    print("Current working directory:", os.getcwd())
    print("Templates folder exists:", os.path.exists("templates/upload.html"))
    app.run(debug=True)