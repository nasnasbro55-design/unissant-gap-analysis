"""Load test: send reviews at increasing concurrency and report latency, timeouts and failures.

Start the API first (in its own Terminal window, with CHALLENGEX_API_KEY set):
    python3 -m uvicorn backend.app:app --port 8000
Then:
    python3 checks/load_test.py                          # 1, 3, 6, 10 at once; 10 reviews per level (40 total)
    python3 checks/load_test.py --levels 1,5 --requests 5
    python3 checks/load_test.py --direct                 # skip the API and call the pipeline directly

The model server is shared with other teams, so keep runs small and do not loop this.
"""
import argparse, json, pathlib, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
NARR = [json.loads(l)["narrative"] for l in (ROOT / "checks/eval/cases.jsonl").read_text().splitlines() if l.strip()]

def via_api(url, text):
    req = urllib.request.Request(url, json.dumps({"narrative": text}).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def one(fn, text):
    t = time.time()
    try:
        rep = fn(text)
        return time.time() - t, "unavailable" if any("model unavailable" in (c.get("reason") or "") for c in rep.get("charges", [])) else "ok"
    except Exception as e:
        return time.time() - t, f"error {type(e).__name__}: {str(e)[:80]}"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/review")
    ap.add_argument("--levels", default="1,3,6,10", help="how many reviews in flight at once, per step")
    ap.add_argument("--requests", type=int, default=10, help="reviews sent at each level")
    ap.add_argument("--direct", action="store_true", help="call build_report directly instead of the API")
    a = ap.parse_args()
    if a.direct:
        sys.path.insert(0, str(ROOT / "pipeline"))
        from report import build_report
        fn = build_report
    else:
        fn = lambda text: via_api(a.url, text)
        try:
            urllib.request.urlopen(a.url.rsplit("/", 1)[0] + "/docs", timeout=5)
        except Exception:
            sys.exit(f"Can't reach the API at {a.url}. Start it first: python3 -m uvicorn backend.app:app --port 8000")
    print(f"{'at once':>7} {'ok':>4} {'model down':>10} {'errors':>6} {'median':>7} {'p95':>6} {'max':>6} {'over 60s':>8} {'per min':>7}")
    for lv in map(int, a.levels.split(",")):
        t0 = time.time()
        with ThreadPoolExecutor(lv) as ex:
            res = list(ex.map(lambda i: one(fn, NARR[i % len(NARR)]), range(a.requests)))
        wall, s = time.time() - t0, sorted(r[0] for r in res)
        errs = [r[1] for r in res if r[1].startswith("error")]
        print(f"{lv:>7} {sum(r[1] == 'ok' for r in res):>4} {sum(r[1] == 'unavailable' for r in res):>10} {len(errs):>6} {s[len(s) // 2]:>6.1f}s {s[int(0.95 * (len(s) - 1))]:>5.1f}s {s[-1]:>5.1f}s {sum(x > 60 for x in s):>8} {len(res) / wall * 60:>7.1f}")
        for e in sorted(set(errs)):
            print("        " + e)
    print("\n'model down' = the 40s timeout fired and the review was sent to a human, which is the safe failure. 'errors' = the API itself failed.")
