# Automated Red Teaming with garak

Scans a local LLM and my own chatbot with [garak](https://github.com/NVIDIA/garak) (NVIDIA's LLM vulnerability scanner), summarizes the results with my own script, and re-runs a small scan automatically on GitHub after every push.

**Headline result:** on a sample of 256 attacks per type, hidden instructions inside a report hijacked the bare llama3.2 model **45.7%** of the time. Against my [prompt-injection-lab](https://github.com/Keerit101/prompt-injection-lab) chatbot, the same attack worked **39.5%** of the time with no defenses and **30.5%** with all three defenses on; for hidden instructions in a resume the rate dropped from 13.3% to 1.6%. Those defenses were built to protect a secret, not to stop these attacks, and one of them mostly worked by refusing the whole request. See [reports/REPORT.md](reports/REPORT.md) for the full numbers, a measurement problem I found and corrected, and the limits of the experiment.

> Scope: every target is a model or app running on my own computer. Nothing external was scanned.

## What's here

| Path | What it does |
| --- | --- |
| `configs/first_scan.yaml` | One probe against a local model, to learn garak's report format |
| `configs/quick.yaml` | Tiny scan (7 prompts) for fast checks |
| `configs/full.yaml` | 4 probes x 256 prompts against the bare model (about 20 minutes) |
| `configs/bot.yaml` | The same probes against my chatbot over HTTP |
| `configs/ci.yaml` | The tiny scan GitHub Actions runs, against a 0.5B model |
| `scripts/run_scan.py` | Runs a config, keeps the report in this repo, prints a summary |
| `scripts/summarize.py` | Turns garak's report file into a table (CSV and Markdown) |
| `scripts/compare.py` | Puts the three scans side by side and corrects a refusal-counting problem |
| `.github/workflows/garak.yml` | Runs the CI scan on every push and shows the results in the job summary |
| `reports/` | Summaries and the comparison. Raw garak logs stay in `reports/raw/` (not committed) |

[EXPLAINED.md](EXPLAINED.md) explains garak's parts and the questions you may be asked.

## Run it

Needs Python 3.12 and [Ollama](https://ollama.com) with `ollama pull llama3.2`. (Python 3.14 is too new for garak's dependencies.)

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python scripts/run_scan.py configs/quick.yaml
```

To scan the chatbot, start it from the prompt-injection-lab repo in another terminal (`python -m app.server`, optionally with `set DEFENSES=input_filter,delimit,output_filter`), then run `python scripts/run_scan.py configs/bot.yaml --tag defenses_off`.
