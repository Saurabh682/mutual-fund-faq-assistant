"""Deploy the current `main` branch to the Hugging Face Space as a snapshot upload.

Why not `git push`: the Space rejects pushes whose *history* contains binary files that were
committed outside Xet/LFS (older index files, screenshots, a PDF snapshot). `upload_folder`
sends only the current files and stores binaries in Xet automatically.

What it uploads: exactly the files git tracks on `main` (LFS files resolved to real content
from the working tree). Files on the Space that are not in that set are deleted, so the Space
mirrors `main`.

Token: HF_TOKEN (any capitalisation) from ./.env, falling back to ../.env, or the HF_TOKEN
environment variable (used in CI). It is never printed.

Usage (from the project root):
    backend\\.venv\\Scripts\\python.exe scripts\\deploy_hf_space.py [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SPACE = "deamonizer/mutual-fund-faq-assistant"
ROOT = Path(__file__).resolve().parent.parent
TOKEN_LINE = re.compile(r'^\s*(?:export\s+)?HF_TOKEN\s*=\s*"?([^"\s]+)"?\s*$', re.I)


def read_token() -> str:
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    for env_file in (ROOT / ".env", ROOT.parent / ".env"):
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                m = TOKEN_LINE.match(line)
                if m:
                    print(f"Using HF token from {env_file}")
                    return m.group(1)
    sys.exit(f"HF_TOKEN not found in {ROOT / '.env'}, {ROOT.parent / '.env'} or the environment")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Stage the files and report; upload nothing")
    args = ap.parse_args()

    if git("rev-parse", "--abbrev-ref", "HEAD").strip() != "main":
        sys.exit("Check out main first.")
    dirty = [l for l in git("status", "--porcelain", "--untracked-files=no").splitlines() if l.strip()]
    if dirty:
        sys.exit("Tracked files have uncommitted changes; commit or stash them so the Space matches main:\n" + "\n".join(dirty))

    head = git("log", "--oneline", "-1").strip()
    files = [f for f in git("ls-files", "-z").split("\0") if f]

    with tempfile.TemporaryDirectory(prefix="hf-deploy-") as tmp:
        stage = Path(tmp)
        for rel in files:
            src = ROOT / rel
            if src.is_file():
                dst = stage / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        print(f"Staged {len(files)} tracked files from {head}")

        if args.dry_run:
            print("Dry run: nothing uploaded.")
            return 0

        from huggingface_hub import HfApi

        api = HfApi(token=read_token())
        commit = api.upload_folder(
            repo_id=SPACE,
            repo_type="space",
            folder_path=str(stage),
            delete_patterns=["*"],  # remove Space files that are no longer in main
            commit_message=f"Deploy {head}",
        )
        print(f"Deployed: {commit.commit_url}")
        print(f"The Space will now rebuild: https://huggingface.co/spaces/{SPACE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
