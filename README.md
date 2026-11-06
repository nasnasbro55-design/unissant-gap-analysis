# GenAI-Assisted Gap Analysis for Investigative Charge Documentation

**Status:** Building (Weeks 5-6 of Challenge+X). The core pipeline, contradiction check, and evaluation harness work end to end against Unissant's hosted model. Front end, API, and blind testing are in progress. Full technical details, results, and the to-do list are in **[TECHNICAL.md](TECHNICAL.md)**.

**Showcase deck:** [TNUX Unissant Showcase Deck](https://claude.ai/artifact/SeZeysx3uUsC2kKFWLdPXF) (shared with the team; a PDF copy goes in `docs/` before the showcase).

This project is part of Challenge+X, Round 3, sponsored by **Unissant** (use case UC3).

## The problem

Officers write a legal narrative for every apprehension or arrest. Under volume, missing facts and citation errors slip through before the record is final, and reviews aren't consistent across officers and stations.

## What we built

A review step that reads an officer's narrative and reports, for each charge cited, which required facts are missing.

- **The LLM only extracts facts.** For each fact it returns the exact quote from the narrative. Anything it can't quote word for word is thrown out.
- **Code makes the decision.** A rules engine compares the facts found to a required-facts table for each charge, so the same narrative always gets the same report.
- **Contradiction check.** If the narrative states something that conflicts with the cited charge (for example "admitted on a B-2 visa" under a no-admission charge), the case goes to a person with the reason.
- **Human-review routing.** Unclear facts, conflicts, charges we don't cover, missing citations, and model outages all go to a person, never resolved by the tool.
- **Evidence-first report.** Every line links to a statute element, a quote, and the sentence it came from, so a reviewer can check it in seconds.
- **Metamorphic testing.** Code generates labeled test cases by deleting facts and changing case, spelling, abbreviations, and sentence order, so we can measure accuracy and consistency over hundreds of cases.

The tool never writes the narrative and never picks or suggests a charge. It only flags gaps and conflicts in what the officer already wrote.

## Results so far

On our own development cases (prompt v5, gpt-oss-20b, low reasoning). These will be re-measured on a blind test set.

| Unissant goal | Target | Current |
|---|---|---|
| Recall of real gaps | at least 90% | 100% (hand-written), 95% (generated) |
| False flags | at most 10% | 10% (hand-written), 9% (generated) |
| Ambiguous cases to a human | 100% | 8 of 8 |
| Time per review | under 60s | about 5.5s average, 16s max |

Known failures and what we're doing about them are in [TECHNICAL.md](TECHNICAL.md#known-failures).

## Data

Narratives are free text (officer-written legal prose), not structured fields. Example style:

> INADMISSIBILITY: 'John Doe' a citizen of Mexico. He has never had any documents that would allow him to be, or remain, in the United States legally. 'John Doe' is inadmissible under section 212(a)(6)(A)(i) of the INA...

The required-elements list per charge isn't provided as structured data. Unissant pointed us to the [USCIS Policy Manual, Vol. 7, Part L, Ch. 3](https://www.uscis.gov/policy-manual/volume-7-part-l-chapter-3), and we built our own table from it (`checks/elements/charge_elements.json`). It currently covers 212(a)(6)(A)(i), 212(a)(9)(A)(i), and 212(a)(6)(C)(i).

Synthetic and fictional data only. No real case records or names anywhere in this repo.

## Models and human review

- **Model:** `gpt-oss-20b`, hosted by Unissant. No other model is used. (Unissant allows any model; choice does not affect scoring.)
- **Where a human reviews:** every result is shown to a person. Cases are explicitly routed to a person when a fact is unclear, a conflict is found, the charge is not in our table, no charge is cited, repeated runs disagree, or the model is unavailable.

## Quick start

```
pip install -r requirements.txt
export CHALLENGEX_API_KEY=...          # never commit the key
python3 pipeline/run_sample.py 3       # check Unissant's sample narrative
python3 checks/eval/run_eval.py --workers 3 --repeat 3 --meta 60
python3 pipeline/batch.py checks/eval/cases_huy_cbp.jsonl --out reports   # one-page report per narrative
```

How to add test cases: [checks/eval/README.md](checks/eval/README.md). Report format for the front end: `pipeline/schemas.py` and `backend/sample_report.json`.

Start the review API with `uvicorn backend.app:app`. Send `POST /review` a JSON body such as `{"narrative": "..."}`; the response is the report. The API uses the model key from `CHALLENGEX_API_KEY`.

## Team: TNUX

| Name | Role | Responsibilities |
|---|---|---|
| Nasrullah "Naz" Hussain (lead, POC) | Technical lead | Architecture, LLM pipeline and prompts, rules engine, contradiction check, routing and guardrails, evaluation, security, main contact with Unissant |
| Jake Dwight Chan Israel | Grounding and evaluation | Blind test cases, review of expected answers, grounding and rule-based checks, co-owns the charge reference table |
| Ethan Cooper | Backend and integration | `/review` API, orchestration, report delivery, keeping each review under 60 seconds, reviews/merges PRs |
| Huy Ngoc Minh Truong | Search, data and frontend | Blind test cases, React review screen, MongoDB and test data handling, search/retrieval |

## Schedule (Challenge+X program weeks)

| Week | Dates | Phase | What we're doing |
|---|---|---|---|
| 1 | Sep 12-18 | Kickoff and Team Formation | Done |
| 2 | Sep 19-25 | Challenge Deep Dive and Early Mentorship | Done |
| 3-4 | Sep 26-Oct 9 | Concept Development and Sponsor Check-ins | Done. Reference table, pipeline design, model access |
| 5-6 | Oct 10-23 | Iteration and Real-World Validation | **We are here.** Pipeline, contradiction check, eval harness, and metamorphic tests built. Blind test set, API, and front end in progress |
| 7 | Oct 24-30 | Final Build and Pitch Prep | Fix failures found by blind testing, finish the UI, load test, scorecard slide, rehearse |
| 8 | Oct 31-Nov 7 | Final Showcase and Awards | Demo day, Saturday Nov 7 |

## Open questions

Resolved:
- ~~Which models are approved~~: Unissant provided hosted gpt-oss-20b, and teams may use any model or tool. Model choice does not affect scoring. We use gpt-oss-20b.
- ~~Does an encounter location count as place of entry~~: yes. An approximate location like "near Brownsville, TX" is acceptable (Unissant, Oct 27).
- ~~Narrative format~~: free text, not structured data.
- ~~Can the tool suggest charges~~: no.

Still open:
- How is a flag scored that is not in Unissant's answer key but is arguably valid?
- How large is the evaluation set beyond the sample?

## Repo structure

```
unissant-gap-analysis/
├── TECHNICAL.md     - design, features, results, remaining work
├── pipeline/        - LLM client, extraction, prompts, rules engine, voting, report builder (Naz)
├── checks/
│   ├── elements/    - required-facts table and fact definitions (Naz, Jake)
│   └── eval/        - eval harness, test cases, metamorphic generator (Naz, Jake)
├── backend/         - API and sample report (Ethan)
├── search/          - search/retrieval (Huy)
├── db/              - MongoDB models, test data handling (Huy)
├── ui/              - React frontend (Huy, not yet created)
└── data/            - Unissant's sample narrative; other data files are not committed (see .gitignore)
```
