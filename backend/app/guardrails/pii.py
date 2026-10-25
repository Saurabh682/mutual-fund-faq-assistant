"""PII Firewall for Mutual Fund FAQ Assistant.

Strictly deterministic scanner adhering to the Indian Digital Personal Data Protection (DPDP) Act 2023.
Detects, redacts, and blocks:
- PAN (Permanent Account Number) with 4th-character entity status verification & spaced formatting.
- Aadhaar (12-digit UID) with full Dihedral D5 Verhoeff checksum validation to eliminate false positives.
- Indian mobile phone numbers (MSISDN +91 / 10-digit).
- Email addresses (RFC-5322 pattern).
- Bank Account numbers and IFSC codes.
- Mutual fund folio numbers.
- One-Time Passwords (OTP), PINs, and credentials.
"""

from __future__ import annotations

import re
from typing import List, Tuple

# Verhoeff algorithm multiplication table d
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# Verhoeff algorithm permutation table p
_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

# Verhoeff algorithm inverse table inv
_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

# Indian Income Tax Dept valid 4th-char entity status types
# P: Individual/Person, C: Company, H: HUF, F: Firm/LLP, A: AOP, T: Trust,
# B: BOI, L: Local Authority, J: Artificial Juridical Person, G: Government
PAN_ENTITY_TYPES = set("PCHFATBLJG")

# Spaced or standard PAN pattern: 5 letters (4th char captured), 4 digits, 1 letter
PAN_REGEX = re.compile(
    r"(?i)\b([a-z]\s*[a-z]\s*[a-z]\s*([a-z])\s*[a-z][\s\-]*(?:\d[\s\-]*){4}[a-z])\b"
)

# Aadhaar candidate pattern: 12 digits, optional space or dash every 4 digits
AADHAAR_REGEX = re.compile(r"\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b")

# Indian mobile: optional +91, starts with 6-9, followed by 9 digits
PHONE_REGEX = re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b")

# RFC-5322-lite email regex
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# IFSC code regex: 4 alphabetic chars, 0, 6 alphanumeric chars
IFSC_REGEX = re.compile(r"\b[A-Za-z]{4}0[A-Za-z0-9]{6}\b")

# Bank Account numbers (9 to 18 digits) near account keywords
ACCOUNT_KEYWORD_REGEX = re.compile(
    r"(?i)\b(?:account|a\/c|acct|acc(?:\s*no)?|bank\s*a\/c)\s*(?:no\.?|num(?:ber)?|#)?\s*(?:is\s*|[:\-])?\s*(\d{9,18})\b"
)
ACCOUNT_FOLLOWED_REGEX = re.compile(
    r"(?i)\b(\d{9,18})\s+(?:is\s+(?:my\s+)?)?(?:account|a\/c|bank\s*account)\b"
)

# Folio numbers (5 to 16 alphanumeric / slashes / hyphens) near 'folio' keyword
FOLIO_REGEX = re.compile(
    r"(?i)\b(?:folio(?:\s*(?:no\.?|num(?:ber)?|#))?)\s*(?:is\s*|[:\-])?\s*([A-Za-z0-9\/\-]{5,16})\b"
)

# OTP / Credentials
OTP_REGEX = re.compile(
    r"(?i)\b(?:otp|password|pin|cvv|secret)\b(?:\s*(?:is|[:\-])?\s*)\d{4,8}\b"
)
OTP_REVERSE_REGEX = re.compile(
    r"(?i)\b\d{4,8}\b\s+(?:is\s+(?:my\s+)?)?(?:otp|password|pin|cvv)\b"
)

PII_SECURITY_WARNING = (
    "Please do not share sensitive financial information such as PAN, Aadhaar, "
    "account, or folio numbers."
)


def verhoeff_validate(num_str: str) -> bool:
    """Validate numerical string using Dihedral D5 Verhoeff checksum algorithm.

    Returns True if valid check digit matches dihedral group D5 permutation, False otherwise.
    """
    digits = [int(c) for c in num_str if c.isdigit()]
    if not digits:
        return False
    c = 0
    for i, item in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][item]]
    return c == 0


def verhoeff_checksum(num_str: str) -> str:
    """Generate the Verhoeff check digit for a string of digits."""
    digits = [int(c) for c in num_str if c.isdigit()]
    c = 0
    for i, item in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[(i + 1) % 8][item]]
    return str(_VERHOEFF_INV[c])


def scan_pii(text: str) -> Tuple[bool, List[str], str]:
    """Deterministic PII scanner across PAN, Aadhaar, Phone, Email, Bank, Folio, and OTP.

    Scans contextual keywords first (Bank Account, Folio, Credentials) to avoid
    false positive collision with general 12-digit Aadhaar / phone patterns.

    Returns:
        (has_pii, detected_types, redacted_text)
    """
    detected: List[str] = []
    redacted = text

    # 1. Check Bank Account & IFSC (runs before Aadhaar so contextual a/c numbers are tagged correctly)
    bank_matches = []
    for m in IFSC_REGEX.finditer(redacted):
        bank_matches.append(m.group(0))
    for m in ACCOUNT_KEYWORD_REGEX.finditer(redacted):
        bank_matches.append(m.group(1))
    for m in ACCOUNT_FOLLOWED_REGEX.finditer(redacted):
        bank_matches.append(m.group(1))
    if bank_matches:
        detected.append("BANK_ACCOUNT")
        for match_str in bank_matches:
            redacted = redacted.replace(match_str, "[ACCOUNT_REDACTED]")

    # 2. Check Folio
    folio_matches = []
    for m in FOLIO_REGEX.finditer(redacted):
        folio_matches.append(m.group(0))
    if folio_matches:
        detected.append("FOLIO")
        for match_str in folio_matches:
            redacted = redacted.replace(match_str, "[FOLIO_REDACTED]")

    # 3. Check OTP / Credentials
    otp_matches = []
    for m in OTP_REGEX.finditer(redacted):
        otp_matches.append(m.group(0))
    for m in OTP_REVERSE_REGEX.finditer(redacted):
        otp_matches.append(m.group(0))
    if otp_matches:
        detected.append("CREDENTIAL")
        for match_str in otp_matches:
            redacted = redacted.replace(match_str, "[CREDENTIAL_REDACTED]")

    # 4. Check PAN (with 4th character entity type check)
    pan_matches = []
    for m in PAN_REGEX.finditer(redacted):
        raw_match = m.group(1)
        entity_char = m.group(2).upper()
        if entity_char in PAN_ENTITY_TYPES:
            pan_matches.append(raw_match)
    if pan_matches:
        detected.append("PAN")
        for match_str in pan_matches:
            redacted = redacted.replace(match_str, "[PAN_REDACTED]")

    # 5. Check Aadhaar (Verhoeff checksum validation strictly on 12-digit candidate strings)
    aadhaar_matches = []
    for m in AADHAAR_REGEX.finditer(redacted):
        candidate = m.group(1)
        digits = [c for c in candidate if c.isdigit()]
        if len(digits) == 12 and verhoeff_validate(candidate):
            aadhaar_matches.append(candidate)
    if aadhaar_matches:
        detected.append("AADHAAR")
        for match_str in aadhaar_matches:
            redacted = redacted.replace(match_str, "[AADHAAR_REDACTED]")

    # 6. Check Phone Numbers
    phone_matches = PHONE_REGEX.findall(redacted)
    if phone_matches:
        detected.append("PHONE")
        for match_str in phone_matches:
            redacted = redacted.replace(match_str, "[PHONE_REDACTED]")

    # 7. Check Email Addresses
    email_matches = EMAIL_REGEX.findall(redacted)
    if email_matches:
        detected.append("EMAIL")
        for match_str in email_matches:
            redacted = redacted.replace(match_str, "[EMAIL_REDACTED]")

    # Deduplicate detected types while preserving order
    unique_detected = list(dict.fromkeys(detected))
    return len(unique_detected) > 0, unique_detected, redacted
