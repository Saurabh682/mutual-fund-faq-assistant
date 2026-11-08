"""Tests for ingest/factsheet_parser.py

Covers:
- no-op when factsheets dir is empty
- facts_amc table creation & schema
- scheme detection from filename
- conflict report detects mismatches
- graceful fallback when pdfplumber is not installed
"""
import json
import sqlite3
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import shutil

@pytest.fixture
def local_tmp_path():
    p = Path('./test_tmp_fs')
    p.mkdir(parents=True, exist_ok=True)
    yield p
    shutil.rmtree(p, ignore_errors=True)


# ---------------------------------------------------------------------------
# Import the module under test (repo root is NOT on sys.path by default when
# pytest is invoked from backend/ — add repo root so the import resolves).
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import ingest.factsheet_parser as fp
from ingest.factsheet_parser import (
    AMCFact,
    SCHEME_NAME_MAP,
    create_facts_amc_table,
    extract_facts_from_pdf,
    write_conflict_report,
)


# ---------------------------------------------------------------------------
# test_no_factsheets_is_noop
# ---------------------------------------------------------------------------
def test_no_factsheets_is_noop(local_tmp_path, capsys, monkeypatch):
    """run() with an empty factsheets dir must print 'no factsheets found'
    and must NOT touch any DB file."""
    empty_dir = local_tmp_path / "factsheets"
    empty_dir.mkdir()
    fake_db = local_tmp_path / "facts.db"

    monkeypatch.setattr(fp, "FACTSHEETS_DIR", empty_dir)
    monkeypatch.setattr(fp, "DB_PATH", fake_db)

    fp.run()

    captured = capsys.readouterr()
    assert "no factsheets found" in captured.out
    # DB must NOT have been created by a no-op
    assert not fake_db.exists(), "DB should not be created when there are no PDFs"


# ---------------------------------------------------------------------------
# test_facts_amc_table_created_on_first_run
# ---------------------------------------------------------------------------
def test_facts_amc_table_created_on_first_run():
    """create_facts_amc_table must create the table with the expected columns."""
    conn = sqlite3.connect(":memory:")
    create_facts_amc_table(conn)

    cursor = conn.execute("PRAGMA table_info(facts_amc)")
    columns = {row[1] for row in cursor.fetchall()}

    expected = {
        "id", "scheme_id", "field", "value",
        "source_pdf", "page_number", "as_of_date", "ingested_at",
    }
    assert expected == columns, f"Missing columns: {expected - columns}"
    conn.close()


# ---------------------------------------------------------------------------
# test_scheme_detection_from_filename
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "filename,expected_scheme",
    [
        ("hdfc_top100_202410.pdf", "hdfc_largecap_dg"),
        ("hdfc_midcap_202410.pdf", "hdfc_midcap_dg"),
        ("hdfc_smallcap_202410.pdf", "hdfc_smallcap_dg"),
        ("hdfc_multicap_202410.pdf", "hdfc_multicap_dg"),
        ("hdfc_silver_fof_202410.pdf", "hdfc_silver_fof_dg"),
    ],
)
def test_scheme_detection_from_filename(local_tmp_path, filename, expected_scheme):
    """Filenames must map to the correct scheme_id via SCHEME_NAME_MAP."""
    # pdfplumber import will fail inside extract_facts_from_pdf — that's fine,
    # we only need to exercise the filename-to-scheme logic.  We can test it
    # directly via SCHEME_NAME_MAP without touching the PDF extraction path.
    stem = Path(filename).stem.lower()
    detected = None
    for key, sid in SCHEME_NAME_MAP.items():
        if key in stem:
            detected = sid
            break
    assert detected == expected_scheme, (
        f"Filename '{filename}' expected scheme '{expected_scheme}', got '{detected}'"
    )


def test_scheme_detection_unknown_file_returns_empty(local_tmp_path, capsys):
    """extract_facts_from_pdf with an unrecognised filename must return []."""
    # Stub pdfplumber so the ImportError path is NOT taken — we want the
    # "cannot detect scheme" branch.
    fake_plumber = types.ModuleType("pdfplumber")
    with patch.dict(sys.modules, {"pdfplumber": fake_plumber}):
        fake_pdf = local_tmp_path / "unknown_fund_202410.pdf"
        fake_pdf.write_bytes(b"")  # content doesn't matter — we won't parse it
        result = extract_facts_from_pdf(fake_pdf)

    assert result == []
    captured = capsys.readouterr()
    assert "Cannot detect scheme" in captured.out


# ---------------------------------------------------------------------------
# test_conflict_report_detects_mismatch
# ---------------------------------------------------------------------------
def test_conflict_report_detects_mismatch(local_tmp_path):
    """write_conflict_report must surface rows where AMC and Groww values differ."""
    conn = sqlite3.connect(":memory:")

    # Create facts_amc table with an AMC-sourced TER
    create_facts_amc_table(conn)
    conn.execute(
        "INSERT INTO facts_amc (scheme_id, field, value, source_pdf, page_number, as_of_date)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        ("hdfc_largecap_dg", "ter", "0.60%", "hdfc_top100_202410.pdf", 1, "31 October 2024"),
    )

    # Create a minimal facts table (Groww-sourced) with a DIFFERENT value
    conn.execute("""
        CREATE TABLE facts (
            id INTEGER PRIMARY KEY,
            scheme_id TEXT,
            field TEXT,
            value TEXT,
            as_of TEXT
        )
    """)
    conn.execute(
        "INSERT INTO facts (scheme_id, field, value, as_of) VALUES (?, ?, ?, ?)",
        ("hdfc_largecap_dg", "ter", "0.55%", "2024-10-30"),
    )
    conn.commit()

    out_file = local_tmp_path / "conflicts.json"
    write_conflict_report(conn, out_file)

    data = json.loads(out_file.read_text())
    assert len(data["conflicts"]) == 1
    conflict = data["conflicts"][0]
    assert conflict["scheme_id"] == "hdfc_largecap_dg"
    assert conflict["field"] == "ter"
    assert conflict["amc_value"] == "0.60%"
    assert conflict["groww_value"] == "0.55%"
    conn.close()


def test_conflict_report_no_conflict_when_values_match(local_tmp_path):
    """write_conflict_report must produce zero conflicts when values agree."""
    conn = sqlite3.connect(":memory:")
    create_facts_amc_table(conn)
    conn.execute(
        "INSERT INTO facts_amc (scheme_id, field, value, source_pdf, page_number, as_of_date)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        ("hdfc_largecap_dg", "ter", "0.60%", "hdfc_top100_202410.pdf", 1, None),
    )
    conn.execute("""
        CREATE TABLE facts (
            id INTEGER PRIMARY KEY, scheme_id TEXT, field TEXT, value TEXT, as_of TEXT
        )
    """)
    conn.execute(
        "INSERT INTO facts (scheme_id, field, value, as_of) VALUES (?, ?, ?, ?)",
        ("hdfc_largecap_dg", "ter", "0.60%", "2024-10-30"),
    )
    conn.commit()

    out_file = local_tmp_path / "conflicts.json"
    write_conflict_report(conn, out_file)
    data = json.loads(out_file.read_text())
    assert data["conflicts"] == []
    conn.close()


# ---------------------------------------------------------------------------
# test_extract_facts_no_pdfplumber
# ---------------------------------------------------------------------------
def test_extract_facts_no_pdfplumber(local_tmp_path, capsys):
    """extract_facts_from_pdf must return [] and print a helpful message
    when pdfplumber is not importable."""
    fake_pdf = local_tmp_path / "hdfc_top100_202410.pdf"
    fake_pdf.write_bytes(b"")

    # Force ImportError for pdfplumber
    with patch.dict(sys.modules, {"pdfplumber": None}):
        result = extract_facts_from_pdf(fake_pdf)

    assert result == []
    captured = capsys.readouterr()
    assert "pdfplumber not installed" in captured.out
