import json
from concurrent.futures import ThreadPoolExecutor
from extract import extract
from run_sample import gap_report

def review(text, votes=3, chat=None):
    """Run the extraction `votes` times in parallel. A charge keeps its normal result only if every run
    produced the same gap report for it; otherwise it goes to a human with the facts the runs disagreed on."""
    with ThreadPoolExecutor(votes) as ex:
        runs = list(ex.map(lambda _: extract(text, chat), range(votes)))
    reps, out = [gap_report(s, c) for s, c, _ in runs], {}
    for k in reps[0]:
        rs = [r.get(k, {}) for r in reps]
        M, C = [set(r.get("missing", [])) for r in rs], [set(r.get("conflicts", [])) for r in rs]
        if len({json.dumps(r, sort_keys=True) for r in rs}) == 1:
            out[k] = dict(rs[0], disagreed=[])
        else:
            out[k] = {"status": "human_review", "reason": "extractions disagreed", "missing": sorted(set.intersection(*M)), "conflicts": sorted(set.intersection(*C)),
                      "disagreed": sorted((set.union(*M) - set.intersection(*M)) | (set.union(*C) - set.intersection(*C)))}
    return out, runs
