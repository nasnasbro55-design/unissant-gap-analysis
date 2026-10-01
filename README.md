# GenAI-Assisted Gap Analysis for Investigative Charge Documentation

**Status:** Provisional — we're in Concept Development (Weeks 3-4 of Challenge+X), not the build phase yet. Details below will firm up as we get more from Unissant and start building.

This project is part of Challenge+X, Round 3, sponsored by **Unissant** (use case UC3).

## The problem

Officers write a legal narrative for every apprehension or arrest. Under volume, missing facts and citation errors slip through before the record is final, and reviews aren't consistent across officers and stations.

## The idea

A GenAI-assisted review step that sits in the investigative case workflow:

- **Required-element check** — for each charge an officer cites, verify the narrative states every fact that charge requires (e.g. country of citizenship, manner of entry, prior removal history)
- **Citation check** — confirm the facts in the narrative actually support the charge cited, flagging mismatches
- **Human-review routing** — ambiguous or low-confidence cases get routed to a person, never resolved by the tool

The tool never writes the narrative and never picks or suggests the charge — it only flags gaps and mismatches against what the officer already wrote.

## Data

Narratives are free text (officer-written legal prose), not structured fields. Example style:

> INADMISSIBILITY: 'John Doe' a citizen of Mexico. He has never had any documents that would allow him to be, or remain, in the United States legally. 'John Doe' is inadmissible under section 212(a)(6)(A)(i) of the INA...

The required-elements list per charge isn't provided as structured data — Unissant pointed us to the [USCIS Policy Manual, Vol. 7, Part L, Ch. 3](https://www.uscis.gov/policy-manual/volume-7-part-l-chapter-3) for inadmissibility grounds. We're building our own `charge -> required elements` reference table from that.

Synthetic data only, no real case records.

## Team — TNUX

| Name | Role | Responsibilities |
|---|---|---|
| Nasrullah "Naz" Hussain (lead, POC) | Technical lead | Architecture, LLM pipeline & prompts (gap check + citation check), human-review routing and guardrails, security, main contact with Unissant |
| Jake Dwight Chan Israel | Grounding & evaluation | Sentence/field grounding, rule-based checks (dates, names, A-numbers, empty fields), eval harness scoring against required elements, co-owns the charge reference table |
| Ethan Cooper | Backend & integration | API, orchestration, report generation, keeping each review under 60 seconds, reviews/merges PRs |
| Huy Ngoc Minh Truong | Search, data & frontend | AI search/retrieval for citation grounding, MongoDB and test data handling, React frontend |

## Schedule (Challenge+X program weeks)

| Week | Dates | Phase | What we're doing |
|---|---|---|---|
| 1 | Sep 12-18 | Kickoff & Team Formation | Done |
| 2 | Sep 19-25 | Challenge Deep Dive & Early Mentorship | Done |
| 3-4 | Sep 26-Oct 9 | Concept Development & Sponsor Check-ins | ← We are here. Building the charge/required-elements reference table, finalizing pipeline design, confirming approved AI tools |
| 5-6 | Oct 10-23 | Iteration & Real-World Validation | Build the gap-check pipeline, citation checker, routing logic, backend, and eval harness against synthetic narratives |
| 7 | Oct 24-30 | Final Build & Pitch Prep | Polish, reports/dashboard, rehearse pitch |
| 8 | Oct 31-Nov 7 | Final Showcase & Awards | Demo day |

## Open questions (resolving during concept development)

- Which AI services/models are GMU-approved — Unissant is still working this out
- How a flag not in Unissant's internal answer key but arguably still valid gets scored
- Exact format of the synthetic narrative set and how large it is beyond the sample
- Whether ambiguous human-review output can reference the elements that are unclear without naming candidate charges

## Repo structure

```
unissant-gap-analysis/
├── pipeline/   - architecture, prompts, routing/guardrails (Naz)
├── checks/     - grounding, rule-based checks, eval harness (Jake)
├── backend/    - API, orchestration, report generation (Ethan)
├── search/     - AI search/retrieval for citation grounding (Huy)
├── db/         - MongoDB models, test data handling (Huy)
├── ui/         - React frontend (Huy)
├── data/       - synthetic narratives, answer key (not committed - see .gitignore)
└── docs/       - architecture notes, meeting notes, decisions
```
