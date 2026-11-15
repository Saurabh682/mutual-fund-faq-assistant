# 🗺️ Corpus Expansion Roadmap
# Growing from 5 HDFC schemes to ~19 (funds, index funds, ETFs, FoFs)

> **Status:** Phase 9.0 done (2026-11-15). 9.1 onwards planned, no new schemes added yet. This is Phase 9 of [implementation-plan.md](implementation-plan.md).
> **Last checked:** 2026-11-14 (Groww candidate URLs probed; see [Candidate list](#2-candidate-list-groww-pages-probed-2026-11-14)).

---

## 1. Goal and Scope

| | Today | After Wave 1 | After Wave 2 | After Wave 3 |
|---|:---:|:---:|:---:|:---:|
| **Schemes** | 5 | 10 | 13 | 19 |
| **Instrument types** | Equity, FoF | + Index fund | + ETF, Gold FoF | + Hybrid, ELSS, Debt, Thematic |

**In scope:** more **HDFC Mutual Fund Direct-Growth** schemes, each with a Groww page as the reference source, answering the same 8 fact fields (TER, exit load, minimum SIP/lump sum, lock-in, riskometer, benchmark, fund manager, NAV/AUM).

**Out of scope for this roadmap (deliberate):**
- **Other AMCs** (SBI, ICICI, Axis…). Those still get the "outside my scope" answer. Multi-AMC is a separate roadmap (architecture §21).
- **Regular plans and IDCW options.** Still unsupported, same refusal.
- **Stock-exchange ETF trading data** (live price, iNAV, volume). Only scheme-level facts from the Groww page.

**Why HDFC only:** the guardrail that refuses other AMCs, the corpus-manifest allow-list and every eval set are built around one AMC. Widening to HDFC's other schemes grows the count without changing any compliance rule.

---

## 2. Candidate List (Groww pages probed 2026-11-14)

HTTP 200 with fund keywords is a **weak** check: a page can load and still lack parsable fields. Every candidate must pass the Phase 9.1 fetch gate before it counts.

| Wave | Scheme | Type | Groww slug (`groww.in/mutual-funds/…`) | Probe |
|---|---|---|---|---|
| **1** | HDFC Flexi Cap Fund | Equity: Flexi Cap | `hdfc-equity-fund-direct-growth` | 200, slug-to-name mapping to confirm (`hdfc-flexi-cap-fund-direct-growth` is a 404) |
| **1** | HDFC Large and Mid Cap Fund | Equity: Large & Mid | `hdfc-large-mid-cap-fund-direct-growth` | 200 |
| **1** | HDFC Focused Fund | Equity: Focused | `hdfc-focused-fund-direct-growth` | 200 |
| **1** | HDFC NIFTY 50 Index Fund | Index fund | `hdfc-nifty-50-index-fund-direct-growth` | 200 |
| **1** | HDFC BSE Sensex Index Fund | Index fund | `hdfc-bse-sensex-index-fund-direct-growth` | 200 |
| **2** | HDFC Gold ETF Fund of Fund | FoF (gold) | `hdfc-gold-etf-fund-of-fund-direct-plan-growth` | 200 |
| **2** | HDFC Gold ETF | ETF | `hdfc-gold-etf` | 200, may redirect: confirm it is the ETF page |
| **2** | HDFC Sensex ETF | ETF | `hdfc-sensex-etf` | 200, may redirect: confirm it is the ETF page |
| **3** | HDFC Balanced Advantage Fund | Hybrid | `hdfc-balanced-advantage-fund-direct-growth` | 200 |
| **3** | HDFC ELSS Tax Saver | ELSS (3-year lock-in) | `hdfc-elss-tax-saver-fund-direct-plan-growth` | 200 |
| **3** | HDFC Liquid Fund | Debt: Liquid | `hdfc-liquid-fund-direct-growth` | 200 |
| **3** | HDFC Defence Fund | Thematic | `hdfc-defence-fund-direct-growth` | 200 |
| **3** | HDFC Pharma and Healthcare Fund | Thematic | `hdfc-pharma-and-healthcare-fund-direct-growth` | 200 |
| **3** | HDFC Manufacturing Fund | Thematic | `hdfc-manufacturing-fund-direct-growth` | 200 |
| **3** | HDFC Transportation and Logistics Fund | Thematic | `hdfc-transportation-and-logistics-fund-direct-growth` | 200 |

Probed and **not found**: `hdfc-nifty-50-etf` (404). Add other ETFs only after finding their real Groww URL on the AMC listing page (`groww.in/mutual-funds/amc/hdfc-mutual-funds`).

Waves are ordered by risk: Wave 1 reuses the equity field set the system already handles; Wave 2 introduces ETF/FoF field differences; Wave 3 adds categories with new fact semantics (lock-in, exit-load slabs, debt metrics).

---

## 3. What Is Hard-Wired To "5 Schemes" Today

Before 9.0, adding a scheme meant editing all of these by hand, which is where mistakes creep in. 9.0 removed that: the manifest is now the source, except for the static claims and hand-written documents noted in the Risks table.

| Area | Where | Problem |
|---|---|---|
| Scheme registry + aliases | `backend/app/rag/entities.py` (`SCHEME_REGISTRY`) | Hand-written aliases, one dict per scheme |
| Scheme lists in the UI/API | `app.py` (dropdown map + list), `backend/app/main.py` | Duplicated id/name lists |
| Corpus build | `ingest/build_official_corpus.py`, `ingest/factsheet_parser.py` (`silver_fof` mapping), `ingest/parsers/html.py` (silver special case) | Per-scheme branches |
| Manifest + truth | `data/corpus_manifest.yaml`, `data/ground_truth.yaml` | Manual, no completeness check |
| Prompt | `backend/app/rag/prompts.py` | "The 5 schemes and their synonymous names are…" |
| Fixed wording "5 HDFC schemes" | `refusal.py`, `validator.py`, `retriever.py`, `entities.py` and tests asserting that text | Wrong the moment the count changes |
| Clarification text | EC-ENT-01 in [edge-case.md](edge-case.md) lists all five names | A 19-name list is unusable |
| Tests and eval data | `test_phase1/3`, golden + holdout datasets name the 5 ids | Need a per-scheme matrix, not hand-copies |

---

## 4. Phases

### Mahindra Manulife wave (out of the original plan): ✅ built 2026-11-15, 15 schemes, total 20

Fund houses are a manifest list (`fund_houses`), each scheme has `amc` and `isin`, and resolution is fund-house aware: a house word narrows matching, a shared bare name yields a clarification with one option per scheme, and "Kotak Mahindra" stays out of scope. Covered by `backend/tests/test_multi_amc.py`.

### Phase 9.0: Make schemes data-driven (no new funds yet): ✅ done 2026-11-15

**Goal:** adding a scheme becomes one manifest entry plus a ground-truth row. Shipped alone, with the count still at 5, so behaviour changes are zero and provable.

What was built:

1. **One source of truth.** The `schemes` list in `data/corpus_manifest.yaml` now carries everything the code needs: id, `name`, `official_name`, category, Groww/AMC/AMFI URLs and code, `aliases`, `also_called` (prompt synonyms), `pinned_fund_manager`, `factsheet_key`. `backend/app/core/schemes.py` turns it into `SCHEME_REGISTRY`, `SCHEME_COUNT` and the dropdown list; `ingest/manifest.py` serves the ingestion code.
   - **Not added: `instrument_type`.** Nothing in 9.0 behaves differently by type, so the field arrives in 9.2 together with the code that reads it.
   - Where manifest and registry disagreed (Top 100's `name`, Silver FoF's `category`) the manifest adopted the registry value, because that is what users see.
2. **Duplicate lists deleted.** `SCHEME_REGISTRY` (`entities.py`), `/api/v1/meta` (`main.py` and `app.py`), the Space dropdown, the Gradio header tags and the health `schemes_count` all read the catalogue.
3. **Counts derived.** "5 HDFC schemes" in the refusal, validator, retriever, entity and prompt text is `SCHEME_COUNT`; the frontend heading uses `meta.schemes.length`. Text is identical at 5. Blanket claims about *every* scheme in static text (`procedures.py`, one knowledge-base document) are **not** derived, because their wording (minimum amount, lock-in, "non-ELSS") can go false independent of the number. A test fails when the count they cite no longer matches the registry, forcing a re-read.
4. **Per-scheme branches moved to data.** Fund-manager pins in `ingest/parsers/html.py` are now `pinned_fund_manager` in the manifest (a scheme with no pin uses the managers scraped from its page); the factsheet filename map in `ingest/factsheet_parser.py` is built from `factsheet_key`. The 15 hand-written official documents in `ingest/build_official_corpus.py` are **content, not branches**, so they stay; how a *new* scheme gets such documents is a 9.1 decision.
5. **Clarification.** The "which scheme?" answer names the first 5 schemes in manifest order and says "for example" when there are more. A bare category that matches several schemes is 9.3.
6. **Completeness tests** (`backend/tests/test_scheme_registry.py`): each scheme has its names, URLs and aliases, exactly one Groww `sources` row and one AMC `official_sources` row, no alias shared with another scheme, a ground-truth row, facts for 10 fields, at least 8 golden cases (two projection-refusal cases were added for Silver FoF and Multi Cap to reach 8), and a README entry.

**Gate (met):** `eval/behaviour_snapshot.py` records the answer, entities and intent for 468 queries plus the static responses and the scheme routes of both the backend and the Space entry, with the LLM off so everything is deterministic. Before and after: 15,051 shared values, **1 difference**: the synthesis prompt lists the same five schemes in manifest order instead of a hand-picked order. Every answer, entity, intent, static response and route is identical. Then the full suite, leak probe (0 of 353 queries leaked), benign eval (105/105), adversarial (60/60) and golden eval (61/61, the two new cases included) all pass.

### Phase 9.1: Fetch gate for each candidate

For every candidate in a wave, before adding it:
1. Fetch the Groww page with the existing fetcher (polite delay, same user agent policy as Phase 1). Decide where the scheme's official documents come from: the 15 existing ones are hand-written, which does not scale.
2. Parse all 8 fields. Record which are **present, not applicable** (e.g. an ETF with no exit load), or **missing**.
3. Cross-check TER, exit load, minimum SIP and the fund manager against the page text by hand once, store them in `ground_truth.yaml`, and set `pinned_fund_manager` in the manifest.
4. Reject or defer any scheme whose key fields cannot be parsed; log it in the decision table at the end of this file.

### Phase 9.2: Instrument-type semantics

| Type | Differences to handle |
|---|---|
| **Index fund / ETF** | TER is low; benchmark equals the index; ETF NAV is per unit and may differ from market price; fund manager may be a team |
| **FoF** | TER is the FoF's own, underlying fund costs are separate; exit load often applies |
| **ELSS** | 3-year lock-in (`lock_in` must be a real value, not "None") |
| **Debt / Liquid** | Exit load is a **slab** over the first 7 days; riskometer differs; no meaningful "lock-in" |
| **Thematic** | Very High risk; concentrated benchmark |

Rules:
- A field that does not apply (ETF exit load) is stored as **`not_applicable`** with a plain-language answer ("This ETF has no exit load per the Groww page"), never an empty value that falls through to "I don't have that information".
- `lock_in` for non-ELSS equity stays "None".
- Exit-load slabs are stored as one string exactly as shown; never summarised.

### Phase 9.3: Entity-resolution safety (do before Wave 1 goes live)

The 2026-11 audit found a fuzzy-match bug (an unlisted "Flexi Cap" resolved to Large Cap). More schemes make collisions likelier.

- **Alias collision tests** for each new pair: *Large Cap vs Large and Mid Cap*, *Flexi Cap vs Multi Cap vs Focused*, *Nifty 50 Index vs Nifty 50 ETF*, *Sensex Index vs Sensex ETF*, *Gold ETF vs Gold ETF FoF vs Silver ETF FoF*, *Mid-Cap Opportunities vs Large and Mid Cap*.
- A bare "Large Cap" or "Gold ETF" that matches 2+ schemes returns the clarification, not a guess.
- Keep the per-word fuzzy-match rule; add a regression test that a made-up HDFC fund name resolves to **no scheme**.
- Structural comparison rule (2+ schemes with no field) stays; confirm it still refuses with 19 names.

### Phase 9.4: Per-wave rollout

Repeat for each wave:

1. Add manifest entries and ground-truth rows (Phase 9.0 makes this declarative).
2. Run ingestion; confirm chunk and fact counts per scheme.
3. Add eval data for the new schemes (see [eval.md §11](eval.md#11-phase-9-evaluation-corpus-expansion-eval-p9)): **≥ 8 golden cases per new scheme**, plus advisory and comparison prompts naming the new funds.
4. Re-run: leak probe, benign eval, adversarial, out-of-corpus eval, golden, pytest, latency benchmark.
5. Check capacity (below). Deploy to the Space and smoke-test one fact per new scheme live.

### Phase 9.5: Operations at scale

| Concern | Check | Limit / action |
|---|---|---|
| **Daily CI time** | Time the ingestion job with N schemes | Job must finish well inside the Actions timeout; parallelise fetches if not |
| **Scraping politeness** | One request per page with a delay, no retry storms | Respect Groww rate limits; stop and report on repeated 403/429 |
| **Index size / Space memory** | Size of `data/index/` and RAM on the free Space | Revisit ADR-7 ("≤ 25 sources"): with ~3 sources per scheme, 19 schemes is ~57 documents |
| **Latency** | Re-run `eval/benchmark_latency_100.py` | Fact path p95 < 150 ms, overall p95 < 2 s must still hold |
| **Selector drift** | Daily job fails loudly on a missing field for any scheme | Keep last good value, flag stale, never publish blanks |
| **UI** | Fact-sheet dropdown with 19 entries | Group by category; keep it keyboard accessible |

---

## 5. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Wrong scheme answered (alias or fuzzy collision) | Highest: a confident wrong number | Phase 9.3 tests; clarification on ambiguity |
| ETF/debt field mis-modelled as "missing" | Users told "I don't have that" for facts that do not exist | `not_applicable` semantics (9.2) |
| More comparable funds raise advice-leak surface | Prompts like "best HDFC index fund" | Re-run leak probe and add advisory prompts per wave |
| Groww layout differs by category | Parser breaks for one type | Per-type parser tests from saved snapshots |
| Groww blocks or rate-limits the scraper | Stale data | Polite delay, fail loudly, keep last good values |
| Hosted Space runs out of memory | App down | Measure after each wave; stop expanding if headroom is thin |
| Static text that speaks for "all supported schemes" (`procedures.py` minimum amount and lock-in, the ELSS knowledge-base document) | Becomes false when ELSS, Liquid or an ETF joins | `test_blanket_claims_about_all_schemes_are_reviewed_when_the_count_changes` fails on any new scheme; reword each claim, then update its number |
| New scheme has no `pinned_fund_manager` | Fund manager comes from the scraped page, which is unverified | Phase 9.1 hand-check; pin it once confirmed |

---

## 6. Definition of Done (per wave)

- [ ] Every new scheme passes the 9.1 fetch gate or is deferred in the decision table.
- [ ] Registry completeness test green.
- [ ] Golden accuracy ≥ 98% and hallucination 0.0% over the enlarged set.
- [ ] 0 advice leaks in the leak probe, 100% adversarial refusal, 0 over-refusal on benign queries.
- [ ] Alias collision tests green; a made-up HDFC fund resolves to no scheme.
- [ ] Latency targets met; daily ingestion finishes within its time budget.
- [ ] README, architecture and eval docs show the new count (the README is checked against the registry by a test; the others by hand).
- [ ] Deployed and one fact per new scheme checked live.

---

## 7. Decision Log

| Date | Decision | Reason |
|---|---|---|
| 2026-11-14 | Stay within HDFC AMC for this expansion | Keeps the out-of-scope AMC guardrail and all eval sets valid |
| 2026-11-15 | **Superseded:** add Mahindra Manulife (all 15 Direct-Growth schemes) as a second fund house first; HDFC ETF/fund batch deferred | User choice. Fund houses moved into the manifest; names both houses use (mid/large/multi cap) now ask which scheme instead of guessing |
| 2026-11-15 | New Mahindra schemes ship with Groww-page facts and chunks only; the 20 hand-written official documents stay | Same sources as the HDFC Groww facts; AMC factsheet cross-check is pending |
| 2026-11-14 | Data-driven registry first (9.0), at unchanged count | Proves refactor safety before behaviour changes |
| 2026-11-15 | `instrument_type` deferred from 9.0 to 9.2 | No 9.0 code behaves differently by type; add it with its first reader |
| 2026-11-15 | README count is test-checked, not generated | A generator for one table is more machinery than a failing test that says what to edit |
| 2026-11-15 | Hand-written official documents stay in `build_official_corpus.py` | They are content; 9.1 decides how new schemes get theirs |
| 2026-11-14 | Waves ordered by field-semantics risk | Index/equity first, ETF/FoF second, debt/ELSS/thematic last |
| _tbd_ | Which candidates are deferred after the fetch gate | Filled in as Phase 9.1 runs |
