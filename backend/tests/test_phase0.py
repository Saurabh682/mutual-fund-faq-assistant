import os
import yaml
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app

client = TestClient(app)

def test_settings_loaded():
    assert settings.PORT == 8000
    assert settings.GROQ_MODEL in ["qwen/qwen3.8-27b", "llama-3.3-70b-versatile"]
    assert len(settings.GROQ_API_KEY) > 0
    assert os.path.exists(settings.DATA_DIR)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["llm_provider"] == "groq"
    assert data["llm_model"] in ["qwen/qwen3.8-27b", "llama-3.3-70b-versatile"]
    assert data["schemes_count"] == 5

def test_meta_endpoint():
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    data = response.json()
    assert data["disclaimer"] == "Facts-only. No investment advice."
    assert len(data["starter_questions"]) == 3
    assert len(data["schemes"]) == 5

def test_corpus_manifest_strictly_5_groww_urls():
    manifest_path = os.path.join(settings.DATA_DIR, "corpus_manifest.yaml")
    assert os.path.exists(manifest_path)
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
        
    expected_urls = {
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth"
    }
    
    source_urls = {s["url"] for s in manifest["sources"]}
    assert source_urls == expected_urls, f"Manifest must contain strictly the 5 Groww URLs. Found: {source_urls}"
    assert manifest["allowed_domains"] == ["groww.in"]
    assert len(manifest["schemes"]) == 5

def test_playwright_installed():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        version = browser.version
        browser.close()
    assert len(version) > 0
