import pdfplumber

def parse_pdf_tables(pdf_path: str) -> list[dict]:
    """Extracts tables and text from PDF documents using pdfplumber."""
    extracted = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                extracted.append({
                    "page": page_idx + 1,
                    "text": text,
                    "tables": tables
                })
    except Exception as e:
        print(f"Error parsing PDF {pdf_path}: {e}")
    return extracted
