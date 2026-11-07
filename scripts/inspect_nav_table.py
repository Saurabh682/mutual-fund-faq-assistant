import io
import sys
from pdfminer.high_level import extract_text

sys.stdout.reconfigure(encoding='utf-8')

with open("scripts/nav_circular.txt", "w", encoding="utf-8") as out:
    import urllib.request
    url = "https://www.amfiindia.com/uploads/Reviewoftimelimitfordisclosureof_NAV_f5ebc65062.pdf"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        pdf_bytes = resp.read()
    text = extract_text(io.BytesIO(pdf_bytes))
    out.write(text)
    print("Done writing nav_circular.txt. Length:", len(text))
    for line in text.splitlines()[20:65]:
        print(line)
