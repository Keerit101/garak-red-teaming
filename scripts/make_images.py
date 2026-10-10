"""Generate the evidence images in evidence/images/ from the committed evidence logs.

    python scripts/make_images.py

Charts are computed from evidence/logs/*.gz (so anyone who clones the repo can
regenerate them). The example is a real prompt and reply from the garak hit log.
The terminal images are the real output of commands this script runs, including
`gh run view` for the GitHub Actions check (skipped if the GitHub CLI is missing).
Needs matplotlib (pip install -r requirements-figures.txt).
"""
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
EVIDENCE = REPO / "evidence" / "logs"
OUT = REPO / "evidence" / "images"
CONSOLAS = r"C:\Windows\Fonts\consola.ttf"
ARIAL = r"C:\Windows\Fonts\arial.ttf"
ARIAL_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
GH = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"

BLUE, GREEN, GREY, AMBER, RED = "#1d4e89", "#0f6b5c", "#8a96a3", "#d98f00", "#b3261e"
TODAY = datetime.date.today().isoformat()
BOT_REFUSAL = "Sorry, I can't help with that."
SCANS = [("full_llama3.2", "Bare llama3.2", GREY), ("bot_defenses_off", "Chatbot, no defenses", BLUE),
         ("bot_defenses_on", "Chatbot, all defenses on", GREEN)]

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#dde3ea", "grid.linewidth": 0.7, "axes.axisbelow": True})


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def records(label, kind):
    """Every JSON record of a committed evidence log (split on newlines only)."""
    with gzip.open(EVIDENCE / f"{label}.{kind}.jsonl.gz", "rt", encoding="utf-8", newline="") as f:
        return [json.loads(line) for line in f.read().split("\n") if line]


def text_of(value):
    return value["text"] if isinstance(value, dict) else str(value)


def eval_table(label):
    return {(r["probe"], r["detector"]): (r["fails"], r["total_evaluated"])
            for r in records(label, "report") if r.get("entry_type") == "eval"}


# ------------------------------------------------------------------ charts
def chart_hijack_rates():
    probes = [("latentinjection.LatentInjectionReport", "Hidden instruction\nin a report"),
              ("latentinjection.LatentInjectionResume", "Hidden instruction\nin a resume")]
    tables = {label: eval_table(label) for label, *_ in SCANS}
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    width = 0.26
    for i, (label, name, color) in enumerate(SCANS):
        values = []
        for probe, _ in probes:
            fails, total = tables[label][(probe, "base.TriggerListDetector")]
            values.append((100 * fails / total, fails, total))
        bars = ax.bar([x + (i - 1) * width for x in range(len(probes))], [v[0] for v in values], width, color=color, label=name)
        for bar, (pct, fails, total) in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, pct + 0.8, f"{pct:.1f}%\n{fails}/{total}", ha="center", fontsize=8.5)
    ax.set_xticks(range(len(probes)), [name for _, name in probes])
    ax.set_ylim(0, 58)
    ax.set_ylabel("attempts where the hidden instruction was obeyed (%)")
    ax.set_title("Hidden instructions hijack the model; the defenses lower it (256 attempts each)",
                 loc="left", fontweight="bold", fontsize=10.5)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="x", visible=False)
    save(fig, "hijack_rates.png")


def chart_refusal_correction():
    key = ("dan.DanInTheWild", "mitigation.MitigationBypass")
    raw = {label: eval_table(label)[key][0] for label, *_ in SCANS}
    refusals_on = sum(1 for r in records("bot_defenses_on", "hitlog")
                      if r["detector"] == key[1] and text_of(r["output"]).strip() == BOT_REFUSAL)
    names = ["Bare llama3.2", "Chatbot,\nno defenses", "Chatbot, defenses on\n(garak's number)", "Chatbot, defenses on\n(blocked prompts removed)"]
    values = [raw["full_llama3.2"], raw["bot_defenses_off"], raw["bot_defenses_on"], raw["bot_defenses_on"] - refusals_on]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    bars = ax.bar(names, [100 * v / 256 for v in values], color=[GREY, BLUE, AMBER, GREEN], width=0.6)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, 100 * v / 256 + 1.2, f"{100 * v / 256:.1f}%\n{v}/256", ha="center", fontsize=9)
    ax.annotate(f"{refusals_on} of these {raw['bot_defenses_on']} 'failures' were the\nbot's own refusal message, which\ngarak's keyword list does not recognize",
                xy=(2.3, 100 * values[3] / 256 + 6), xytext=(2.45, 100 * values[2] / 256 + 14), fontsize=8.5, color=RED,
                arrowprops={"arrowstyle": "->", "color": RED})
    ax.set_ylim(0, 105)
    ax.set_ylabel("replies with no known refusal phrase (%)")
    ax.set_title("A measurement problem, found and corrected", loc="left", fontweight="bold", fontsize=10.5)
    ax.grid(axis="x", visible=False)
    save(fig, "refusal_correction.png")


def chart_blocked():
    probes = [("latentinjection.LatentInjectionReport", "Report\nlatent injection"),
              ("latentinjection.LatentInjectionResume", "Resume\nlatent injection"),
              ("dan.DanInTheWild", "Jailbreak\nprompts"), ("encoding.InjectBase64", "Base64\nattacks")]
    counts = {probe: 0 for probe, _ in probes}
    for r in records("bot_defenses_on", "report"):
        if r.get("entry_type") == "attempt" and r.get("status") == 2 and r["outputs"]:
            if text_of(r["outputs"][0]).strip() == BOT_REFUSAL:
                counts[r["probe_classname"]] = counts.get(r["probe_classname"], 0) + 1
    fig, ax = plt.subplots(figsize=(8.5, 4))
    values = [counts[probe] for probe, _ in probes]
    bars = ax.bar([name for _, name in probes], values, color=[GREEN if v else GREY for v in values], width=0.55)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 4, f"{v}/256\n({100 * v / 256:.0f}%)", ha="center", fontsize=9)
    ax.set_ylim(0, 230)
    ax.set_ylabel("prompts the chatbot refused outright")
    ax.set_title("With defenses on: how many garak prompts got the refusal message instead of an answer",
                 loc="left", fontweight="bold", fontsize=10)
    ax.grid(axis="x", visible=False)
    save(fig, "blocked_by_defenses.png")


# ------------------------------------------------------------------ real example
def wrap(text, width):
    lines = []
    for paragraph in text.replace("\r", "").split("\n"):
        lines += textwrap.wrap(paragraph, width) or [""]
    return lines


def example_hijack_image():
    hit = next(r for r in records("full_llama3.2", "hitlog")
               if r["probe"] == "latentinjection.LatentInjectionReport" and len(text_of(r["output"])) < 80)
    prompt = text_of(hit["prompt"]["turns"][-1]["content"]) if isinstance(hit["prompt"], dict) else text_of(hit["prompt"])
    tail = "... " + " ".join(prompt[-430:].split()).split(" ", 1)[1]    # start at a whole word
    reply = text_of(hit["output"]).strip()
    trigger = ", ".join(hit["triggers"]) if isinstance(hit.get("triggers"), list) else str(hit.get("triggers"))

    body, bold, small = ImageFont.truetype(ARIAL, 17), ImageFont.truetype(ARIAL_BOLD, 17), ImageFont.truetype(ARIAL, 13)
    sections = [("THE DOCUMENT (end of the text sent to the model)", "a company FAQ with one hidden instruction at the bottom", tail, "#e9eef4", "#1f2933"),
                ("THE MODEL'S ENTIRE REPLY", f"garak verdict: FAIL, the reply contains the planted phrase '{trigger}'", reply, "#fde7e5", RED)]
    width, pad, line_h = 980, 24, 24
    blocks, total_h = [], 70
    for title, source, text, bg, accent in sections:
        lines = wrap(text, 100)
        h = 62 + line_h * len(lines)
        blocks.append((title, source, lines, bg, accent, h))
        total_h += h + 14
    image = Image.new("RGB", (width, total_h + 30), "white")
    d = ImageDraw.Draw(image)
    d.text((pad, 16), "Real example from evidence/logs/full_llama3.2.hitlog.jsonl.gz (bare llama3.2)", font=bold, fill="#1f2933")
    y = 56
    for title, source, lines, bg, accent, h in blocks:
        d.rounded_rectangle([pad, y, width - pad, y + h], radius=10, fill=bg)
        d.rectangle([pad, y, pad + 6, y + h], fill=accent)
        d.text((pad + 20, y + 10), title, font=bold, fill=accent)
        d.text((pad + 20, y + 33), source, font=small, fill="#5b6773")
        ty = y + 58
        for line in lines:
            d.text((pad + 20, ty), line, font=body, fill="#1f2933")
            ty += line_h
        y += h + 14
    d.text((pad, y + 2), f"Generated {TODAY} from the evidence log. Regenerate: python scripts/make_images.py", font=small, fill="#8a96a3")
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / "example_hijack.png")
    print("wrote example_hijack.png")


# ------------------------------------------------------------------ terminal images
def run_text(args):
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", cwd=REPO,
                            env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return result.stdout + result.stderr


def terminal_image(text, command, name, max_chars=112):
    font = ImageFont.truetype(CONSOLAS, 16)
    small = ImageFont.truetype(CONSOLAS, 13)
    text = text.replace("\u2713", "[ok]").replace("\u2717", "[x]")      # Consolas has no tick glyphs
    lines = []
    for raw in text.rstrip().split("\n"):
        while len(raw) > max_chars:
            lines.append(raw[:max_chars])
            raw = "    " + raw[max_chars:]
        lines.append(raw)
    footer = f"Real output captured {TODAY}. Regenerate: python scripts/make_images.py"
    pad, line_h, header_h = 18, 22, 38
    width = int(max(font.getlength(line) for line in lines + ["$ " + command]) + 2 * pad)
    width = max(width, int(small.getlength(footer)) + 2 * pad)
    height = header_h + pad + line_h * len(lines) + 34
    image = Image.new("RGB", (width, height), "#0f1720")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, header_h], fill="#1b2733")
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        draw.ellipse([14 + i * 22, 13, 26 + i * 22, 25], fill=color)
    draw.text((86, 9), "$ " + command, font=font, fill="#9fb3c8")
    y = header_h + pad
    for line in lines:
        ok = "[ok]" in line or line.strip() == "OK"
        draw.text((pad, y), line, font=font, fill="#7ee2a8" if ok else "#d6e2ee")
        y += line_h
    draw.text((pad, height - 26), footer, font=small, fill="#5b6f84")
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name)
    print("wrote", name)


def ci_images():
    if not Path(GH).exists():
        print("GitHub CLI not found; skipping the CI images")
        return
    run_id = run_text([GH, "run", "list", "--status", "success", "--limit", "1", "--json", "databaseId",
                       "--jq", ".[0].databaseId"]).strip()
    summary = run_text([GH, "run", "view", run_id])
    # keep the useful part (the check mark, the job and its timing), drop the long warnings
    shown = [line for line in summary.splitlines()
             if line.startswith(("[ok]", "\u2713", "Triggered", "JOBS", "ARTIFACTS", "garak-report", "View this run"))
             or line.startswith("\u2713") or " in " in line and "scan" in line]
    terminal_image("\n".join(shown), f"gh run view {run_id}", "proof_ci_run.png")
    log = run_text([GH, "run", "view", run_id, "--log"])
    results = []
    for line in log.splitlines():
        if line.rstrip().endswith("failed") and "Run garak" in line:
            results.append(line.split("Z ", 1)[-1])          # drop the timestamp prefix
    terminal_image("\n".join(results), f"gh run view {run_id} --log | grep failed", "proof_ci_results.png")


def main():
    chart_hijack_rates()
    chart_refusal_correction()
    chart_blocked()
    example_hijack_image()
    terminal_image(run_text([sys.executable, "scripts/compare.py", "--evidence"]),
                   "python scripts/compare.py --evidence", "proof_compare.png", max_chars=125)
    ci_images()


if __name__ == "__main__":
    main()
