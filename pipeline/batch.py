"""Review many narratives and write a one-page gap report for each.

    python3 pipeline/batch.py INPUT [--out reports] [--workers 3]

INPUT is a folder of .txt files (one narrative each), a .jsonl file (one {"id", "narrative"} per line),
or a .csv file with a "narrative" column (and optionally "id"). Writes, in --out:
    <id>.html     one-page printable report (Print > Save as PDF gives the PDF)
    <id>.json     the full report, same shape as the API
    index.html    summary table linking every report
    summary.csv   one row per narrative
"""
import argparse, csv, html, json, pathlib, re, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from report import build_report

STATUS = {"complete": ("Complete", "#2B5C94"), "gaps": ("Gaps found", "#9A5410"), "human_review": ("Human review", "#14213D")}
CHECK = {"supported": "Supported", "incomplete": "Incomplete", "likely_mismatch": "Likely mismatch", "needs_review": "Needs review",
         "not_in_reference_table": "Not in reference table", "no_citation": "No charge cited", "not_checked": "Not checked"}
CSS = """@page{size:letter;margin:0.5in}body{font:10.5pt/1.4 'IBM Plex Sans',Arial,sans-serif;color:#14213D;max-width:7.5in;margin:24px auto;background:#F7F5EF}
h1{font:600 16pt Georgia,serif;margin:0 0 2px}.meta{color:#5A6372;font-size:9pt}.banner{color:#F7F5EF;padding:8px 12px;border-radius:6px;font-weight:600;margin:10px 0}
h2{font-size:11pt;margin:12px 0 4px;text-transform:uppercase;letter-spacing:1px;color:#5A6372}table{border-collapse:collapse;width:100%;font-size:9.5pt}
td,th{border-bottom:1px solid #D9D3C4;padding:4px 6px;text-align:left;vertical-align:top}ol{margin:0;padding-left:20px}li{margin:3px 0}
.n{font:9pt 'IBM Plex Mono','Courier New',monospace;background:#FFFDF8;border:1px solid #D9D3C4;border-radius:6px;padding:8px 10px}
.n p{margin:2px 0}.sid{color:#9A5410;font-weight:600}mark{background:#DCE8F5;color:#14213D}.foot{color:#5A6372;font-size:8.5pt;margin-top:10px}
@media print{body{margin:0;background:#fff}}"""

def load(path):
    p = pathlib.Path(path)
    if p.is_dir():
        return [(f.stem, f.read_text()) for f in sorted(p.glob("*.txt"))]
    if p.suffix == ".jsonl":
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        return [(str(r.get("id", i + 1)), r["narrative"]) for i, r in enumerate(rows)]
    if p.suffix == ".csv":
        return [(str(r.get("id") or i + 1), r["narrative"]) for i, r in enumerate(csv.DictReader(p.open(newline="", encoding="utf-8-sig")))]
    sys.exit("INPUT must be a folder of .txt files, a .jsonl file, or a .csv file")

def marked(sent, quotes):
    """Highlight every found quote inside one sentence (case- and spacing-insensitive)."""
    low, spans = sent.lower(), []
    for q in quotes:
        i = low.find(" ".join(str(q).split()).lower()) if q else -1
        if i >= 0:
            spans.append((i, i + len(" ".join(str(q).split()))))
    out, pos = "", 0
    for a, b in sorted(spans):
        if a >= pos:
            out, pos = out + html.escape(sent[pos:a]) + "<mark>" + html.escape(sent[a:b]) + "</mark>", b
    return out + html.escape(sent[pos:])

def page(rid, rep):
    e = html.escape
    overall = "human_review" if rep.get("human_review") else "gaps" if any(c["missing"] for c in rep["charges"]) else "complete"
    label, color = STATUS[overall]
    found = {}
    for c in rep["charges"]:
        for f in c["facts"] + c["conflicts"]:
            for i in f.get("sentence_ids") or []:
                found.setdefault(i, []).append(f.get("quote"))
    checks = "".join(f"<tr><td><b>{e(c['citation'] or '(none)')}</b><br>{e(c['name'] or '')}</td><td><b>{e(CHECK.get(c['citation_check']['result'], c['citation_check']['result']))}</b></td><td>{e(c['citation_check']['reason'])}</td></tr>" for c in rep["charges"])
    flags = "".join(f"<li>{e(f['reason'])}" + (f" <span class='sid'>[{', '.join(f['sentence_ids'])}]</span>" if f["sentence_ids"] else "") + "</li>" for f in rep["flags"]) or "<li>No flags. Every required fact is stated.</li>"
    narr = "".join(f"<p><span class='sid'>{k}</span> {marked(v, found.get(k, []))}</p>" for k, v in rep["sentences"].items())
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Gap report {e(rid)}</title><style>{CSS}</style></head><body>
<h1>Gap report: {e(rid)}</h1><div class="meta">{time.strftime('%Y-%m-%d %H:%M')} · model {e(rep['model'])} · prompt {e(rep['prompt_version'])} · {rep['seconds']}s</div>
<div class="banner" style="background:{color}">{label}{' · send to a person' if overall == 'human_review' else ''}</div>
<h2>Citation check</h2><table><tr><th style="width:24%">Charge cited</th><th style="width:18%">Result</th><th>Reason</th></tr>{checks}</table>
<h2>Form I-213 fields</h2><table>{''.join(f"<tr><td style='width:38%'>{e(r['block'])}</td><td>{'Stated' if not r['not_stated'] else 'Not stated: ' + e(', '.join(x.replace('_', ' ') for x in r['not_stated']))}</td><td style='width:14%'>{e(', '.join(r['sentence_ids']))}</td></tr>" for r in rep.get('i213', []))}</table>
<h2>Flags</h2><ol>{flags}</ol>
<h2>Narrative</h2><div class="n">{narr}</div><div class="meta" style="margin-top:4px">Highlighted text is the exact quote behind each fact found. [S#] points to a sentence.</div>
<div class="foot">{e(rep['disclaimer'])}</div></body></html>"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    if not __import__("os").environ.get("CHALLENGEX_API_KEY"):
        sys.exit("CHALLENGEX_API_KEY is not set in this Terminal window. Set it first (see README), then rerun.")
    items, out = load(a.input), pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    safe = lambda s: re.sub(r"[^A-Za-z0-9_.-]+", "_", s)[:80] or "narrative"
    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        reps = list(ex.map(lambda it: build_report(it[1]), items))
    rows = []
    for (rid, _), rep in zip(items, reps):
        f = safe(rid)
        (out / f"{f}.html").write_text(page(rid, rep), encoding="utf-8")
        (out / f"{f}.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
        overall = "human_review" if rep.get("human_review") else "gaps" if any(c["missing"] for c in rep["charges"]) else "complete"
        rows.append({"id": rid, "file": f"{f}.html", "result": STATUS[overall][0], "charges": "; ".join(c["citation"] or "(none)" for c in rep["charges"]),
                     "citation_check": "; ".join(CHECK.get(c["citation_check"]["result"], "") for c in rep["charges"]), "flags": len(rep["flags"]),
                     "missing": "; ".join(f"{c['citation']}: {', '.join(c['missing'])}" for c in rep["charges"] if c["missing"]), "seconds": rep["seconds"]})
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["id"]); w.writeheader(); w.writerows(rows)
    e = html.escape
    trs = "".join(f"<tr><td><a href='{e(r['file'])}'>{e(r['id'])}</a></td><td>{e(r['result'])}</td><td>{e(r['charges'])}</td><td>{e(r['citation_check'])}</td><td>{r['flags']}</td><td>{r['seconds']}s</td></tr>" for r in rows)
    (out / "index.html").write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>Gap reports</title><style>{CSS} body{{max-width:10in}}</style></head><body><h1>Gap reports ({len(rows)} narratives)</h1>"
        f"<div class='meta'>{time.strftime('%Y-%m-%d %H:%M')} · {time.time() - t0:.0f}s total</div><table><tr><th>Narrative</th><th>Result</th><th>Charges cited</th><th>Citation check</th><th>Flags</th><th>Time</th></tr>{trs}</table></body></html>", encoding="utf-8")
    print(f"{len(rows)} reports written to {out}/ in {time.time() - t0:.0f}s. Open {out}/index.html")
    for r in rows:
        print(f"  {r['id']:<12} {r['result']:<14} {r['citation_check']}")
