"""Run a garak config, keep the report inside this repo, and print a summary.

    python scripts/run_scan.py configs/quick.yaml
    python scripts/run_scan.py configs/bot.yaml --tag defenses_off

Why a wrapper? garak decides for itself where reports go. This script copies
the config, points the report at reports/raw/, runs garak, saves a cleaned
console log, and then calls summarize.py on the result.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from summarize import read_evals, write_outputs

REPO = Path(__file__).resolve().parent.parent
RAW_DIR = REPO / "reports" / "raw"


def clean_console(text):
    """garak redraws progress bars with carriage returns; keep only real lines."""
    kept = []
    for piece in text.replace("\r", "\n").split("\n"):
        if "it/s]" in piece or "s/it]" in piece or piece.startswith("Preparing prompts"):
            continue
        if piece.strip():
            kept.append(piece)
    return "\n".join(kept)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("--tag", default="", help="added to the report name, e.g. defenses_off")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    name = Path(args.config).stem + (f"_{args.tag}" if args.tag else "")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.setdefault("reporting", {})["report_prefix"] = (RAW_DIR / name).as_posix()

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        yaml.safe_dump(config, tmp)
        tmp_path = tmp.name

    print(f"running garak with {args.config} -> reports/raw/{name}.report.jsonl")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run([sys.executable, "-m", "garak", "--config", tmp_path],
                            capture_output=True, text=True, encoding="utf-8", env=env)
    os.remove(tmp_path)

    log = clean_console(result.stdout + "\n" + result.stderr)
    (RAW_DIR / f"{name}_console.txt").write_text(log, encoding="utf-8")

    report = RAW_DIR / f"{name}.report.jsonl"
    if result.returncode != 0 or not report.exists():
        print(log[-1500:])
        sys.exit(f"garak failed (exit code {result.returncode})")

    rows = read_evals(report)
    for r in rows:
        print(f"{r['probe']:<45} {r['detector']:<32} {r['fails']}/{r['evaluated']} failed")
    write_outputs(rows, REPO / "reports" / name)


if __name__ == "__main__":
    main()
