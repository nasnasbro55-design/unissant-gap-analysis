"""Builds the review result in the shape the front end and API use. See pipeline/schemas.py for the contract."""
import os, time
from concurrent.futures import ThreadPoolExecutor
from extract import extract, split_sentences, VERSION
from run_sample import gap_report, TABLE
from review import review

# hard limit per review: the client timeout covers each network wait, not the whole call
DEADLINE, POOL = float(os.environ.get("REVIEW_DEADLINE", 50)), ThreadPoolExecutor(8)
DISCLAIMER = "Flags missing documentation only. It does not judge the case or suggest charges. A person reviews every result."

def build_report(text, votes=1, chat=None):
    t = time.time()
    out = {"version": "1", "model": "gpt-oss-20b", "prompt_version": VERSION, "votes": votes, "disclaimer": DISCLAIMER, "sentences": split_sentences(text)}
    try:
        if votes > 1:
            gaps, runs = POOL.submit(review, text, votes, chat).result(timeout=DEADLINE)
            claims = runs[0][1]
        else:
            _, claims, _ = POOL.submit(extract, text, chat).result(timeout=DEADLINE)
            gaps = gap_report(out["sentences"], claims)
    except Exception as e:
        return dict(out, seconds=round(time.time() - t, 1), charges=[{"citation": None, "name": None, "source": None, "status": "human_review", "reason": f"model unavailable ({type(e).__name__}); review this narrative by hand", "facts": [], "missing": [], "conflicts": [], "disagreed": []}])
    by, charges = {c["fact_type"]: c for c in claims}, []
    for k, g in gaps.items():
        row, bad = TABLE.get(k, {}), set(g.get("missing", [])) | set(g.get("disagreed", []))
        ev = lambda f: {x: by[f][x] for x in ("quote", "sentence_ids", "confidence")} if f in by else {"quote": None, "sentence_ids": [], "confidence": None}
        charges.append({"citation": None if k == "no_charge_cited" else k, "name": row.get("name"), "source": row.get("source"), "status": g["status"],
            "reason": g.get("reason") or ("the narrative states facts that conflict with this charge" if g.get("conflicts") else f"low confidence on: {', '.join(g['low_confidence'])}" if g.get("low_confidence") and g["status"] == "human_review" else None),
            "facts": [dict(fact_type=f, label=f.replace("_", " "), found=f not in bad, **(ev(f) if f not in bad else ev(None))) for f in row.get("required_facts", [])],
            "missing": g.get("missing", []), "conflicts": [dict(fact_type=f, **ev(f)) for f in g.get("conflicts", [])], "disagreed": g.get("disagreed", [])})
    return dict(out, seconds=round(time.time() - t, 1), charges=charges)
