import os, sys, json, time, argparse, pathlib
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "pipeline"))
from extract import extract
from run_sample import gap_report

def run_case(c):
    t = time.time()
    try:
        sents, claims, dropped = extract(c["narrative"])
        return {"report": gap_report(sents, claims), "dropped": len(dropped), "secs": time.time() - t}
    except Exception as e:
        return {"error": repr(e), "secs": time.time() - t, "dropped": 0}

def score(c, r):
    tp = fn = fp = 0
    ok, why = "error" not in r, ([r["error"][:150]] if "error" in r else [])
    for k, e in c["expected"].items():
        a = r.get("report", {}).get(k, {})
        want, got = set(e["missing"]), set(a.get("missing", []))
        tp, fn, fp = tp + len(want & got), fn + len(want - got), fp + len(got - want)
        if a.get("status") != e["status"] or want != got:
            ok = False
            why.append(f"{k}: expected {e['status']} missing {sorted(want)}, got {a.get('status')} missing {sorted(got)}")
    if set(r.get("report", {})) - set(c["expected"]):
        ok = False
        why.append(f"unexpected charges flagged: {sorted(set(r['report']) - set(c['expected']))}")
    return tp, fn, fp, ok, why

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1, help="requests in flight at once (use 3+ to test concurrency)")
    ap.add_argument("--only", default="", help="comma-separated case ids")
    a = ap.parse_args()
    cases = [json.loads(l) for l in (HERE / "cases.jsonl").read_text().splitlines() if l.strip()]
    cases = [c for c in cases if not a.only or c["id"] in a.only.split(",")]
    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        results = list(ex.map(run_case, cases))
    wall = time.time() - t0
    tp = fn = fp = 0
    head, amb, route, by_author = [], [], [], {}
    for c, r in zip(cases, results):
        ctp, cfn, cfp, ok, why = score(c, r)
        is_amb = "ambiguous" in c["tags"]
        print(f"{'PASS' if ok else 'FAIL'} {c['id']} {r['secs']:5.1f}s  {','.join(c['tags'])}{'  (ambiguous: not in headline score)' if is_amb else ''}")
        for w in why:
            print("      " + w)
        (amb if is_amb else head).append(ok)
        by_author.setdefault(c["author"], []).append(ok)
        if not is_amb:
            tp, fn, fp = tp + ctp, fn + cfn, fp + cfp
        if any(e["status"] == "human_review" for e in c["expected"].values()):
            route.append(all(r.get("report", {}).get(k, {}).get("status") == "human_review" for k, e in c["expected"].items() if e["status"] == "human_review"))
    secs = [r["secs"] for r in results]
    print(f"\nsettings: PROMPT_VERSION={os.environ.get('PROMPT_VERSION', 'v2')} REASONING_EFFORT={os.environ.get('REASONING_EFFORT', 'default')} workers={a.workers}")
    print(f"cases passed (headline): {sum(head)}/{len(head)}   ambiguous cases passed: {sum(amb)}/{len(amb)}")
    print(f"recall of planted gaps: {tp}/{tp + fn} = {tp / max(tp + fn, 1):.0%}   (goal 90%)")
    print(f"false flags: {fp} of {tp + fp} flags raised = {fp / max(tp + fp, 1):.0%}   (goal at most 10%)")
    print(f"human-review routing: {sum(route)}/{len(route)}   (goal 100%)")
    print(f"latency per review: mean {sum(secs) / len(secs):.1f}s, max {max(secs):.1f}s   (goal under 60s)   wall time {wall:.0f}s")
    print(f"claims dropped as ungrounded: {sum(r['dropped'] for r in results)}")
    print("by author: " + ", ".join(f"{k} {sum(v)}/{len(v)}" for k, v in by_author.items()))
