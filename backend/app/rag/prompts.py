"""Constrained Synthesis Prompt Builder for Mutual Fund FAQ Assistant.

Provides system instructions, context formatting, and targeted repair prompts
designed to keep Groq generation factual, concise (<= 3 sentences), and free of
evaluative words or unauthorized URLs.
"""

from __future__ import annotations

from typing import Any, List

SYSTEM_SYNTHESIS_PROMPT = """You are an official, facts-only Mutual Fund FAQ assistant for HDFC Mutual Fund schemes.
RULES:
1. Use ONLY the CONTEXT below. If the answer is not present in CONTEXT, output exactly: NOT_FOUND.
2. Note that 'HDFC Top 100 Fund' and 'HDFC Large Cap Fund' refer to the same fund scheme.
3. Maximum 3 sentences. No preamble, no greetings, no conversational filler, no closing remarks.
4. Copy numbers, percentages, dates, and names EXACTLY as written in CONTEXT.
5. Never give advice, opinions, recommendations, comparisons, predictions, or calculations.
6. Never use evaluative words (e.g., good, best, better, safe, safest, attractive, recommended, lucrative, ideal).
7. Do NOT output any URL, link, source line, or date; those are added programmatically by the system.
"""


def format_context_chunks(chunks: List[Any]) -> str:
    """Formats retrieved chunks into numbered context blocks for prompt injection."""
    formatted_blocks = []
    for idx, c in enumerate(chunks, 1):
        if isinstance(c, str):
            text = c.strip()
        elif isinstance(c, dict):
            text = c.get("text", "").strip()
        elif hasattr(c, "text"):
            text = getattr(c, "text", "").strip()
        else:
            text = str(c).strip()

        if text:
            formatted_blocks.append(f"[{idx}] {text}")

    return "\n\n".join(formatted_blocks)


def build_synthesis_user_prompt(question: str, chunks: List[Any]) -> str:
    """Builds the user prompt containing formatted context and the user query."""
    context_str = format_context_chunks(chunks)
    return (
        f"CONTEXT:\n{context_str}\n\n"
        f"QUESTION:\n{question.strip()}\n\n"
        f"FACTUAL ANSWER (1 to 3 sentences maximum, no URLs):"
    )


def build_repair_prompt(
    question: str,
    chunks: List[Any],
    previous_draft: str,
    violation_reason: str,
) -> str:
    """Builds a targeted repair prompt explaining the specific contract violation."""
    context_str = format_context_chunks(chunks)
    return (
        f"Your previous answer violated the strict output contract: {violation_reason}.\n\n"
        f"PREVIOUS DRAFT:\n\"{previous_draft}\"\n\n"
        f"CONTEXT:\n{context_str}\n\n"
        f"QUESTION:\n{question.strip()}\n\n"
        f"REVISED FACTUAL ANSWER (Strictly 1 to 3 sentences, use ONLY numbers from CONTEXT, no evaluative words, no URLs):"
    )
