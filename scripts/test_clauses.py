import sys
sys.path.insert(0, "backend")

from app.guardrails.intent import classify_intent

clauses = [
    "will it outperform large cap funds",
    "can you guarantee capital safety",
    "tell me if it is a good buy today",
    "rank the 5 HDFC schemes for me",
    "do you recommend starting an SIP",
    "is this the right time to sell",
    "will it deliver 15% CAGR",
    "which is better",
    "should I invest",
    "how much will it grow",
]

for c in clauses:
    res = classify_intent(c)
    print(f"'{c}': intent={res.intent} | is_refusal={res.is_refusal} | triggers={res.matched_triggers}")
