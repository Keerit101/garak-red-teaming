# Project 3 — Automating Red Teaming with garak

## Goal
Use [garak](https://github.com/NVIDIA/garak), NVIDIA's LLM vulnerability scanner, to automatically probe language models for weaknesses, then automate and report the results.

## How garak works (for the write-up)
- **Generators**: the model under test (Hugging Face, OpenAI, Ollama, REST endpoint, …)
- **Probes**: attack prompts grouped by weakness (e.g. `promptinject`, `dan`, `encoding`, `leakreplay`, `malwaregen`, `xss`)
- **Detectors**: judge whether each response counts as a failure
- **Reports**: JSONL log + HTML summary for each run

## Tasks
1. **Install & first run**
   ```bash
   pip install garak
   python -m garak --list_probes
   python -m garak --model_type huggingface --model_name gpt2 --probes encoding
   ```
2. **Probe suite** (`configs/`): YAML configs for a focused suite (prompt injection, jailbreaks, encoding, data leakage)
3. **Targets**
   - A local model via Ollama
   - The Project 1 app through garak's REST generator, before vs. after defenses
   - (Stretch) Compare 2–3 models side by side
4. **Automation** (`scripts/`)
   - `run_scan.py`: runs a config and saves the report path
   - `summarize.py`: parses garak JSONL into a pass/fail table per probe (CSV + Markdown)
   - GitHub Actions workflow: runs a small, fast scan on push/PR (`.github/workflows/garak.yml`)
5. **Report** (`reports/`): failure rates per probe and model, the most interesting failures, and how this compares to the manual testing in Project 1

## Deliverables
- [ ] garak running locally
- [ ] 2+ YAML configs
- [ ] Scan of the Project 1 app, before and after defenses
- [ ] Report parser + summary table
- [ ] CI workflow
- [ ] `reports/REPORT.md`

> Check exact CLI flags and generator names with `python -m garak --help`. They change between garak versions.

## Schedule (week of Oct 12, 2026)

- **Thu:** install garak, build YAML configs, scan a local model and the prompt-injection-lab app, write a JSONL report parser
- **Fri:** GitHub Actions workflow for a small scan on push, finish `reports/REPORT.md`
