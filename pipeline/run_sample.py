import sys, json, re, time
from extract import extract, locate, ROOT

TABLE = json.loads((ROOT / "checks/elements/charge_elements.json").read_text())
KEYS = {re.sub(r"\s+", "", k.lower()): k for k in TABLE}
_SUB = r"\(\s*\d+\s*\)(?:\s*\(\s*[A-Za-z]{1,4}\s*\)){1,3}"
# INA 212(a)..., Title 8 U.S.C. sections (1182(a)... maps to INA 212(a)...), INA 237(a)... and INA 275/276 (criminal entry/reentry)
CITE = re.compile(rf"(?P<ina>212\s*\(\s*a\s*\)\s*{_SUB})|(?P<usc>8\s*U\.?\s*S\.?\s*C\.?\s*(?:§+\s*)?(?:sec(?:tion|\.)?\s*)?(?P<sec>1\d{{3}})(?P<sub>(?:\s*\(\s*\w{{1,4}}\s*\))*))"
                  rf"|(?P<dep>237\s*\(\s*a\s*\)\s*{_SUB})|(?P<crim>\b(?:INA|section)\s*(?:§+\s*)?(?P<cnum>27[56])\b(?P<csub>(?:\s*\(\s*\w{{1,4}}\s*\))*))", re.I)
EXPECTED = {"212(a)(6)(A)(i)": ["place_of_entry"], "212(a)(9)(A)(i)": ["prior_removal_date"]}

def cite_key(m):
    t = lambda x: re.sub(r"\s+", "", x or "").lower()
    k = (t(m["ina"]) if m["ina"] else ("212" + t(m["sub"]) if m["sec"] == "1182" else f"8 U.S.C. {m['sec']}{t(m['sub'])}") if m["usc"]
         else t(m["dep"]) if m["dep"] else f"INA {m['cnum']}{t(m['csub'])}")
    return KEYS.get(k, k)

def with_derived(claims):
    """In a reentry, an admission phrase in the same sentence as the reentry ("re-entered ... without being admitted")
    also states admission status at reentry. The model often records it only once, so code fills in the second fact."""
    ok = lambda f: [c for c in claims if c["fact_type"] == f and c["confidence"] in ("high", "medium")]
    if any(c["fact_type"] == "admitted_status_at_reentry" for c in claims):
        return claims
    ids = {i for c in ok("reentry_or_attempted_reentry") for i in c["sentence_ids"]}
    return claims + [dict(c, fact_type="admitted_status_at_reentry", derived=True) for c in ok("admitted_or_paroled_status") if ids & set(c["sentence_ids"])][:1]

def gap_report(sents, claims):
    seen, report, claims = {}, {}, with_derived(claims)
    for c in claims:
        seen.setdefault(c["fact_type"], set()).add(c["confidence"])
    for m in CITE.finditer(" ".join(sents.values())):
        k = cite_key(m)
        if k in report:
            continue
        where = locate(m.group(0), sents)
        if k not in TABLE:
            report[k] = {"status": "human_review", "reason": "charge not in reference table", "cited_in": where}
            continue
        miss = sorted(f for f in TABLE[k]["required_facts"] if f not in seen)
        unsure = sorted(f for f in TABLE[k]["required_facts"] if f in seen and not seen[f] & {"high", "medium"})
        conf = sorted({f for f in TABLE[k].get("contradicted_by", []) if seen.get(f, set()) & {"high", "medium"}}
                      | {c["fact_type"] for c in claims if c["confidence"] in ("high", "medium") and c["fact_type"] in TABLE[k].get("contradicted_by_stance", {})
                         and str(c.get("admitted")).lower() == str(TABLE[k]["contradicted_by_stance"][c["fact_type"]]).lower()})
        report[k] = {"status": "human_review" if conf else "gaps" if miss else "human_review" if unsure else "complete", "missing": miss, "low_confidence": unsure, "conflicts": conf, "cited_in": where}
    if len(report) > 1:
        report["multiple_charges_cited"] = {"status": "human_review", "reason": f"the narrative cites {len(report)} charges; multi-charge cases go to a person", "charges": list(report)}
    return report or {"no_charge_cited": {"status": "human_review", "reason": "no charge citation found in narrative"}}

if __name__ == "__main__":
    from llm_client import chat
    text, runs, reports = (ROOT / "data/sample_narrative.txt").read_text(), int(sys.argv[1]) if len(sys.argv) > 1 else 1, []
    for i in range(runs):
        t = time.time()
        sents, claims, dropped = extract(text)
        reports.append(json.dumps(gap_report(sents, claims), sort_keys=True, indent=2))
        u = getattr(chat, "usage", None)
        print(f"--- run {i + 1}: {time.time() - t:.1f}s, {len(claims)} claims kept, {len(dropped)} dropped (not grounded in the text)")
        if u:
            print(f"  tokens: {u.prompt_tokens} in, {u.completion_tokens} out ({getattr(u.completion_tokens_details, 'reasoning_tokens', None)} of them reasoning)")
        for c in claims:
            print(f"  {c['sentence_ids']} {c['fact_type']} [{c['confidence']}] {c['quote']!r}")
        for c in dropped:
            print(f"  DROPPED: {c}")
    print("\n" + reports[-1])
    print("\nidentical gap report across all runs:", len(set(reports)) == 1)
    got = json.loads(reports[-1])
    for k, want in EXPECTED.items():
        print(f"expected gaps for {k}: {want} ->", "MATCH" if got.get(k, {}).get("missing") == want else f"MISMATCH (got {got.get(k)})")
