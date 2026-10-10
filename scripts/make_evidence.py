"""Make a shareable, compressed copy of the raw garak logs.

    python scripts/make_evidence.py

The raw logs in reports/raw/ are large (about 10 MB each) and contain the local
file paths of the computer that ran the scans. This script:

  1. replaces the home-folder path with the placeholder <home>,
  2. gzips each log into reports/evidence/ (these ARE committed),
  3. re-reads the cleaned copy and checks that it gives exactly the same
     pass and fail counts as the raw log, so the evidence still supports the
     numbers in reports/REPORT.md.

Nothing else is changed: every prompt, reply and verdict is kept as garak wrote it.
"""
import gzip
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "reports" / "raw"
EVIDENCE = REPO / "reports" / "evidence"
SCANS = ["full_llama3.2", "bot_defenses_off", "bot_defenses_on"]
KINDS = ["report", "hitlog"]
NEWLINE = chr(10)


def home_variants():
    """The home folder written the ways it appears inside the JSON text."""
    home = str(Path.home())                      # C:\Users\name
    # A backslash can be escaped once or twice more when a path sits inside a
    # string that is itself inside JSON, so match 8, 4, 2 and 1 backslashes.
    variants = [home.replace("\\", "\\" * n) for n in (8, 4, 2, 1)]
    variants.append(home.replace("\\", "/"))     # forward-slash form
    return variants


def clean(text):
    for variant in home_variants():
        text = text.replace(variant, "<home>")
    return text


def eval_counts(text):
    """Pass and fail counts per probe and detector, read from the eval lines of a log.

    Split on newline characters only. str.splitlines() would also split on odd
    characters that can appear inside a model's reply, cutting a JSON line in two.
    """
    counts = {}
    for line in text.split(NEWLINE):
        if not line:
            continue
        entry = json.loads(line)                 # also proves every line is still valid JSON
        if entry.get("entry_type") == "eval":
            counts[(entry["probe"], entry["detector"])] = (entry["fails"], entry["total_evaluated"])
    return counts


if __name__ == "__main__":
    EVIDENCE.mkdir(exist_ok=True)
    for scan in SCANS:
        for kind in KINDS:
            source = RAW / f"{scan}.{kind}.jsonl"
            target = EVIDENCE / f"{scan}.{kind}.jsonl.gz"
            raw_text = source.read_text(encoding="utf-8")
            cleaned = clean(raw_text)

            with open(target, "wb") as raw_file:
                # mtime=0 so running this twice gives byte-identical files
                with gzip.GzipFile(fileobj=raw_file, mode="wb", mtime=0) as gz:
                    gz.write(cleaned.encode("utf-8"))

            with gzip.open(target, "rt", encoding="utf-8", newline="") as check:
                same = eval_counts(check.read()) == eval_counts(raw_text)
            leftover = any(v in cleaned for v in home_variants())
            print(f"{target.name:<42} {target.stat().st_size / 1e6:5.2f} MB   "
                  f"counts identical to raw: {same}   local paths left: {leftover}")
            assert same and not leftover
