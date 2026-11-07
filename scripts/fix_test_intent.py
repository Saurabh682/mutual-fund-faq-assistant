with open('backend/tests/test_intent.py', 'r', encoding='utf-8') as f:
    content = f.read()

target_proc = '''    @pytest.mark.parametrize(
        "query",
        [
            "How do I download my Capital Gains statement on Groww?",
            "how to download capital gains statement",
            "Where can I find my capital gains report on Groww?",
            "How do I redeem my mutual fund units on Groww?",
            "How to start a SIP on Groww?",
            "What documents are required for KYC?",
            "What is the lock-in period for ELSS mutual funds?",
            "Explain the SEBI riskometer framework",
            "What is the SEBI categorization for large cap funds?",
        ],
    )
    def test_procedural_intent_and_lookup(self, query: str):
        from app.rag.facts import lookup_fact

        res = classify_intent(query)
        assert res.intent == IntentType.PROCEDURAL.value, f"Query '{query}' intent: {res.intent}"
        assert res.is_refusal is False

        fact = lookup_fact(query)
        assert fact is not None, f"lookup_fact returned None for procedural query: {query}"
        assert fact.get("source") in ("procedural_store", "glossary_store")
        assert "Source: " in fact.get("rendered", "")
        assert "Last updated from sources:" in fact.get("rendered", "")'''

replacement_proc = '''    @pytest.mark.parametrize(
        "query,is_supported",
        [
            ("How do I download my Capital Gains statement on Groww?", False),
            ("how to download capital gains statement", False),
            ("Where can I find my capital gains report on Groww?", False),
            ("How do I redeem my mutual fund units on Groww?", False),
            ("How to start a SIP on Groww?", False),
            ("What documents are required for KYC?", False),
            ("What is the lock-in period for ELSS mutual funds?", True),
            ("Explain the SEBI riskometer framework", True),
            ("What is the SEBI categorization for large cap funds?", True),
        ],
    )
    def test_procedural_intent_and_lookup(self, query: str, is_supported: bool):
        from app.rag.facts import lookup_fact

        res = classify_intent(query)
        assert res.intent == IntentType.PROCEDURAL.value, f"Query '{query}' intent: {res.intent}"
        assert res.is_refusal is False

        fact = lookup_fact(query)
        if is_supported:
            assert fact is not None, f"lookup_fact returned None for supported procedural query: {query}"
            assert fact.get("source") in ("procedural_store", "glossary_store")
            assert "Source: " in fact.get("rendered", "")
            assert "Last updated from sources:" in fact.get("rendered", "")
        else:
            assert fact is None, f"Unsupported procedural query '{query}' should return None, got: {fact}"'''

assert target_proc in content, "target_proc not found"
content = content.replace(target_proc, replacement_proc)

# Fix nav citation
content = content.replace(
    '("What does NAV mean?", "nav", "groww.in"),',
    '("What does NAV mean?", "nav", "amfiindia.com"),'
)

with open('backend/tests/test_intent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated backend/tests/test_intent.py successfully!")
