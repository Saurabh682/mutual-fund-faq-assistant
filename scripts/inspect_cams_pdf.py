import urllib.request
import io
import sys
from pdfminer.high_level import extract_text

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.camsonline.com/assets/PDF/Revision_in_timelines-equity_payout.pdf"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        pdf_bytes = resp.read()
    print("PDF bytes:", len(pdf_bytes))
    text = extract_text(io.BytesIO(pdf_bytes))
    print("PDF text length:", len(text))
    print("Content:\n", text)
except Exception as e:
    print("Error:", e)
