"""Builds the review result in the shape the front end, API and batch reports use. See pipeline/schemas.py for the contract."""
import json, os, time
from concurrent.futures import ThreadPoolExecutor
from extract import extract, split_sentences, VERSION, ROOT
from run_sample import gap_report, with_derived, TABLE
from review import review

# hard limit per review: the client timeout covers each network wait, not the whole call
DEADLINE, POOL = float(os.environ.get("REVIEW_DEADLINE", 50)), ThreadPoolExecutor(8)
DISCLAIMER = "Flags missing or conflicting documentation only. It does not judge the case or suggest charges. A person reviews every result."
PLAIN = {k: v for k, v in json.loads((ROOT / "checks/elements/fact_plain.json").read_text()).items() if not k.startswith("_")}

def build_report(text, votes=1, chat=None):
    t = time.time()
    out = {"version": "2", "model": os.environ.get("LLM_MODEL", "gpt-oss-20b"), "prompt_version": VERSION, "votes": votes, "disclaimer": DISCLAIMER, "sentences": split_sentences(text)}
    try:
        if votes > 1:
            gaps, runs = POOL.submit(review, text, votes, chat).result(timeout=DEADLINE)
            claims = runs[0][1]
        else:
            _, claims, _ = POOL.submit(extract, text, chat).result(timeout=DEADLINE)
            gaps = gap_report(out["sentences"], claims)
    except Exception as e:
        why = f"The model was unavailable ({type(e).__name__}), so this narrative was not checked. A person should review it by hand."
        return dict(out, seconds=round(time.time() - t, 1), human_review=True, multiple_charges=None,
                    flags=[{"type": "model_unavailable", "charge": None, "fact_type": None, "reason": why, "sentence_ids": []}],
                    charges=[{"citation": None, "name": None, "source": None, "status": "human_review", "reason": why, "cited_in": [], "facts": [], "missing": [], "conflicts": [], "disagreed": [],
                              "citation_check": {"result": "not_checked", "reason": why}}])
    by, charges, flags = {}, [], []
    for c in with_derived(claims):
        by.setdefault(c["fact_type"], c)
    ev = lambda f: {x: by[f].get(x) for x in ("quote", "sentence_ids", "confidence")} if f in by else {"quote": None, "sentence_ids": [], "confidence": None}
    flag = lambda typ, k, f, why, ids: flags.append({"type": typ, "charge": k, "fact_type": f, "reason": why, "sentence_ids": ids})
    multi = gaps.pop("multiple_charges_cited", None)
    for k, g in gaps.items():
        row, cite, at = TABLE.get(k, {}), None if k == "no_charge_cited" else k, g.get("cited_in", [])
        name, miss, conf, unsure, dis = row.get("name"), g.get("missing", []), g.get("conflicts", []), g.get("low_confidence", []), g.get("disagreed", [])
        label = f"{k} ({name})" if name else k
        if not cite:
            check = ("no_citation", "The narrative does not cite a charge, so there is nothing to check it against. A person should review it.")
            flag("no_citation", None, None, check[1], [])
        elif not row:
            check = ("not_in_reference_table", f"{k} is not in our reference table, so the tool cannot check its required facts. A person should review it.")
            flag("unknown_charge", k, None, check[1], at)
        elif conf:
            check = ("likely_mismatch", f"The narrative states facts that conflict with {label}: " + "; ".join(f"“{by[f]['quote']}”" for f in conf if f in by) + ". The tool does not suggest another charge.")
            for f in conf:
                flag("conflict", k, f, f"This conflicts with {label}: the narrative includes {PLAIN.get(f, f)}" + (f" (“{by[f]['quote']}”)." if f in by else "."), ev(f)["sentence_ids"])
        elif miss:
            check = ("incomplete", f"{len(miss)} of {len(row['required_facts'])} facts that {k} requires {'is' if len(miss) == 1 else 'are'} not stated: {', '.join(PLAIN.get(f, f) for f in miss)}.")
        elif g["status"] == "human_review":
            check = ("needs_review", f"Some facts for {k} are unclear: {', '.join(PLAIN.get(f, f) for f in unsure + dis)}. A person should confirm them.")
        else:
            check = ("supported", f"Every fact {k} requires is stated, and none conflicts with it.")
        for f in miss:
            flag("missing", k, f, f"{label} requires {PLAIN.get(f, f)}. The narrative does not state it.", at)
        for f in unsure + dis:
            flag("unclear", k, f, f"{label} requires {PLAIN.get(f, f)}. The narrative states it unclearly, so a person should confirm it.", ev(f)["sentence_ids"] or at)
        bad = set(miss) | set(dis)
        charges.append({"citation": cite, "name": name, "source": row.get("source"), "status": g["status"], "cited_in": at,
            "reason": g.get("reason") or (check[1] if g["status"] == "human_review" else None),
            "citation_check": {"result": check[0], "reason": check[1]},
            "facts": [dict(fact_type=f, label=f.replace("_", " "), found=f not in bad, derived=bool(f in by and by[f].get("derived")), **(ev(f) if f not in bad else ev(None))) for f in row.get("required_facts", [])],
            "missing": miss, "conflicts": [dict(fact_type=f, **ev(f)) for f in conf], "disagreed": dis})
    if multi:
        flag("multiple_charges", None, None, f"The narrative cites {len(multi['charges'])} charges ({', '.join(multi['charges'])}). Multi-charge cases go to a person; each charge is still checked below.", sorted({i for c in charges for i in c["cited_in"]}))
    return dict(out, seconds=round(time.time() - t, 1), human_review=bool(multi) or any(c["status"] == "human_review" for c in charges),
                multiple_charges=multi and multi["charges"], flags=flags, charges=charges)
