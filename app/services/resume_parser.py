import pymupdf as fitz
from pathlib import Path

def extract_text_from_pdf(pdf_path) -> str:
    extracted_text = []
    document = fitz.open(stream=Path(pdf_path).read_bytes(), filetype="pdf")
    try:
        for page in document:
            page_text = page.get_text()
            if page_text:
                extracted_text.append(page_text)
    finally:
        document.close()
    return "\n".join(extracted_text)
