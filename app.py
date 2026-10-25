"""Mutual Fund FAQ Assistant - Hugging Face Space Demo.

Groww-styled Facts-Only Q&A Assistant bounded strictly to 5 HDFC Mutual Fund schemes.
Adheres strictly to the SEBI 5-Point Response Contract and Option C Stat Card output format.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Generator, List, Tuple

# Ensure backend package is in python path, and remove current dir from sys.path
# so app.py does not shadow the backend/app package.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, "backend")

while CURRENT_DIR in sys.path:
    sys.path.remove(CURRENT_DIR)
while "" in sys.path:
    sys.path.remove("")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Restore CURRENT_DIR at the end of sys.path for other local assets
sys.path.append(CURRENT_DIR)

# Bind default DATA_DIR
if not os.environ.get("DATA_DIR"):
    os.environ["DATA_DIR"] = os.path.join(CURRENT_DIR, "data")

try:
    import spaces
except ImportError:
    class spaces:  # type: ignore
        @staticmethod
        def GPU(func=None, duration=60):
            if func is None:
                return lambda f: f
            return func

import gradio as gr
from app.api.rag import ask_query
from app.guardrails.pii import PII_SECURITY_WARNING, scan_pii
from app.guardrails.refusal import CANONICAL_LINKS, get_default_corpus_date
from app.rag.facts import SCHEME_REGISTRY, get_fact_from_db
from app.schemas.synthesis import SynthesisQueryRequest

SCHEME_MAP = {
    "Auto-detect from Question": None,
    "HDFC Mid-Cap Opportunities Fund (Direct - Growth)": "hdfc_midcap_dg",
    "HDFC Small Cap Fund (Direct - Growth)": "hdfc_smallcap_dg",
    "HDFC Top 100 Fund (Direct - Growth)": "hdfc_largecap_dg",
    "HDFC Silver ETF FoF (Direct - Growth)": "hdfc_silver_fof_dg",
    "HDFC Multi Cap Fund (Direct - Growth)": "hdfc_multicap_dg",
}

CUSTOM_CSS = """
/* Groww Obsidian Archetype */
:root {
    --groww-primary: #00D09C;
    --groww-primary-dark: #00B386;
    --groww-bg: #12161A;
    --groww-card: #1E252E;
    --groww-card-border: #2C3542;
    --groww-text: #FFFFFF;
    --groww-text-muted: #9CA3AF;
}

body, .gradio-container {
    background-color: #12161A !important;
    color: #F3F4F6 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

#col-container {
    max-width: 1100px;
    margin: 0 auto;
}

.dark .gradio-container {
    color: var(--body-text-color);
}

/* Header Badge & Title */
.groww-header {
    background: linear-gradient(135deg, #1E252E 0%, #161C24 100%);
    border: 1px solid #2C3542;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
}

.groww-badge {
    display: inline-block;
    background-color: rgba(0, 208, 156, 0.12);
    color: #00D09C;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 9999px;
    border: 1px solid rgba(0, 208, 156, 0.3);
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Chatbot container */
.chatbot-container {
    border: 1px solid #2C3542 !important;
    border-radius: 12px !important;
    background-color: #181E26 !important;
}

/* Markdown Table Rendering for Option C Stat Cards */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    border-radius: 8px;
    overflow: hidden;
    background-color: #1E252E;
    border: 1px solid #2C3542;
}

th {
    background-color: rgba(0, 208, 156, 0.15) !important;
    color: #00D09C !important;
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
    border-bottom: 1px solid #2C3542;
    font-size: 13px;
}

td {
    padding: 10px 14px;
    border-bottom: 1px solid #26303D;
    color: #E5E7EB;
    font-size: 13.5px;
}

tr:last-child td {
    border-bottom: none;
}

/* Button & Input accents */
button.primary-btn {
    background: #00D09C !important;
    color: #000000 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    transition: all 0.2s ease;
}

button.primary-btn:hover {
    background: #00B386 !important;
    box-shadow: 0 4px 12px rgba(0, 208, 156, 0.3);
}

.scheme-tag {
    background: #1E252E;
    border: 1px solid #2C3542;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
    color: #9CA3AF;
}
"""


@spaces.GPU(duration=60)
def respond(
    message,
    history,
    selected_scheme_label,
):
    """Process user message and yield streaming chat response."""
    if not message or not message.strip():
        yield history
        return

    query = message.strip()
    scheme_id = SCHEME_MAP.get(selected_scheme_label)

    # 1. PII Check
    has_pii, detected, redacted = scan_pii(query)
    if has_pii:
        doc_date = get_default_corpus_date()
        citation = CANONICAL_LINKS["ADVISORY"]
        reply = (
            f"⚠️ **Security Warning**: {PII_SECURITY_WARNING}\n\n"
            f"Detected sensitive items: `{', '.join(detected)}`\n\n"
            f"Source: {citation}\n"
            f"Last updated from sources: {doc_date}"
        )
        updated_history = history + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": reply},
        ]
        yield updated_history
        return

    # 2. Invoke RAG Synthesis Pipeline
    try:
        req = SynthesisQueryRequest(
            query=query,
            session_scheme_id=scheme_id,
            top_k=4,
        )
        resp = ask_query(req)
        full_response = resp.rendered
    except Exception as e:
        full_response = (
            f"An error occurred while retrieving factual data: `{str(e)}`\n\n"
            f"Source: https://www.amfiindia.com/investor-corner/knowledge-center\n"
            f"Last updated from sources: 2026-10-25"
        )

    # 3. Stream typewriter tokens for natural Groww assistant feel
    updated_history = history + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": ""},
    ]

    chunk_size = 6
    for i in range(0, len(full_response), chunk_size):
        updated_history[-1]["content"] = full_response[: i + chunk_size]
        yield updated_history
        time.sleep(0.01)

    updated_history[-1]["content"] = full_response
    yield updated_history


def get_fact_explorer_data() -> str:
    """Builds a formatted markdown table of all 5 verified HDFC schemes."""
    md = (
        "| Scheme Name | Category | NAV | AUM (Fund Size) | Expense Ratio | Exit Load |\n"
        "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    )
    for scheme_id, meta in SCHEME_REGISTRY.items():
        name = meta.get("official_name", meta.get("name"))
        cat = meta.get("category", "Equity")
        nav_fact = get_fact_from_db(scheme_id, "nav")
        aum_fact = get_fact_from_db(scheme_id, "aum_cr")
        er_fact = get_fact_from_db(scheme_id, "expense_ratio")
        el_fact = get_fact_from_db(scheme_id, "exit_load")

        nav = f"₹{nav_fact['value_num']:.2f}" if nav_fact and nav_fact.get("value_num") else "N/A"
        aum = f"₹{aum_fact['value_num']:,.2f} Cr" if aum_fact and aum_fact.get("value_num") else "N/A"
        er = f"{er_fact['value_num']:.2f}%" if er_fact and er_fact.get("value_num") else "N/A"
        el = el_fact.get("value_str", "1.0% (1 yr)") if el_fact else "1.0% (1 yr)"
        md += f"| **{name}** | {cat} | {nav} | {aum} | {er} | {el} |\n"
    return md


# Build Gradio Interface
with gr.Blocks(theme=gr.themes.Citrus(), css=CUSTOM_CSS, title="Mutual Fund FAQ Assistant") as demo:
    with gr.Column(elem_id="col-container"):
        # Header Section
        gr.HTML(
            """
            <div class="groww-header">
                <div class="groww-badge">Groww UX • Facts-Only • SEBI Compliant</div>
                <h1 style="color: #FFFFFF; margin: 4px 0 8px 0; font-size: 24px; font-weight: 700;">
                    📊 Mutual Fund FAQ Assistant
                </h1>
                <p style="color: #9CA3AF; margin: 0; font-size: 14px; line-height: 1.5;">
                    Deterministic, verifiable mutual fund facts powered by hybrid retrieval across 
                    5 official HDFC Mutual Fund schemes. Built on the principle: 
                    <strong style="color: #00D09C;">Accuracy over Intelligence</strong>.
                </p>
                <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px;">
                    <span class="scheme-tag">📈 Mid-Cap Opportunities</span>
                    <span class="scheme-tag">🚀 Small Cap Fund</span>
                    <span class="scheme-tag">🏛️ Top 100 (Large-Cap)</span>
                    <span class="scheme-tag">🥈 Silver ETF FoF</span>
                    <span class="scheme-tag">🌐 Multi Cap Fund</span>
                </div>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=4):
                scheme_dropdown = gr.Dropdown(
                    choices=list(SCHEME_MAP.keys()),
                    value="Auto-detect from Question",
                    label="Focus Scheme (Optional Pre-filter)",
                    interactive=True,
                )

        chatbot = gr.Chatbot(
            label="Verified Groww Assistant",
            elem_classes=["chatbot-container"],
            height=420,
            type="messages",
            avatar_images=(None, "https://groww.in/groww-logo-270.png"),
        )

        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="Ask about AUM, NAV, expense ratio, exit load, fund managers...",
                show_label=False,
                scale=5,
                container=False,
                autofocus=True,
            )
            submit_btn = gr.Button("Ask Assistant", variant="primary", scale=1, elem_classes=["primary-btn"])

        with gr.Row():
            clear_btn = gr.ClearButton([msg_input, chatbot], value="Clear Conversation")

        # Example Queries
        gr.Markdown("### 💡 Click an example to test:")
        gr.Examples(
            examples=[
                ["What is the AUM of HDFC Mid-Cap Opportunities Fund?", "Auto-detect from Question"],
                ["What is the expense ratio of HDFC Small Cap Fund?", "Auto-detect from Question"],
                ["Who manages the HDFC Top 100 Fund?", "Auto-detect from Question"],
                ["What is the exit load of HDFC Silver ETF FoF?", "Auto-detect from Question"],
                ["Should I invest ₹1,00,000 in HDFC Multi Cap Fund today?", "Auto-detect from Question"],
                ["My PAN is ABCDE1234F, tell me my balance.", "Auto-detect from Question"],
            ],
            inputs=[msg_input, scheme_dropdown],
        )

        # Quick Fact Sheet Tab
        with gr.Accordion("📋 Verified Scheme Fact Sheet (Direct from facts.db)", open=False):
            gr.Markdown(get_fact_explorer_data())

        # Regulatory Notice
        gr.HTML(
            """
            <div style="margin-top: 24px; padding: 14px; border: 1px solid #232D3F; border-radius: 8px; background: rgba(30, 37, 46, 0.4); text-align: center; font-size: 12px; color: #6B7280;">
                🛡️ <strong>SEBI Regulatory Notice</strong>: Mutual fund investments are subject to market risks. Read all scheme related documents carefully.
                This assistant provides factual metrics strictly from official regulatory sources (AMFI, Groww, CAMS) and never offers investment advice.
            </div>
            """
        )

    # Event bindings
    def user_submit(user_msg, chat_hist, scheme_sel):
        if not user_msg.strip():
            return "", chat_hist
        return "", chat_hist + [{"role": "user", "content": user_msg.strip()}]

    msg_input.submit(
        respond,
        inputs=[msg_input, chatbot, scheme_dropdown],
        outputs=[chatbot],
        show_api=False,
    ).then(lambda: "", None, [msg_input], show_api=False)

    submit_btn.click(
        respond,
        inputs=[msg_input, chatbot, scheme_dropdown],
        outputs=[chatbot],
        show_api=False,
    ).then(lambda: "", None, [msg_input], show_api=False)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
    )
