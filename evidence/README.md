# Evidence

Everything in this folder backs a number or a claim in [../reports/REPORT.md](../reports/REPORT.md).

| Folder | What it holds |
| --- | --- |
| [`logs/`](logs/README.md) | The full garak logs for the three scans (every prompt, reply and verdict), cleaned of local file paths and compressed |
| [`images/`](images/) | Charts and real command output, generated from those logs |

## The images

| Image | What it shows | Which claim it backs |
| --- | --- | --- |
| `images/hijack_rates.png` | How often a hidden instruction in a report or resume was obeyed, for the bare model, the chatbot with no defenses and the chatbot with all three | Hidden instructions work (up to 45.7%), and the defenses lowered it |
| `images/example_hijack.png` | One real saved example: the hidden instruction at the bottom of a document and the model's entire reply | What a "failure" actually looks like, not just a count |
| `images/refusal_correction.png` | The jailbreak numbers before and after removing the chatbot's own refusals | The measurement problem and its correction (186 became 135) |
| `images/blocked_by_defenses.png` | How many prompts the defended chatbot refused outright, per probe | Much of the resume improvement is refusal, which also blocks legitimate requests |
| `images/proof_compare.png` | Real output of `python scripts/compare.py --evidence` | The results table can be rebuilt from the committed logs |
| `images/proof_ci_run.png` | Real output of `gh run view` for a passing GitHub Actions run | The scan runs automatically on GitHub |
| `images/proof_ci_results.png` | The scan result lines from that run's log | The CI scan really produced results (and that they vary between runs) |

## How the images were made

`python scripts/make_images.py` regenerates all of them. The charts are computed from `logs/`, the example is a real record from the hit log, and the terminal images are the actual text printed by the commands the script runs. Nothing is drawn by hand or edited afterwards.

## What this evidence does not show

- It shows what garak recorded, not whether the detectors are right. The jailbreak detector is only a keyword check.
- Each scan was run once, so run-to-run variation is not measured. The CI results are a small hint that it exists.
- Which individual defense helped is not known, because only "none" and "all three" were run.
