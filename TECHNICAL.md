# Technical Overview

Team TNUX, Challenge+X Round 3, Unissant UC3: GenAI-Assisted Gap Analysis for Investigative Charge Documentation.

This file is the single place for how the tool works, what is built, how well it performs, and what is left. Update it when any of those change.

---

## 1. The goal

Officers write free-text narratives that cite charges (for example INA 212(a)(6)(A)(i)). Each charge needs certain facts to be documented. The tool reads a narrative and reports which required facts are missing for each charge cited, so the officer can fix the narrative before it moves on.

What the tool does NOT do, by design and per Unissant:

- It does not write or rewrite the narrative.
- It does not pick, judge, or suggest a charge. It only checks the charges the officer cited.
- It does not decide anything on its own. Every result is reviewed by a person, and unclear cases are sent to a person with a reason.

### Unissant's success metrics (our targets)

| Metric | Target |
|---|---|
| Recall of real gaps | at least 90% |
| False flags (facts flagged missing that are present) | at most 10% |
| Ambiguous cases routed to a human | 100% |
| Time per review | under 60 seconds |

Scoring is based on how accurately the tool finds missing information. Narratives are free text, not structured data.

---

## 2. Why our approach is different

The generic version is "an LLM reads the narrative and lists what is missing." Most teams will build that. Its problems are well documented: legal AI tools hallucinate at high rates (Stanford RegLab measured over 17% on legal research tools), results change from run to run, and reviewers start trusting confident-looking output without checking it (automation bias).

Our design splits the work so the LLM does only the part it is good at:

```
narrative
   |
   v
[1] LLM extracts facts          -> fact type + exact quote + confidence (no judging)
   |
   v
[2] Grounding check (code)      -> every quote must appear word for word in the narrative, or it is dropped
   |
   v
[3] Rules engine (code)         -> compares found facts to the required-facts table for each cited charge
   |
   v
[4] Conflict check (code)       -> does any stated fact contradict the cited charge?
   |
   v
[5] Router (code)               -> unclear, conflicting, unknown-charge, no-citation, or model-down cases go to a human
   |
   v
evidence-first report (JSON)    -> every line points to a statute element, a quote, and a sentence
```

Steps 2 to 5 are plain code, so the same facts always give the same report. This is what makes results consistent across officers and stations, which is one of Unissant's stated goals. The research angle is "rules as code" / neuro-symbolic compliance checking: the LLM handles messy language, deterministic rules make the decision.

The model is Unissant's hosted gpt-oss-20b. Unissant allows any model and says model choice does not affect scoring. We use only gpt-oss-20b.

---

## 3. Features

Status key: **Built** = in the repo and tested. **Partial** = started. **Planned** = not started.

### 3.1 Core pipeline (Built)

- **Fact extraction** (`pipeline/extract.py`, prompts in `pipeline/prompts/`). The model returns JSON claims: fact type, shortest exact quote, confidence. The narrative is treated as data, and instructions inside it are ignored (tested with a prompt-injection case, c09).
- **Grounding guardrail.** A claim is kept only if its quote is found in the narrative (ignoring case and spacing). Sentence IDs are computed by code from where the quote sits, never trusted from the model.
- **Sentence splitter** that handles initials and abbreviations (`Subj.`, `K.`, `Mr.`), so quotes are not broken.
- **Required-facts table** (`checks/elements/charge_elements.json`) with plain-English definitions (`fact_definitions.json`). Three charges so far:
  - 212(a)(6)(A)(i), present without admission or parole
  - 212(a)(9)(A)(i), prior removal, reentry without admission
  - 212(a)(6)(C)(i), fraud or willful misrepresentation
- **Rules engine** (`gap_report` in `pipeline/run_sample.py`). Per charge: `complete`, `gaps` (with the missing facts), or `human_review` (with a reason).
- **Routing to a human** when: a charge is not in our table, no charge is cited, a required fact was found only with low confidence, a conflict is found, repeated runs disagree, or the model is unavailable.
- **Timeout.** A model call that takes over 40 seconds fails fast and the case goes to a human, so a slow shared server cannot hang the demo.
- **Speed.** `reasoning_effort=low` cut reviews from about 21 to 38 seconds down to about 5 to 9 seconds, with no loss in accuracy.

### 3.2 Differentiator 1: Metamorphic testing (Built)

`checks/eval/metamorphic.py` generates labeled test cases with code, with no hand-labeling:

- Builds a complete narrative from fact sentences, then deletes 0 to 2 facts. The correct answer is exactly the deleted facts.
- Applies one mutation that must not change the answer: all caps, all lowercase, abbreviations, a typo, or shuffled sentence order.
- Facts that depend on each other are deleted together (for example, deleting the removal order also deletes the removal date).
- Each remaining sentence is written so it does not imply a deleted fact. An early version broke this rule; we found it by inspecting failures and fixed it.

Run with `--meta N`. The summary breaks results down by charge, by mutation, and by number of deleted facts. This gives a recall and stability curve over hundreds of cases where other teams will show a handful of examples.

Limitation: generated narratives use fixed templates, so they test robustness, not natural writing. Hand-written cases from teammates cover natural writing.

### 3.3 Differentiator 2: Contradiction detection (Built)

Most tools check that a fact is present. Ours also checks that it fits the cited charge.

- Each charge lists facts that contradict it (`contradicted_by`), for example a statement that the subject was lawfully admitted, for a charge that requires no admission.
- Prompt v5 (the default) also asks the model for a yes/no `admitted` stance on admission facts; code checks the stance against `contradicted_by_stance`. This caught the overstay case (x06) that the separate conflict fact type missed.
- A conflict sends the charge to a human with the reason and the quote. The tool never suggests a different charge.
- Test cases: 6 contradictions (x01 to x06) and 2 hard negatives that must NOT be flagged: an earlier lawful admission followed by a later unlawful entry (n01), and someone else's admission (n02).

### 3.4 Differentiator 3: Abstain when unsure (Built, not the default)

`pipeline/review.py` runs the extraction 3 times in parallel. If the runs give different reports for a charge, that charge goes to a human with the facts they disagreed on.

Result so far: it catches random slips (metamorphic wrong answers went from 7 to 4) but not mistakes the model makes every time, and running 6 requests at once pushed one review to 97 seconds. So it is available with `--votes 3` but off by default. A possible improvement is to make the runs more independent (different fact order or slight temperature).

### 3.5 Differentiator 4: Evidence-first report (Partial)

- **Built:** the output contract (`pipeline/schemas.py`), the builder (`pipeline/report.py`), and a real sample (`backend/sample_report.json`). For every required fact: found or not, the quote, the sentence IDs, the confidence. Plus status, reason, conflicts, disagreements, statute source, and a disclaimer.
- **Left:** `POST /review` endpoint (Ethan, `backend/app.py`) and the React screen with the narrative highlighted (Huy).

### 3.6 Differentiator 5: Candid scorecard (Planned)

A showcase slide with our measured recall, false-flag rate, routing, latency, and failure list on the 20B model, plus what the tool deliberately does not do. The numbers come from section 4, updated after the blind test set.

### 3.7 Evaluation harness (Built)

`checks/eval/run_eval.py` scores against Unissant's metrics.

- Loads every `checks/eval/cases*.jsonl`, so each teammate keeps their own file. Scores are broken down by author.
- `--workers N` (parallel requests), `--repeat N` (stability across runs), `--votes N` (abstain mode), `--meta N --seed S` (metamorphic cases), `--only ids`.
- Cases tagged `ambiguous` are kept out of the headline score. `"missing": null` means only the status is checked (used for contradiction cases).
- Failed cases print the extracted and dropped claims, so failures can be diagnosed.

---

## 4. Results so far

Prompt v5, low reasoning, 3 parallel workers, 3 repeated runs, 60 metamorphic cases. Pass/fail is from the first run; stability is across all three. These are our own development cases, so they are optimistic until the blind set is in.

| Metric | Target | Result |
|---|---|---|
| Recall, hand-written cases | 90% | 9/9 (100%) |
| False flags, hand-written cases | at most 10% | 1 of 10 (10%) |
| Routing to human | 100% | 8/8 |
| Latency | under 60s | mean 5.5s, max 15.9s |
| Headline cases passed | | 17/18 |
| Contradiction and hard-negative cases | | 8/8 |
| Metamorphic cases passed | | 51/60 |
| Metamorphic recall | 90% | 72/76 (95%) |
| Metamorphic false flags | at most 10% | 7 of 79 (9%) |
| Same report on all 3 runs | | 73/81 |

v5 against v4: v5 fixed the overstay contradiction (x06) and reached 8/8 routing, but scored 3 fewer metamorphic cases (54 to 51) and was slightly less stable. Several contradiction cases (x01, x03, x04) changed between runs, so the per-run counts printed by `--repeat` are the number to quote, not one run.

### Blind test, round 1 (Jake's 15 cases, Oct 28)

First run on cases written by a teammate who never saw the prompts, before any fix based on them: **12/15 passed**. Across all 36 hand-written cases: recall 13/16 (81%, goal 90%), false flags 4 of 17 (24%, goal at most 10%), routing 12/12, max latency 37s. The fixes below were made after this run, so Jake's cases are now development cases and Huy's 17 cases are the next blind test.

What the blind run exposed, and the fix for each (all general rules, not edits to individual cases):

| Failure | Cases | Fix |
|---|---|---|
| Model cites a sentence with no admission words as admission status ("He re-entered the US") | c05, j06, m1-022, m1-024, m1-043 | Code rule: an admission-status quote must contain admit, parole or inspect; a removal-date quote must contain a date (`checks/elements/fact_anchors.json`) |
| Model fixes a typo inside its quote, so the exact-match check drops a correct fact | j11 | Accept a quote within a small spelling difference of the narrative text, and store the narrative's own text as evidence |
| Lowercase names missed | m1-002, m1-008, m1-016 | Definition: names may be lowercase or all caps |
| "Crossed the border near X" counted as how the subject entered | j05, m1-042 | Definition: saying the subject crossed or entered, without how, does not count |
| Unexplained: fraud facts not extracted (c07), multi-charge manner (c11) | c07, c11 | Open |

The sample narrative from Unissant gives the expected gaps (place of entry for 212(a)(6)(A)(i), prior removal date for 212(a)(9)(A)(i)) on every run.

### Load test (Oct 28)

`checks/load_test.py` against the `/review` API, 10 reviews per level, on the shared Unissant server:

| Reviews at once | Median | Slowest | Reviews per minute | Failures |
|---|---|---|---|---|
| 1 | 5.2s | 9.8s | 11 | 0 |
| 3 | 6.2s | 8.3s | 31 | 0 |
| 6 | 7.4s | 10.2s | 42 | 0 |
| 10 | 8.6s | 10.2s | 59 | 0 |

With the model unreachable (tested by accident with a missing key), every review was returned as `human_review` with "model unavailable" instead of failing. Each API review also has a hard 50-second limit, so a slow server on showcase day cannot push a review past the 60-second goal.

### Development rerun after the round 1 fixes (Oct 28)

On all 36 hand-written cases: 34/36 passed, recall 16/16 (100%), false flags 2 of 18 (11%), routing 12/12. Metamorphic 58/60 with 0 false flags. Both remaining false flags (c07, n02) came from the model shortening quotes with "...", which is now accepted when every piece appears in order. Not yet re-measured after that fix.

### Known failures

1. **Contradiction cases are not stable across runs.** v5 fixed x06 and passed all 8 on the first run, but x01, x03 and x04 changed between runs. Also, in 3 metamorphic cases v5 reported an admission status that had been deleted, possibly a side effect of asking for the stance. Watch both on the blind set.
2. **Lowercase names.** In all-lowercase narratives the model sometimes misses the subject's name.
3. **"Entered near X" counted as how they entered.** When the manner of entry is not stated, the model sometimes counts the place sentence as manner.
4. **Shared quotes in multi-charge narratives (c11).** One phrase that should cover several facts misses manner of entry.
5. **Definition questions, settled.** Unissant confirmed an approximate location like "near Brownsville, TX" counts as place of entry, so c01 and c13 are now normal cases expected complete. "Never inspected by an immigration officer" counts as stating admission status (Jake's rule from his blind cases), so c08 now expects complete.

### Prompt history

| Version | Change | Outcome |
|---|---|---|
| v1 | first extraction prompt | baseline |
| v2 | each fact once, short quotes | fewer duplicate claims |
| v3 | raw narrative, one quote can cover several facts | false flags 31% to 0% on early cases |
| v4 | conflict rule | slightly fewer false flags and more stable than v3 |
| v5 | yes/no admission stance, checked in code | **default.** Fixed x06, 8/8 routing; 3 fewer metamorphic passes than v4 |

---

## 5. Decisions and why

- **The LLM extracts, code decides.** Keeps results repeatable and auditable.
- **Quotes must be word for word.** Kills invented facts at the cost of occasionally dropping a paraphrased one.
- **No charge suggestions, ever.** Unissant's instruction, and a legal risk.
- **Low reasoning effort.** Same accuracy, 3 to 4 times faster.
- **Voting is optional.** Real but small gain, real latency cost.
- **Do not tune prompts on our own cases until the blind set arrives.** Every change fitted to our cases makes our numbers less trustworthy.
- **Fictional data only.** No real case records or names anywhere in the repo. The API key lives in an environment variable and never in the repo.

---

## 6. What is left

### Waiting on others
- [ ] Blind test cases from Huy and Jake (`cases_huy.jsonl`, `cases_jake.jsonl`), including contradictions and charges we do not cover.
- [ ] Jake's review of the expected answers in `cases.jsonl`.
- [x] Unissant answers: any model allowed (no effect on scoring); approximate location counts as place of entry.
- [x] Jake's blind cases: first run 12/15, fixes made (see Blind test, round 1).
- [ ] Huy's blind cases (`cases_huy.jsonl`) and React UI (`ui/`) pushed to main.
- [ ] First run on Huy's cases as the round 2 blind test, with no changes in between.
- [ ] Write test cases in the style of the public redacted CBP I-213 narratives Unissant shared, with fictional names and places.

### Pipeline
- [x] Live-test v5 against v4. v5 is the default (fixed x06, n01 not broken, small metamorphic cost).
- [ ] Re-run v5 with `--repeat 3` to get per-case pass counts across runs, especially for x01 to x06.
- [ ] After the blind set: address known failures 2 to 4, re-score, and record the result.
- [x] Fix the citation pattern so 3- to 5-level cites (`212(a)(2)(B)`, `212(a)(2)(A)(i)(II)`) are read in full.
- [ ] Add 1 or 2 more common charges (for example 212(a)(7)(A)(i)(I), no valid entry documents), checked against the statute and marked for Unissant to confirm.
- [ ] Decide on voting after testing more independent runs.

### Product
- [ ] `POST /review` endpoint wrapping `build_report` (Ethan).
- [ ] React review screen: per-charge status, missing facts, highlighted quotes, disclaimer, no suggested charges (Huy).
- [x] Load check: 10 at once, max 10.2s, no failures (see Load test).

### Showcase (Saturday 7 Nov)
- [ ] Update README (open questions are out of date; list models used and where a human reviews output, per Unissant's guardrail).
- [ ] Scorecard slide from section 4, with the failure list.
- [ ] Live demo script: one clean narrative, one with gaps, one contradiction, one unknown charge.

---

## 7. Where things are

| Path | What it is |
|---|---|
| `pipeline/llm_client.py` | connection to the hosted model (key from `CHALLENGEX_API_KEY`) |
| `pipeline/extract.py` | sentence splitting, extraction, grounding |
| `pipeline/prompts/` | extraction prompts v1 to v5 |
| `pipeline/run_sample.py` | rules engine (`gap_report`) and the sample narrative check |
| `pipeline/review.py` | voting / abstain mode |
| `pipeline/report.py` | builds the evidence-first report |
| `pipeline/schemas.py` | report contract |
| `checks/elements/` | required-facts table, fact definitions, hand markup of the sample |
| `checks/eval/` | harness, test cases, metamorphic generator |
| `backend/sample_report.json` | example report for the front end |
| `data/sample_narrative.txt` | Unissant's sample narrative |

### How to run

```
export CHALLENGEX_API_KEY=...        # never commit this
python3 pipeline/run_sample.py 3     # sample narrative, 3 runs
python3 checks/eval/run_eval.py --workers 3 --repeat 3 --meta 60
PROMPT_VERSION=v4 python3 checks/eval/run_eval.py --workers 3 --repeat 3 --meta 60   # compare with the previous prompt
python3 checks/eval/run_eval.py --workers 2 --votes 3 --meta 60
```
