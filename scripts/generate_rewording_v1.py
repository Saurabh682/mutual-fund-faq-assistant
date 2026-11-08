"""Generates 50 reworded in-corpus questions from facts.db and static definitions.

Covers all 5 HDFC schemes and verified static entries. Uses deterministic templates
with natural paraphrases, colloquial aliases, and common typographical variations.
Saves to eval/datasets/rewording_v1.jsonl (FROZEN).
"""

import json
from pathlib import Path

OUT_FILE = Path("eval/datasets/rewording_v1.jsonl")

# 50 Curated rewordings covering all 5 schemes + static procedures/glossary
ITEMS = [
    # --- Scheme Facts: HDFC Top 100 (1-9) ---
    {"id": "rw01", "query": "what is the expense ratio of hdfc top 100 direct", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "ter", "expected_value": "0.80%"},
    {"id": "rw02", "query": "how much exit load for hdfc top 100 fund", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "exit_load", "expected_value": "1%"},
    {"id": "rw03", "query": "mincimum sip amount for hdfc top 100", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "min_sip", "expected_value": "₹100"},
    {"id": "rw04", "query": "tell me hdfc top 100 current nav price", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "nav", "expected_value": "1233"},
    {"id": "rw05", "query": "what is the fund size of hdfc top 100 direct growth", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "aum", "expected_value": "37,298"},
    {"id": "rw06", "query": "who is the portfolio manager of hdfc top 100", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "fund_manager", "expected_value": "Rahul Baijal"},
    {"id": "rw07", "query": "which benchmark index does hdfc top 100 track", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "benchmark", "expected_value": "NIFTY 100"},
    {"id": "rw08", "query": "what risk level is shown on hdfc top 100 riskometer", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "riskometer", "expected_value": "Very High"},
    {"id": "rw09", "query": "is there any lockin period in hdfc top 100", "expected_behavior": "answer", "expected_scheme_id": "hdfc_largecap_dg", "expected_field": "lock_in", "expected_value": "Nil"},

    # --- Scheme Facts: HDFC Mid-Cap Opportunities (10-18) ---
    {"id": "rw10", "query": "what is the total charges or ter of hdfc midcap", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "ter", "expected_value": "0.74%"},
    {"id": "rw11", "query": "exit load schedule for hdfc mid cap opportunities direct", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "exit_load", "expected_value": "1%"},
    {"id": "rw12", "query": "starting sip amount for hdfc mid-cap opp", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "min_sip", "expected_value": "₹100"},
    {"id": "rw13", "query": "nav of hdfc midcap opportunities direct plan", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "nav", "expected_value": "199"},
    {"id": "rw14", "query": "how much total aum does hdfc mid cap manage", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "aum", "expected_value": "75,417"},
    {"id": "rw15", "query": "who manages hdfc midcap opportunities fund currently", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "fund_manager", "expected_value": "Chirag Setalvad"},
    {"id": "rw16", "query": "what is the official benchmark of hdfc mid-cap", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "benchmark", "expected_value": "NIFTY Midcap 150"},
    {"id": "rw17", "query": "sebi riskometer score for hdfc midcap opportunities", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "riskometer", "expected_value": "Very High"},
    {"id": "rw18", "query": "does hdfc mid cap fund have mandatory lock in duration", "expected_behavior": "answer", "expected_scheme_id": "hdfc_midcap_dg", "expected_field": "lock_in", "expected_value": "Nil"},

    # --- Scheme Facts: HDFC Small Cap (19-27) ---
    {"id": "rw19", "query": "how much is charged as ter in hdfc small cap direct", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "ter", "expected_value": "0.68%"},
    {"id": "rw20", "query": "what is the redemption fee for hdfc smallcap if sold in 1 year", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "exit_load", "expected_value": "1%"},
    {"id": "rw21", "query": "lowest monthly sip allowed in hdfc small cap scheme", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "min_sip", "expected_value": "₹100"},
    {"id": "rw22", "query": "tell me latest nav unit price for hdfc small cap", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "nav", "expected_value": "153"},
    {"id": "rw23", "query": "what is the corpus size of hdfc smallcap direct growth", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "aum", "expected_value": "35,161"},
    {"id": "rw24", "query": "who runs hdfc small cap fund", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "fund_manager", "expected_value": "Chirag Setalvad"},
    {"id": "rw25", "query": "target index tracked by hdfc smallcap fund", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "benchmark", "expected_value": "BSE 250 SmallCap"},
    {"id": "rw26", "query": "riskometer category of hdfc small cap fund", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "riskometer", "expected_value": "Very High"},
    {"id": "rw27", "query": "lock in period of hdfc small cap fund direct", "expected_behavior": "answer", "expected_scheme_id": "hdfc_smallcap_dg", "expected_field": "lock_in", "expected_value": "Nil"},

    # --- Scheme Facts: HDFC Multi Cap (28-36) ---
    {"id": "rw28", "query": "expense ratio direct growth for hdfc multicap fund", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "ter", "expected_value": "0.78%"},
    {"id": "rw29", "query": "what is exit load on hdfc multicap if redeemed within 12 months", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "exit_load", "expected_value": "1%"},
    {"id": "rw30", "query": "min sip investment for hdfc multi cap direct", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "min_sip", "expected_value": "₹100"},
    {"id": "rw31", "query": "hdfc multicap current net asset value", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "nav", "expected_value": "18"},
    {"id": "rw32", "query": "total asset size for hdfc multi-cap fund", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "aum", "expected_value": "16,812"},
    {"id": "rw33", "query": "portfolio managers handling hdfc multi cap", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "fund_manager", "expected_value": "Gopal Agrawal"},
    {"id": "rw34", "query": "what is benchmark index for hdfc multi cap", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "benchmark", "expected_value": "NIFTY 500 Multicap"},
    {"id": "rw35", "query": "risk level for hdfc multi cap scheme", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "riskometer", "expected_value": "Very High"},
    {"id": "rw36", "query": "is there lock in duration for hdfc multi cap", "expected_behavior": "answer", "expected_scheme_id": "hdfc_multicap_dg", "expected_field": "lock_in", "expected_value": "Nil"},

    # --- Scheme Facts: HDFC Silver ETF FoF (37-43) ---
    {"id": "rw37", "query": "what is direct expense ratio of hdfc silver etf fof", "expected_behavior": "answer", "expected_scheme_id": "hdfc_silver_fof_dg", "expected_field": "ter", "expected_value": "0.25%"},
    {"id": "rw38", "query": "exit load for hdfc silver fof if sold after 15 days", "expected_behavior": "answer", "expected_scheme_id": "hdfc_silver_fof_dg", "expected_field": "exit_load", "expected_value": "Nil"},
    {"id": "rw39", "query": "minimum sip installment in hdfc silver fof", "expected_behavior": "answer", "expected_scheme_id": "hdfc_silver_fof_dg", "expected_field": "min_sip", "expected_value": "₹100"},
    {"id": "rw40", "query": "current nav for hdfc silver etf fof direct", "expected_behavior": "answer", "expected_scheme_id": "hdfc_silver_fof_dg", "expected_field": "nav", "expected_value": "13"},
    {"id": "rw41", "query": "what benchmark index does hdfc silver etf fund of fund track", "expected_behavior": "answer", "expected_scheme_id": "hdfc_silver_fof_dg", "expected_field": "benchmark", "expected_value": "Silver"},
    {"id": "rw42", "query": "who manages hdfc silver etf fof", "expected_behavior": "answer", "expected_scheme_id": "hdfc_silver_fof_dg", "expected_field": "fund_manager", "expected_value": "Bhagyesh Kagalkar"},
    {"id": "rw43", "query": "is there any lock-in in hdfc silver fof", "expected_behavior": "answer", "expected_scheme_id": "hdfc_silver_fof_dg", "expected_field": "lock_in", "expected_value": "Nil"},

    # --- Static Glossary & Procedures (44-50) ---
    {"id": "rw44", "query": "what is systematic investment plan", "expected_behavior": "answer", "expected_scheme_id": None, "expected_field": "sip", "expected_value": "Systematic Investment Plan"},
    {"id": "rw45", "query": "what does nav mean in mutual funds", "expected_behavior": "answer", "expected_scheme_id": None, "expected_field": "nav", "expected_value": "Net Asset Value"},
    {"id": "rw46", "query": "define total expense ratio", "expected_behavior": "answer", "expected_scheme_id": None, "expected_field": "ter", "expected_value": "Total Expense Ratio"},
    {"id": "rw47", "query": "how to complete kyc for investing", "expected_behavior": "answer", "expected_scheme_id": None, "expected_field": "kyc", "expected_value": "KYC"},
    {"id": "rw48", "query": "how do i download my capital gains statement", "expected_behavior": "answer", "expected_scheme_id": None, "expected_field": "capital_gains", "expected_value": "Capital Gains"},
    {"id": "rw49", "query": "how can i pause my active sip on groww", "expected_behavior": "answer", "expected_scheme_id": None, "expected_field": "pause_sip", "expected_value": "pause"},
    {"id": "rw50", "query": "what is cutoff time for mutual fund orders", "expected_behavior": "answer", "expected_scheme_id": None, "expected_field": "cutoff", "expected_value": "cut-off"},
]


def generate():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for item in ITEMS:
            f.write(json.dumps(item) + "\n")
    print(f"Generated {len(ITEMS)} frozen rewording evaluation cases to {OUT_FILE}")


if __name__ == "__main__":
    generate()
