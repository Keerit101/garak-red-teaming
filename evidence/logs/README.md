# Evidence

The raw logs behind every number in [reports/REPORT.md](../../reports/REPORT.md). Each scan has two files:

| File | What it holds |
| --- | --- |
| `<scan>.report.jsonl.gz` | garak's full report: every prompt sent, every reply, and every detector verdict (one JSON object per line) |
| `<scan>.hitlog.jsonl.gz` | Only the attempts a detector marked as a failure (the attack worked), with the prompt and reply |

Scans: `full_llama3.2` (the bare model), `bot_defenses_off` and `bot_defenses_on` (the prompt-injection-lab chatbot). Each logs 1,024 prompts: 4 probes x 256.

## Check the numbers yourself

```
python scripts/compare.py --evidence
```

This reads these files only and rebuilds `../../reports/comparison.md`, including the correction for the bot's own refusal messages being counted as failures. The table it prints matches the one in the report.

To look at a log directly:

```
python -c "import gzip,json,collections as c; print(c.Counter(json.loads(l)['entry_type'] for l in gzip.open('bot_defenses_on.report.jsonl.gz','rt',encoding='utf-8')))"
```

## What was changed from the original logs

Only the home-folder path of the computer that ran the scans was replaced with `<home>` (it appeared in a few configuration entries), and the files were gzip-compressed. `scripts/make_evidence.py` does this and then checks that the cleaned copy gives exactly the same pass and fail counts as the original. Prompts, replies and verdicts are untouched.

garak's own test prompts contain dummy data such as `customer_email@example.com`; those are part of garak's attacks, not real addresses.
