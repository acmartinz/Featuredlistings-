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

# Fixed regex to handle multi-line city-address formats
ADDRESS_PATTERN = r"([A-Za-z\s]+)\s\|\s(\d{1,6}\s[\w\s]+(?:Boulevard|Street|Avenue|Drive|Road|Lane|Trail|Highway|Pkwy|Ct|Pl|Way|Canyon|Valley|Hills|Square))"

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
    """Extracts city and addresses from a PDF using regex."""
    text = extract_text_from_pdf(pdf_path)

    # If no text is found, use OCR as a fallback
    if not text.strip():
        text = extract_text_with_ocr(pdf_path)

    # Save extracted text for debugging
    debug_text_path = "extracted_text_debug.txt"
    with open(debug_text_path, "w") as f:
        f.write(text)

    # Extract city and addresses
    matches = re.findall(ADDRESS_PATTERN, text, re.MULTILINE)

    if not matches:
        print("⚠️ No addresses found! Check extracted_text_debug.txt for issues.")
    else:
        print(f"✅ Extracted {len(matches)} addresses successfully!")
        for match in matches:
            print(f"City: {match[0]} | Address: {match[1]}")

    # Convert extracted matches to a list of dictionaries
    extracted_data = [{"City": city.strip(), "Address": address.strip()} for city, address in matches]

    return extracted_data  # Returns list of dictionaries with City & Address

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename.endswith(".pdf"):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # Extract addresses
            addresses = extract_addresses(file_path)
            csv_path = os.path.join(UPLOAD_FOLDER, "extracted_addresses.csv")

            if addresses:
                # Save to CSV with City and Address columns
                df = pd.DataFrame(addresses)
                df.to_csv(csv_path, index=False)
                return send_file(csv_path, as_attachment=True)
            else:
                return "⚠️ No addresses found. Check 'extracted_text_debug.txt' for issues."

    return render_template("upload.html")

if __name__ == "__main__":
    print("Current working directory:", os.getcwd())
    print("Templates folder exists:", os.path.exists("templates/upload.html"))
    app.run(debug=True)