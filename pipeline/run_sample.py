import sys, json, re, time
from extract import extract, ROOT

TABLE = json.loads((ROOT / "checks/elements/charge_elements.json").read_text())
KEYS = {re.sub(r"\s+", "", k.lower()): k for k in TABLE}
CITE = r"212\s*\(\s*a\s*\)\s*\(\s*\d+\s*\)\s*\(\s*\w\s*\)\s*\(\s*\w+\s*\)"
EXPECTED = {"212(a)(6)(A)(i)": ["place_of_entry"], "212(a)(9)(A)(i)": ["prior_removal_date"]}

def gap_report(sents, claims):
    seen, report = {}, {}
    for c in claims:
        seen.setdefault(c["fact_type"], set()).add(c["confidence"])
    for m in re.finditer(CITE, " ".join(sents.values()), re.I):
        n = re.sub(r"\s+", "", m.group(0).lower())
        k = KEYS.get(n, n)
        if k in report:
            continue
        if k not in TABLE:
            report[k] = {"status": "human_review", "reason": "charge not in reference table"}
            continue
        miss = sorted(f for f in TABLE[k]["required_facts"] if f not in seen)
        unsure = sorted(f for f in TABLE[k]["required_facts"] if f in seen and not seen[f] & {"high", "medium"})
        report[k] = {"status": "gaps" if miss else "human_review" if unsure else "complete", "missing": miss, "low_confidence": unsure}
    return report

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
