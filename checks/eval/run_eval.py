import os, sys, json, time, argparse, pathlib
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "pipeline"))
from extract import extract
from run_sample import gap_report
from review import review

VOTES = 1

def run_case(c):
    t = time.time()
    try:
        if VOTES > 1:
            report, runs = review(c["narrative"], VOTES)
            return {"report": report, "claims": runs[0][1], "dropped": runs[0][2], "secs": time.time() - t}
        sents, claims, dropped = extract(c["narrative"])
        return {"report": gap_report(sents, claims), "claims": claims, "dropped": dropped, "secs": time.time() - t}
    except Exception as e:
        return {"error": repr(e), "claims": [], "dropped": [], "secs": time.time() - t}

def score(c, r):
    tp = fn = fp = 0
    ok, why = "error" not in r, ([r["error"][:150]] if "error" in r else [])
    for k, e in c["expected"].items():
        a = r.get("report", {}).get(k, {})
        want, got = set(e["missing"] or []), set(a.get("missing", []))
        tp, fn, fp = (tp + len(want & got), fn + len(want - got), fp + len(got - want)) if e["missing"] is not None else (tp, fn, fp)
        if a.get("status") != e["status"] or (e["missing"] is not None and want != got):
            ok = False
            why.append(f"{k}: expected {e['status']} missing {sorted(want)}, got {a.get('status')} missing {sorted(got)}")
    if set(r.get("report", {})) - set(c["expected"]):
        ok = False
        why.append(f"unexpected charges flagged: {sorted(set(r['report']) - set(c['expected']))}")
    return tp, fn, fp, ok, why

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1, help="requests in flight at once (use 3+ to test concurrency)")
    ap.add_argument("--repeat", type=int, default=1, help="run the whole set N times and report which cases changed between runs")
    ap.add_argument("--votes", type=int, default=1, help="run each extraction N times in parallel; any disagreement sends that charge to a human")
    ap.add_argument("--meta", type=int, default=0, help="also run N generated metamorphic cases (see metamorphic.py)")
    ap.add_argument("--seed", type=int, default=1, help="seed for --meta")
    ap.add_argument("--only", default="", help="comma-separated case ids")
    a = ap.parse_args()
    if not os.environ.get("CHALLENGEX_API_KEY"):
        sys.exit("CHALLENGEX_API_KEY is not set in this Terminal window. Set it first (see README), then rerun.")
    VOTES = a.votes
    cases = [json.loads(l) for f in sorted(HERE.glob("cases*.jsonl")) for l in f.read_text().splitlines() if l.strip()]
    if a.meta:
        sys.path.insert(0, str(HERE))
        from metamorphic import generate
        cases += generate(a.meta, a.seed)
    cases = [c for c in cases if not a.only or c["id"] in a.only.split(",")]
    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        runs = [list(ex.map(run_case, cases)) for _ in range(a.repeat)]
    wall, results = time.time() - t0, runs[0]
    tp = fn = fp = 0
    head, amb, route, by_author, meta = [], [], [], {}, []
    for c, r in zip(cases, results):
        ctp, cfn, cfp, ok, why = score(c, r)
        ab = not ok and any(v.get("reason") == "extractions disagreed" for v in r.get("report", {}).values())
        if "meta" in c["tags"]:
            meta.append((c, ok, ctp, cfn, cfp, ab))
            if not ok:
                print(f"{'ABST' if ab else 'FAIL'} {c['id']} {','.join(c['tags'])}: " + "; ".join(why))
            continue
        is_amb = "ambiguous" in c["tags"]
        print(f"{'PASS' if ok else 'ABST' if ab else 'FAIL'} {c['id']} {r['secs']:5.1f}s  {','.join(c['tags'])}{'  (ambiguous: not in headline score)' if is_amb else ''}")
        for w in why:
            print("      " + w)
        for cl in ([] if ok else r["claims"]):
            print(f"      - {cl['fact_type']} [{cl['confidence']}] {cl['quote']!r}")
        for cl in ([] if ok else r["dropped"]):
            print(f"      x DROPPED {cl.get('fact_type')} {cl.get('quote')!r}")
        (amb if is_amb else head).append("pass" if ok else "abst" if ab else "fail")
        by_author.setdefault(c["author"], []).append(ok)
        if not is_amb and not ab:
            tp, fn, fp = tp + ctp, fn + cfn, fp + cfp
        if any(e["status"] == "human_review" for e in c["expected"].values()):
            route.append(all(r.get("report", {}).get(k, {}).get("status") == "human_review" for k, e in c["expected"].items() if e["status"] == "human_review"))
    secs = [r["secs"] for r in results]
    print(f"\nsettings: PROMPT_VERSION={os.environ.get('PROMPT_VERSION', 'v5')} REASONING_EFFORT={os.environ.get('REASONING_EFFORT', 'low')} workers={a.workers} repeat={a.repeat} votes={a.votes}")
    print(f"cases passed (headline): {head.count('pass')}/{len(head)}   sent to human because runs disagreed: {head.count('abst')}   wrong: {head.count('fail')}   ambiguous cases passed: {amb.count('pass')}/{len(amb)}")
    print(f"accuracy when the tool gave an answer: {head.count('pass')}/{head.count('pass') + head.count('fail')}")
    print(f"recall of planted gaps: {tp}/{tp + fn} = {tp / max(tp + fn, 1):.0%}   (goal 90%)")
    print(f"false flags: {fp} of {tp + fp} flags raised = {fp / max(tp + fp, 1):.0%}   (goal at most 10%)")
    print(f"human-review routing: {sum(route)}/{len(route)}   (goal 100%)")
    print(f"latency per review (first run): mean {sum(secs) / len(secs):.1f}s, max {max(secs):.1f}s   (goal under 60s)   wall time {wall:.0f}s")
    print(f"claims dropped as ungrounded: {sum(len(r['dropped']) for r in results)}")
    print("by author: " + ", ".join(f"{k} {sum(v)}/{len(v)}" for k, v in by_author.items()))
    if meta:
        mt, mf, mp = (sum(m[i] for m in meta if not m[5]) for i in (2, 3, 4))
        print(f"\nmetamorphic ({len(meta)} generated cases, seed {a.seed}): passed {sum(m[1] for m in meta)}/{len(meta)}   sent to human: {sum(m[5] for m in meta)}   wrong: {sum(not m[1] and not m[5] for m in meta)}   recall {mt}/{mt + mf}   false flags {mp} of {mt + mp}")
        for t in sorted({x for m in meta for x in m[0]["tags"] if x != "meta"}):
            g = [m for m in meta if t in m[0]["tags"]]
            print(f"   {t:<18} {sum(m[1] for m in g)}/{len(g)}")
    if a.repeat > 1:
        flaky = [(c["id"], sum(score(c, r[i])[3] for r in runs)) for i, c in enumerate(cases)]
        print("passed in only some runs: " + (", ".join(f"{k} {n}/{a.repeat}" for k, n in flaky if 0 < n < a.repeat) or "none"))
        print("failed in every run: " + (", ".join(k for k, n in flaky if n == 0) or "none"))
        unstable = [c["id"] for i, c in enumerate(cases) if len({json.dumps(r[i].get("report"), sort_keys=True) for r in runs}) > 1]
        print(f"stability over {a.repeat} runs: {len(cases) - len(unstable)}/{len(cases)} cases gave the same gap report every time; changed: {unstable}")
