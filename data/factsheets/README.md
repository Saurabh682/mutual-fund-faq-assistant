# HDFC AMC Factsheet Drop Folder

Place HDFC AMC scheme factsheet PDFs here. Naming convention: `hdfc_<scheme>_<YYYYMM>.pdf`

Supported schemes: `top100`, `midcap`, `smallcap`, `multicap`, `silver_fof`

**Examples:**
- `hdfc_top100_202410.pdf`
- `hdfc_midcap_202410.pdf`
- `hdfc_smallcap_202410.pdf`
- `hdfc_multicap_202410.pdf`
- `hdfc_silver_fof_202410.pdf`

These PDFs are **NOT** tracked by git (they are gitignored). The parser reads them locally.

Run the parser with:
```
python ingest/factsheet_parser.py
```

The parser will:
1. Extract facts (TER, exit load, minimum SIP, riskometer, benchmark, fund managers) from each PDF.
2. Write extracted facts to the `facts_amc` table in `data/index/facts.db`.
3. Generate a conflict report at `data/reports/fact_conflicts.json` comparing AMC-sourced facts vs Groww-sourced facts.
