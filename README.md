# 📊 Mutual Fund FAQ Assistant (Facts-Only Q&A)

> An AI-powered, retrieval-augmented generation (RAG) assistant for mutual fund schemes with Groww as the reference product context.
> Built on the foundational principle: **"Accuracy over Intelligence"** — deterministic, factual, verifiable answers backed strictly by official regulatory and AMC sources.

---

## 📚 Project Documentation

All specifications, architectural blueprints, and execution roadmaps are organized in the [`docs/`](./docs) directory:

| Document | Description |
|---|---|
| **[`docs/problemStatement.md`](./docs/problemStatement.md)** | Core problem statement, product context, objectives, target personas, scope, and non-functional constraints. |
| **[`docs/problemStatement.txt`](./docs/problemStatement.txt)** | Original raw problem statement brief. |
| **[`docs/architecture.md`](./docs/architecture.md)** | Comprehensive 22-section technical architecture, system context, hybrid retrieval, guardrail layer, and ADRs. |
| **[`docs/implementation-plan.md`](./docs/implementation-plan.md)** | Phase-by-phase implementation plan (Phases 0–7) with acceptance gates, code blueprints, and evaluation metrics. |
| **[`docs/edge-case.md`](./docs/edge-case.md)** | Exhaustive matrix of corner scenarios, failure modes, adversarial prompts, and regulatory tripwires. |
| **[`docs/eval.md`](./docs/eval.md)** | Phase-by-phase evaluation framework, testing procedures, scoring weights, and golden benchmark runner. |

---

## 🎯 Target Schemes & Reference Corpus (HDFC Mutual Fund)

The assistant is scoped to **HDFC Mutual Fund** across 5 diversified schemes:

1. **Mid-Cap**: [HDFC Mid-Cap Opportunities Fund (Direct - Growth)](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)
2. **Small-Cap**: [HDFC Small Cap Fund (Direct - Growth)](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth)
3. **Large-Cap**: [HDFC Top 100 Fund (Direct - Growth)](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth)
4. **Precious Metals FoF**: [HDFC Silver ETF FoF (Direct - Growth)](https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth)
5. **Multi-Cap**: [HDFC Multi Cap Fund (Direct - Growth)](https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth)

Official regulatory and investor guidance:
- [AMFI India Knowledge Center](https://www.amfiindia.com/investor-corner/knowledge-center)
- [SEBI Investor Protection & Riskometer Circulars](https://sebi.gov.in)
- [CAMS Online Statement Services](https://www.camsonline.com)

---

## 🛡️ Response Contract & Guardrail Invariants

Every assistant response satisfies the **"Rule of Three"**:
1. **Length**: Maximum 3 sentences (concise and factual).
2. **Single Citation**: Exactly 1 verified official source URL from the whitelist.
3. **Standardized Footer**: `Last updated from sources: <YYYY-MM-DD>`.
4. **Zero Investment Advice**: 100% deterministic refusal on advisory/comparative/projection queries, redirecting users to official AMFI resources.
5. **Zero PII**: Automatic detection and redaction of PAN, Aadhaar, account numbers, and OTPs.
