"""Behaviour snapshot: proves a refactor or a corpus change left existing answers alone (EVAL-P9.2).

    # on the baseline commit (e.g. a `git worktree add ../base <sha>`):
    GROQ_API_KEY= python -m eval.behaviour_snapshot snapshot before.json
    # on the changed tree:
    GROQ_API_KEY= python -m eval.behaviour_snapshot snapshot after.json
    python -m eval.behaviour_snapshot compare before.json after.json [--ignore static.registry ...]

Run with an empty GROQ_API_KEY so the LLM path falls back and every answer is deterministic. For every
query in eval/datasets/*.jsonl it records the API answer, the resolved entities and the intent, plus the
static responses and the scheme-listing routes of both the backend and the Hugging Face Space entry.
"""

from __future__ import annotations

import argparse
import dataclasses
import glob
import importlib.util
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXTRA_QUERIES = [
    "What is the expense ratio?",
    "Exit load?",
    "What is the NAV?",
    "Compare HDFC Mid-Cap and HDFC Small Cap",
    "HDFC Silver",
    "Tell me about HDFC schemes",
    "What is the TER of HDFC Regular Plan Mid-Cap?",
    "What is the expense ratio of SBI Bluechip Fund?",
    "hello",
    "help",
    "What can you do?",
]


def _queries() -> list[str]:
    queries: list[str] = []
    for path in sorted(glob.glob(os.path.join(REPO_ROOT, "eval", "datasets", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                q = json.loads(line).get("query") if line.strip() else None
                if q and q not in queries:
                    queries.append(q)
    return queries + [q for q in EXTRA_QUERIES if q not in queries]


def snapshot(out_path: str) -> None:
    sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))
    os.chdir(REPO_ROOT)
    from fastapi.testclient import TestClient

    from app.guardrails.intent import classify_intent
    from app.guardrails.refusal import generate_refusal
    from app.main import _IP_REQUEST_TIMESTAMPS, app
    from app.rag import entities as E
    from app.rag import prompts, retriever

    client = TestClient(app)
    snap: dict = {"queries": {}, "entities": {}, "intents": {}, "static": {}, "routes": {}}
    for q in _queries():
        _IP_REQUEST_TIMESTAMPS.clear()
        r = client.post("/api/v1/rag/ask", json={"query": q})
        snap["queries"][q] = {"status": r.status_code, "body": {k: v for k, v in r.json().items() if k != "latency_ms"}}
        snap["entities"][q] = dataclasses.asdict(E.resolve_entities(q))
        i = classify_intent(q)
        snap["intents"][q] = {"intent": i.intent, "is_refusal": i.is_refusal, "triggers": list(i.matched_triggers or [])}

    snap["static"] = {
        "external_amc": E.get_external_amc_response("sbi"),
        "unsupported_plan": E.get_unsupported_plan_response(),
        "amc_out_of_scope": E.get_amc_out_of_scope_response(),
        "disambiguation": E.get_disambiguation_response(),
        "not_found": retriever.get_not_found_response(),
        "refusal_help": generate_refusal("HELP"),
        "refusal_smalltalk": generate_refusal("SMALLTALK"),
        "refusal_out_of_scope": generate_refusal("OUT_OF_SCOPE"),
        "registry": E.SCHEME_REGISTRY,
        "system_prompt": prompts.SYSTEM_SYNTHESIS_PROMPT,
    }
    routes = ("/health", "/api/v1/health", "/api/v1/meta", "/api/v1/facts/schemes")
    for route in routes:
        r = client.get(route)
        snap["routes"]["backend" + route] = {"status": r.status_code, "body": r.json()}

    # The Hugging Face Space entry registers its own copies of these routes.
    import gradio as gr

    spec = importlib.util.spec_from_file_location("space_app", os.path.join(REPO_ROOT, "app.py"))
    space = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(space)
    space_client = TestClient(gr.routes.App.create_app(space.demo))
    for route in routes:
        r = space_client.get(route)
        snap["routes"]["space" + route] = {"status": r.status_code, "body": r.json()}
    snap["space_scheme_map"] = space.SCHEME_MAP
    snap["space_fact_table"] = space.get_fact_explorer_data()

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1, ensure_ascii=False, sort_keys=True, default=str)
    print(f"{len(snap['queries'])} queries -> {out_path}")


def _flatten(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _flatten(v, f"{prefix}.{k}" if prefix else str(k))
    else:
        yield prefix, node


def compare(before_path: str, after_path: str, ignore: list[str]) -> int:
    """Differences in answers both runs gave. Queries only one run has (new eval cases) are listed, not failed."""
    with open(before_path, encoding="utf-8") as f:
        before = dict(_flatten(json.load(f)))
    with open(after_path, encoding="utf-8") as f:
        after = dict(_flatten(json.load(f)))
    ignored = lambda k: any(k.startswith(p) for p in ignore)
    diffs = [k for k in sorted(set(before) & set(after)) if before[k] != after[k] and not ignored(k)]
    for k in diffs[:40]:
        print(f"DIFF {k}", f"  before: {str(before[k])[:160]!r}", f"  after:  {str(after[k])[:160]!r}", sep="\n")
    only = sorted({k.split(".")[1] for k in set(before) ^ set(after) if k.startswith(("queries.", "entities.", "intents."))})
    for q in only:
        print(f"ONLY IN ONE RUN: {q}")
    print(f"{len(set(before) & set(after))} shared values compared, {len(diffs)} differ, {len(only)} queries in only one run"
          + (f" ({len(ignore)} prefixes ignored)" if ignore else ""))
    return 1 if diffs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot").add_argument("out")
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("before")
    cmp_.add_argument("after")
    cmp_.add_argument("--ignore", nargs="*", default=[])
    args = ap.parse_args()
    if args.cmd == "snapshot":
        snapshot(args.out)
    else:
        sys.exit(compare(args.before, args.after, args.ignore))
