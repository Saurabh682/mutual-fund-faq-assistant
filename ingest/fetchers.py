import os
import json
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def check_domain_allowlist(url: str, allowed_domains: list[str]) -> bool:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return any(domain == d.lower() or domain.endswith("." + d.lower()) for d in allowed_domains)

def fetch_groww_scheme(url: str, cache_dir: str, scheme_id: str, force_refresh: bool = False) -> dict:
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{scheme_id}.json")

    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, timeout=40000, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        html_content = page.content()
        browser.close()

    soup = BeautifulSoup(html_content, "html.parser")
    next_data_script = soup.find("script", id="__NEXT_DATA__")
    next_data = {}
    if next_data_script and next_data_script.string:
        try:
            full_json = json.loads(next_data_script.string)
            next_data = full_json.get("props", {}).get("pageProps", {}).get("mfServerSideData", {})
        except Exception:
            next_data = {}

    content_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
    fetched_at = datetime.utcnow().strftime("%Y-%m-%d")

    result = {
        "url": url,
        "scheme_id": scheme_id,
        "html": html_content,
        "next_data": next_data,
        "content_hash": content_hash,
        "fetched_at": fetched_at
    }

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    return result
