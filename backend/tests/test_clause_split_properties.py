"""Property tests verifying clause splitting behavior under strict SEBI compliance.

Invariants:
1. Coordinated noun phrases ("TER and exit load", "Direct and Regular", "Silver FoF and gold")
   MUST stay intact as a single clause without spurious splitting.
2. Mixed factual-plus-advisory queries where conjunctions ('and', 'but', 'also') introduce
   actionable advisory/recommendation verbs MUST split cleanly into constituent clauses.
"""

import pytest
from app.guardrails.intent import split_clauses


PROPERTY_CASES = [
    # 5 Coordinated phrases that must stay a single clause (len == 1)
    ("TER and exit load", 1),
    ("Direct and Regular plans", 1),
    ("Silver FoF and gold", 1),
    ("NAV and AUM of HDFC Top 100", 1),
    ("minimum SIP and exit load", 1),
    # 5 Compound queries with advisory second clauses that must split (len >= 2)
    ("What is the TER of HDFC Mid Cap and should I invest in it?", 2),
    ("Tell me the NAV of HDFC Top 100 but can I sell?", 2),
    ("What is the AUM of HDFC Small Cap and will it grow?", 2),
    ("What is the exit load for HDFC Multi Cap and would you recommend it?", 2),
    ("Tell me the benchmark of HDFC Silver FoF also should I switch?", 2),
]


@pytest.mark.parametrize("query,expected_min_clauses", PROPERTY_CASES)
def test_clause_splitting_properties(query: str, expected_min_clauses: int):
    """Asserts that coordinated noun phrases do not split, and advisory suffixes do split."""
    clauses = split_clauses(query)
    print(f"\nINPUT: '{query}' -> CLAUSES: {clauses} (count: {len(clauses)})")

    if expected_min_clauses == 1:
        assert len(clauses) == 1, f"Expected 1 clause for '{query}', got {clauses}"
    else:
        assert len(clauses) >= 2, f"Expected >= 2 clauses for '{query}', got {clauses}"
