with open('backend/tests/test_static_contract.py', 'r', encoding='utf-8') as f:
    content = f.read()

test_date_logic = """

class TestDateLogic:
    \"\"\"Verifies date normalization and ISO footer format enforcement across facts and static responses.\"\"\"

    def test_normalize_date_footer_iso(self):
        from app.guardrails.validator import normalize_date_footer
        assert normalize_date_footer("2026-11-05") == "2026-11-05"
        assert normalize_date_footer("2025-10-23") == "2025-10-23"

    def test_normalize_date_footer_text(self):
        from app.guardrails.validator import normalize_date_footer
        assert normalize_date_footer("23-Oct-2026") == "2026-10-23"
        assert normalize_date_footer("05-Nov-2026") == "2026-11-05"

    def test_normalize_date_footer_fallback(self):
        from app.guardrails.validator import normalize_date_footer
        assert normalize_date_footer(None) == "2026-11-05"
        assert normalize_date_footer("") == "2026-11-05"

    def test_validate_response_date_footer_match(self):
        from app.guardrails.validator import validate_response
        res = validate_response("This is a factual response.", None, "https://groww.in/test", "2026-10-23")
        assert res.last_updated == "2026-10-23"
        assert "Last updated from sources: 2026-10-23" in res.rendered
"""

if "class TestDateLogic:" not in content:
    content += test_date_logic
    with open('backend/tests/test_static_contract.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added TestDateLogic successfully!")
else:
    print("TestDateLogic already present!")
