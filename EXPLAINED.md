# EXPLAINED: garak and this repo in plain English

## The idea
In the prompt-injection lab I attacked a chatbot by hand with about 40 prompts I wrote. That does not scale, and I only test the attacks I think of. [garak](https://github.com/NVIDIA/garak) is a tool that fires hundreds of known attacks at a model automatically and scores the replies. This repo uses it, adds my own summary scripts, and runs a small scan automatically in CI.

## garak's four parts
| Part | What it is | Analogy |
| --- | --- | --- |
| Generator | The thing being tested (a model, or an HTTP endpoint) | The exam student |
| Probe | A set of attack prompts for one weakness | The exam questions |
| Detector | Code that decides if a reply counts as a failure | The marker |
| Report | A log of every prompt, reply and verdict (JSONL) plus an HTML summary | The marked exam |

A "failure" in garak means **the attack worked**.

## The probes I used
- **latentinjection (Report, Resume):** a document the model is asked to process has an instruction hidden inside ("reply with only this text..."). Failure = the reply contains that text. This is *indirect injection*, the same weakness that worked best in my manual lab.
- **dan.DanInTheWild:** real jailbreak prompts from the internet. Failure = the reply has none of a list of refusal phrases. **This is a weak signal:** it does not prove harmful output, only that the model did not clearly refuse.
- **encoding.InjectBase64:** asks the model to decode hidden Base64 text. Failure = it prints the decoded payload.

## Files
- **`configs/*.yaml`**: each is a repeatable scan recipe (which probes, which target). A config file means anyone can re-run my exact test. `bot.yaml` points garak's REST generator at my chatbot's `/chat` endpoint; garak substitutes each attack prompt for `$INPUT`.
- **`scripts/run_scan.py`**: runs garak with a config, points the report into `reports/raw/`, saves a cleaned log, and prints a summary.
- **`scripts/summarize.py`**: reads garak's report. The report is JSONL (one JSON object per line); the lines I need have `entry_type: "eval"`, with pass and fail counts per probe and detector. I looked at the real file first to see which fields exist.
- **`scripts/compare.py`**: puts the three scans side by side and **corrects a counting problem**: my bot's refusal message is not on garak's list of refusal phrases, so blocked prompts were counted as successful attacks (51 of 186 jailbreak "failures" with defenses on).
- **`.github/workflows/garak.yml`**: GitHub Actions installs Ollama and a tiny 0.5B model, runs `configs/ci.yaml` on every push, and posts the table in the job summary. This is continuous testing: every change gets re-scanned automatically.

## What I found, in one paragraph
Hidden instructions hijack llama3.2 a lot (45.7% on the report probe). My chatbot's three defenses lowered that (39.5% to 30.5% on the report probe; 13.3% to 1.6% on resume), but they were designed to protect a secret, and the effect on resume is largely because the input filter refused 180 of 256 prompts outright, including ordinary resume-summary requests. I cannot say which defense helped because I only ran "none" and "all three".

## Questions you may be asked
1. **What does garak do?** Sends many known attack prompts (probes) to a model and uses detectors to mark each reply pass or fail.
2. **Why use it if you already tested by hand?** Scale, repeatability, and attacks I did not think of.
3. **Are garak's results always right?** No. The jailbreak detector is a keyword check. I also found it miscounted my bot's own refusals as failures, and I corrected for that.
4. **How did you find that problem?** The defenses seemed to make jailbreaks slightly worse, which made no sense. I read the saved replies and found 51 of the "failures" were my own refusal message.
5. **Which defense worked best?** I cannot say. I only ran no defenses vs all three. The output filter only checks for the secret, so it should not affect these probes.
6. **Is the improvement real?** The resume drop is far beyond noise but is mostly refusals, which also blocks legitimate use. The report-probe drop (9 points) is suggestive, not conclusive, from one run.
7. **Why does the CI scan use a tiny model?** GitHub's free runners have no GPU and little memory. It proves the pipeline runs automatically; it says nothing about bigger models.
8. **What did your attacks and garak's attacks have in common?** Both found that hiding instructions in content the model reads works best, but they measure different goals (print a phrase vs leak a secret), so the numbers cannot be compared directly.
9. **Limits?** One model, a sample of 256 prompts per probe, each scan run once, a keyword-based jailbreak detector, and garak was never told the chatbot's secret.
