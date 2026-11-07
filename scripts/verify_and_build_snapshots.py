import hashlib
import json
import os
import re
import urllib.request
from bs4 import BeautifulSoup

SNAPSHOTS_DIR = os.path.join("data", "snapshots")
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_text_from_html(html_bytes: bytes) -> str:
    html = html_bytes.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style", "noscript"]):
        s.extract()
    text = " ".join(soup.get_text().split())
    return text

print("Verifying and rebuilding snapshots...")
