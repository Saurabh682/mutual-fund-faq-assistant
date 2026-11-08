import re

CLAUSE_SPLIT_PATTERN = re.compile(
    r"(?:[?;]+\s*(?:also\s+)?|\s+(?:and|but|also)\s+(?=(?:should|can|could|would|will|is|are|do|does|did|how|what|why|who|where|tell|suggest|recommend|advise|give|help)\b|[a-z0-9\s-]+\b(?:invest|buy|sell|redeem|outperform|grow|beat|switch|pick|choose)\b))",
    re.I
)

def split_clauses_v2(query: str):
    parts = CLAUSE_SPLIT_PATTERN.split(query.strip())
    clean_parts = []
    for p in parts:
        c = p.strip()
        c = re.sub(r"^[,\s;?]+|[,\s;?]+$", "", c)
        c = re.sub(r"^(?:also|and|but)\s+", "", c, flags=re.I).strip()
        if c:
            clean_parts.append(c)
    return clean_parts

test_cases = [
    # Should NOT split on "and":
    ("What is the TER and exit load of Small Cap", ["What is the TER and exit load of Small Cap"]),
    ("What is the expense ratio and minimum SIP for HDFC Mid Cap?", ["What is the expense ratio and minimum SIP for HDFC Mid Cap"]),
    ("Explain the difference between Direct and Regular plans", ["Explain the difference between Direct and Regular plans"]),
    ("HDFC Silver ETF FoF and gold comparison", ["HDFC Silver ETF FoF and gold comparison"]),
    ("What is the NAV and AUM of HDFC Top 100?", ["What is the NAV and AUM of HDFC Top 100"]),
    
    # SHOULD split into fact + advice:
    ("What is the TER of HDFC Mid Cap and should I invest in it?", ["What is the TER of HDFC Mid Cap", "should I invest in it"]),
    ("What is the exit load for HDFC Small Cap Fund, but is it a good time to buy?", ["What is the exit load for HDFC Small Cap Fund", "is it a good time to buy"]),
    ("What is HDFC Top 100 NAV? Also will it outperform Nifty 50?", ["What is HDFC Top 100 NAV", "will it outperform Nifty 50"]),
    ("What is the minimum SIP for HDFC Multi Cap Fund and how much will 5000 grow to in 5 years?", ["What is the minimum SIP for HDFC Multi Cap Fund", "how much will 5000 grow to in 5 years"]),
    ("What is the riskometer of HDFC Silver ETF FoF? Can you guarantee capital safety?", ["What is the riskometer of HDFC Silver ETF FoF", "Can you guarantee capital safety"]),
]

all_passed = True
for q, expected in test_cases:
    actual = split_clauses_v2(q)
    if actual != expected:
        print(f"FAILED on '{q}'")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        all_passed = False
    else:
        print(f"PASSED: '{q[:40]}...' -> {actual}")

if all_passed:
    print("\nALL CLAUSE SPLITTING TESTS PASSED!")
