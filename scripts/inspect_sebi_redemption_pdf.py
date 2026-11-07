import urllib.request
import io
import sys
from pdfminer.high_level import extract_text

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.sebi.gov.in/sebi_data/attachdocs/nov-2022/1669373687117.pdf"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        pdf_bytes = resp.read()
    print("PDF bytes:", len(pdf_bytes))
    text = extract_text(io.BytesIO(pdf_bytes))
    print("PDF text length:", len(text))
    print("Content:\n", text[:2000])
except Exception as e:
    print("Error:", e)
