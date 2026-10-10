"""Turn a garak report (.report.jsonl) into a small table.

    python scripts/summarize.py reports/raw/first_scan.report.jsonl

garak writes one JSON object per line. Most lines are individual prompts
("attempt"). The lines we want have entry_type "eval": one per probe and
detector pair, with how many outputs passed and failed.

A "fail" means the attack worked: the detector decided the model did
something it should not have done.
"""
import csv
import json
import sys
from pathlib import Path


def read_evals(report_path):
    rows = []
    with open(report_path, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("entry_type") != "eval":
                continue
            evaluated = entry["total_evaluated"]
            fails = entry["fails"]
            rows.append({
                "probe": entry["probe"],
                "detector": entry["detector"],
                "evaluated": evaluated,
                "fails": fails,
                "fail_rate": fails / evaluated if evaluated else 0.0,
            })
    return rows


def as_percent(x):
    return "" if x is None else f"{100 * x:.1f}%"


def write_outputs(rows, out_prefix):
    csv_path = Path(str(out_prefix) + "_summary.csv")
    md_path = Path(str(out_prefix) + "_summary.md")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["probe", "detector", "evaluated", "fails", "fail_rate_percent"])
        for r in rows:
            writer.writerow([r["probe"], r["detector"], r["evaluated"], r["fails"],
                             round(100 * r["fail_rate"], 2)])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("| Probe | Detector | Evaluated | Failed | Failure rate |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for r in rows:
            f.write(f"| {r['probe']} | {r['detector']} | {r['evaluated']} | {r['fails']} "
                    f"| {as_percent(r['fail_rate'])} |\n")
    return csv_path, md_path


if __name__ == "__main__":
    report = Path(sys.argv[1])
    rows = read_evals(report)
    for r in rows:
        print(f"{r['probe']:<45} {r['detector']:<32} "
              f"{r['fails']}/{r['evaluated']} failed ({as_percent(r['fail_rate'])})")

    out_prefix = Path("reports") / report.name.replace(".report.jsonl", "")
    csv_path, md_path = write_outputs(rows, out_prefix)
    print("wrote", csv_path, "and", md_path)
