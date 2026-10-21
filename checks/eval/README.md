# Eval harness

`cases.jsonl` holds one test case per line. `run_eval.py` runs every case through
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
