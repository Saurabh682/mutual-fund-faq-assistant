"""AMC Factsheet PDF parser — independent source for scheme facts.

Drop PDFs in data/factsheets/. This parser is a no-op if none exist.
Never overwrites facts (the Groww-sourced data). Writes to facts_amc table only.
"""
import os
import re
import sqlite3
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

FACTSHEETS_DIR = Path("data/factsheets")
DB_PATH = Path("data/index/facts.db")

SCHEME_NAME_MAP = {
    "top100": "hdfc_largecap_dg",
    "midcap": "hdfc_midcap_dg",
    "smallcap": "hdfc_smallcap_dg",
    "multicap": "hdfc_multicap_dg",
    "silver_fof": "hdfc_silver_fof_dg",
}


@dataclass
class AMCFact:
    scheme_id: str
    field: str
    value: str
    source_pdf: str
    page_number: Optional[int]
    as_of_date: Optional[str]  # from document itself


def create_facts_amc_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS facts_amc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id TEXT NOT NULL,
            field TEXT NOT NULL,
            value TEXT NOT NULL,
            source_pdf TEXT NOT NULL,
            page_number INTEGER,
            as_of_date TEXT,
            ingested_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def extract_facts_from_pdf(pdf_path: Path) -> list[AMCFact]:
    """Extract scheme facts from a single PDF.
    Returns empty list if pdfplumber not available.
    Never invents values.
    """
    try:
        import pdfplumber
    except ImportError:
        print(f"pdfplumber not installed — skipping {pdf_path.name}")
        return []

    # Detect scheme from filename
    name = pdf_path.stem.lower()
    scheme_id = None
    for key, sid in SCHEME_NAME_MAP.items():
        if key in name:
            scheme_id = sid
            break
    if not scheme_id:
        print(f"Cannot detect scheme from filename {pdf_path.name} — skipping")
        return []

    facts: list[AMCFact] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            page_texts: list[tuple[int, str]] = []
            for i, page in enumerate(pdf.pages):
                t = page.extract_text() or ""
                page_texts.append((i + 1, t))
                full_text += t + "\n"

            # Extract as_of date (look for "As on" or "As of" date in text)
            as_of_date = None
            m = re.search(
                r"As\s+(?:on|of)\s+(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{4}|\d{4}-\d{2}-\d{2})",
                full_text,
                re.I,
            )
            if m:
                as_of_date = m.group(1).strip()

            # TER (Direct Plan)
            ter_m = re.search(
                r"(?:Total\s+Expense\s+Ratio|TER)[^\n]*Direct[^\n]*?(\d+\.\d+)\s*%",
                full_text,
                re.I,
            )
            if not ter_m:
                ter_m = re.search(
                    r"(?:Direct\s+Plan)[^\n]*(?:TER|Expense\s+Ratio)[^\n]*?(\d+\.\d+)\s*%",
                    full_text,
                    re.I,
                )
            if ter_m:
                # Find page
                val = ter_m.group(1) + "%"
                pg = next((pn for pn, pt in page_texts if ter_m.group(0) in pt), None)
                facts.append(AMCFact(scheme_id, "ter", val, pdf_path.name, pg, as_of_date))

            # Exit Load
            el_m = re.search(r"Exit\s+Load[^\n]*?(\d+(?:\.\d+)?)\s*%", full_text, re.I)
            if el_m:
                val = el_m.group(1) + "%"
                pg = next((pn for pn, pt in page_texts if el_m.group(0) in pt), None)
                facts.append(AMCFact(scheme_id, "exit_load", val, pdf_path.name, pg, as_of_date))

            # Minimum SIP
            sip_m = re.search(
                r"Minimum\s+(?:SIP|Installment)[^\n]*?(?:Rs\.?\s*|₹\s*)(\d[\d,]+)",
                full_text,
                re.I,
            )
            if sip_m:
                val = "₹" + sip_m.group(1).replace(",", "")
                pg = next((pn for pn, pt in page_texts if sip_m.group(0) in pt), None)
                facts.append(AMCFact(scheme_id, "minimum_sip", val, pdf_path.name, pg, as_of_date))

            # Riskometer
            risk_m = re.search(
                r"Riskometer[^\n]*?(Very\s+High|High|Moderately\s+High|Moderate|Moderately\s+Low|Low)",
                full_text,
                re.I,
            )
            if risk_m:
                val = risk_m.group(1).strip()
                pg = next((pn for pn, pt in page_texts if risk_m.group(0) in pt), None)
                facts.append(AMCFact(scheme_id, "riskometer", val, pdf_path.name, pg, as_of_date))

            # Benchmark
            bench_m = re.search(r"Benchmark[^\n]*?:(.*?)(?:\n|$)", full_text, re.I)
            if bench_m:
                val = bench_m.group(1).strip()[:100]
                pg = next((pn for pn, pt in page_texts if bench_m.group(0) in pt), None)
                facts.append(AMCFact(scheme_id, "benchmark", val, pdf_path.name, pg, as_of_date))

            # Fund Managers (all co-managers)
            mgr_m = re.findall(
                r"(?:Fund\s+Manager|Managed\s+by)[^\n]*?:\s*([\w\s,]+?)(?=\n|Fund\s+Manager|$)",
                full_text,
                re.I,
            )
            if mgr_m:
                val = "; ".join(m.strip() for m in mgr_m[:3])
                facts.append(AMCFact(scheme_id, "fund_manager", val, pdf_path.name, None, as_of_date))

    except Exception as e:
        print(f"Error parsing {pdf_path.name}: {e}")

    return facts


def write_conflict_report(conn: sqlite3.Connection, out_path: Path) -> None:
    """Compare facts_amc vs facts and write JSON conflict report."""
    amc: dict = {}
    for row in conn.execute(
        "SELECT scheme_id, field, value, as_of_date, source_pdf FROM facts_amc"
    ):
        amc[(row[0], row[1])] = {"value": row[2], "date": row[3], "source": row[4]}

    groww: dict = {}
    try:
        for row in conn.execute("SELECT scheme_id, field, value, as_of FROM facts"):
            groww[(row[0], row[1])] = {"value": row[2], "date": row[3], "source": "Groww scheme page"}
    except sqlite3.OperationalError:
        # facts table may not exist in test/isolated environments
        pass

    conflicts = []
    for key in set(amc) | set(groww):
        a = amc.get(key)
        g = groww.get(key)
        if a and g and a["value"] != g["value"]:
            conflicts.append(
                {
                    "scheme_id": key[0],
                    "field": key[1],
                    "amc_value": a["value"],
                    "amc_date": a["date"],
                    "amc_source": a["source"],
                    "groww_value": g["value"],
                    "groww_date": g["date"],
                    "groww_source": g["source"],
                }
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"generated_at": str(Path.cwd()), "conflicts": conflicts}, indent=2)
    )
    print(f"Conflict report: {len(conflicts)} conflict(s) written to {out_path}")


def run() -> None:
    pdfs = list(FACTSHEETS_DIR.glob("*.pdf")) if FACTSHEETS_DIR.exists() else []
    if not pdfs:
        print("no factsheets found")
        return

    conn = sqlite3.connect(DB_PATH)
    create_facts_amc_table(conn)

    all_facts: list[AMCFact] = []
    for pdf in pdfs:
        facts = extract_facts_from_pdf(pdf)
        all_facts.extend(facts)
        for f in facts:
            conn.execute(
                "INSERT INTO facts_amc (scheme_id, field, value, source_pdf, page_number, as_of_date)"
                " VALUES (?,?,?,?,?,?)",
                (f.scheme_id, f.field, f.value, f.source_pdf, f.page_number, f.as_of_date),
            )
    conn.commit()
    print(f"Ingested {len(all_facts)} facts from {len(pdfs)} PDFs")

    write_conflict_report(conn, Path("data/reports/fact_conflicts.json"))
    conn.close()


if __name__ == "__main__":
    run()
