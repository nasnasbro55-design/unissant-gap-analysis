# Eval harness

`cases.jsonl` holds one test case per line. Every file named `cases*.jsonl` in this folder is loaded,
so each author can keep their own (for example `cases_huy.jsonl`) and use ids with their own
prefix (`h01`, `h02`, ...). Scores are also broken down by author. `run_eval.py` runs every case through
the real pipeline and scores it:

    python3 checks/eval/run_eval.py                      # all cases, one at a time
    REASONING_EFFORT=low python3 checks/eval/run_eval.py
    python3 checks/eval/run_eval.py --workers 3          # 3 requests in flight at once
    python3 checks/eval/run_eval.py --only c05,c09

## Case format

    {"id": "c14", "author": "huy", "tags": ["gap"],
     "narrative": "...free text...",
     "expected": {"212(a)(6)(A)(i)": {"status": "gaps", "missing": ["place_of_entry"]}}}

- `status` is one of `complete`, `gaps`, `human_review`.
- `missing` lists the required facts the narrative does NOT state (empty if none).
- A charge that is not in `charge_elements.json` is keyed by its lowercase, space-free
  citation (e.g. `212(a)(2)(a)(i)`) and expects `human_review`.
- A narrative that cites no charge expects key `no_charge_cited` with `human_review`.
- Tag a case `ambiguous` if reasonable people could disagree about the answer. Those are
  reported separately and left out of the headline score.

## Rules for adding cases

- Fictional people and events only. No real case records, names, or A-numbers.
- Put your own name in `author`. Whoever wrote the prompt should not be the only author.
- Write the expected answer from the rule ("is the fact explicitly stated?"), not by
  running the model first and copying what it said.

## Flags

- `--repeat N` runs the whole set N times and lists the cases whose gap report changed
  between runs (the model's extraction is not perfectly repeatable, so measure it).
- Failed cases print the facts the model extracted and any claims dropped as ungrounded.
- Settings come from the environment: `PROMPT_VERSION` (v4 default, which adds the conflict rule; v3 and v2 are the older
  prompt) and `REASONING_EFFORT` (low default; `default` leaves the server's setting).

- A narrative whose facts contradict the charge it cites (for example it says the subject was
  admitted on a visa, but cites unlawful presence without admission) expects `human_review`
  with `missing` empty. The pipeline does not catch these yet, so they should fail for now.
