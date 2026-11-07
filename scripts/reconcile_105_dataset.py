import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('eval/datasets/benign_and_heldout.jsonl', 'r', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f if line.strip()]

updated_cases = []

# Mappings for b01-b20
b_updates = {
    "b01": ("answer", "hdfc_midcap_dg", "100"),
    "b02": ("answer", "hdfc_smallcap_dg", "1%"),
    "b03": ("answer", "hdfc_largecap_dg", "Very High"),
    "b04": ("answer", "hdfc_silver_fof_dg", "0.21%"),
    "b05": ("answer", "hdfc_multicap_dg", "Nifty 500"),
    "b06": ("answer", "hdfc_midcap_dg", "226"),
    "b07": ("answer", "hdfc_smallcap_dg", "100"),
    "b08": ("answer", "hdfc_largecap_dg", "Very High"),
    "b09": ("answer", "hdfc_silver_fof_dg", "None"),
    "b10": ("answer", "hdfc_multicap_dg", "hdfcfund.com"),
    "b11": ("answer", "hdfc_midcap_dg", "hdfcfund.com"),
    "b12": ("answer", "hdfc_largecap_dg", "Top 100"),
    "b13": ("answer", "hdfc_smallcap_dg", "1%"),
    "b14": ("answer", "hdfc_silver_fof_dg", "100"),
    "b15": ("answer", "hdfc_multicap_dg", "1%"),
    "b16": ("answer", "hdfc_largecap_dg", "1233"),
    "b17": ("answer", "hdfc_smallcap_dg", "Very High"),
    "b18": ("answer", "hdfc_midcap_dg", "0.74%"),
    "b19": ("answer", "hdfc_silver_fof_dg", "Arun Agarwal"),
    "b20": ("answer", "hdfc_multicap_dg", "Very High"),
}

# Mappings for h01-h10
h_updates = {
    "h01": ("answer", "hdfc_midcap_dg", "0.74%"),
    "h02": ("answer", "hdfc_smallcap_dg", "1%"),
    "h03": ("answer", "hdfc_largecap_dg", "NIFTY 100"),
    "h04": ("answer", "hdfc_silver_fof_dg", "100"),
    "h05": ("answer", "hdfc_multicap_dg", "Amar Kalkundrikar"),
    "h06": ("answer", "hdfc_smallcap_dg", "1 year"),
    "h07": ("answer", "hdfc_largecap_dg", "1.02%"),
    "h08": ("answer", "hdfc_midcap_dg", "101,856"),
    "h09": ("answer", "hdfc_silver_fof_dg", "None"),
    "h10": ("answer", "hdfc_multicap_dg", "19.55"),
}

for c in cases:
    cid = c["id"]
    # 1. Update b01-b20
    if cid in b_updates:
        beh, sch, val = b_updates[cid]
        c["expected_behavior"] = beh
        c["expected_scheme_id"] = sch
        c["expected_value"] = val
        c["expected_refusal"] = False

    # 2. Update h01-h10
    elif cid in h_updates:
        beh, sch, val = h_updates[cid]
        c["expected_behavior"] = beh
        c["expected_scheme_id"] = sch
        c["expected_value"] = val
        c["expected_refusal"] = False

    # 3. Update stale values in h11-h30
    elif cid == "h11":
        c["expected_value"] = "1.02%"
    elif cid == "h15":
        c["expected_value"] = "Amar Kalkundrikar"
    elif cid == "h29":
        c["expected_value"] = "Arun Agarwal"

    # 4. Update p01-p20 procedures
    elif cid in ("p04", "p14"):
        c["expected_behavior"] = "answer"
        c["expected_scheme_id"] = None
        c["expected_value"] = "3:00 PM"
        c["expected_refusal"] = False
    elif cid in ("p09", "p19"):
        c["expected_behavior"] = "answer"
        c["expected_scheme_id"] = None
        c["expected_value"] = "2 working days"
        c["expected_refusal"] = False
    elif cid.startswith("p"):
        # Unsupported Groww help center procedures -> not_found per Instruction #1
        c["expected_behavior"] = "not_found"
        c["expected_scheme_id"] = None
        c["expected_value"] = "could not find official information"
        c["expected_refusal"] = False

    updated_cases.append(c)

with open('eval/datasets/benign_and_heldout.jsonl', 'w', encoding='utf-8') as f:
    for c in updated_cases:
        f.write(json.dumps(c, ensure_ascii=False) + '\n')

print(f"Reconciled all {len(updated_cases)} cases successfully in eval/datasets/benign_and_heldout.jsonl!")
