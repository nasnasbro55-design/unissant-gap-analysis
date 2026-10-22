import json, os, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERSION = os.environ.get("PROMPT_VERSION", "v4")
FACTS = json.loads((ROOT / "checks/elements/fact_definitions.json").read_text())
SYSTEM = (ROOT / f"pipeline/prompts/extract_{VERSION}.txt").read_text().replace("{fact_definitions}", "\n".join(f"- {k}: {v}" for k, v in FACTS.items()))
ABBR = re.compile(r"(?:^|\s)(?:[A-Z]|Mr|Mrs|Ms|Dr|Sr|Jr|St|Subj)\.$")
norm = lambda s: " ".join(str(s or "").split()).lower()

def split_sentences(text):
    out = []
    for p in re.split(r"(?<=\.)\s+(?=[A-Z'\"‘“])", text.strip()):
        out.append(out.pop() + " " + p if out and ABBR.search(out[-1]) else p)
    return {f"S{i}": " ".join(s.split()) for i, s in enumerate(out, 1)}

def locate(quote, sents):
    q, full, spans = norm(quote), "", {}
    for k, v in sents.items():
        spans[k] = (len(full), len(full) + len(norm(v)))
        full += norm(v) + " "
    i = full.find(q) if q else -1
    return [] if i < 0 else [k for k, (a, b) in spans.items() if a < i + len(q) and i < b]

def extract(text, chat=None):
    if chat is None:
        from llm_client import chat
    sents = split_sentences(text)
    body = text.strip() if VERSION not in ("v1", "v2") else "\n".join(f"{k}: {v}" for k, v in sents.items())
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "<narrative>\n" + body + "\n</narrative>"}]
    eff = os.environ.get("REASONING_EFFORT", "low")
    kw = {"temperature": 0, **({"reasoning_effort": eff} if eff not in ("", "default") else {})}
    try:
        raw = chat(msgs, response_format={"type": "json_object"}, **kw)
    except Exception:
        raw = chat(msgs, **kw)
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        raise ValueError("model returned no JSON: " + (raw or "")[:200])
    claims = [dict(c, sentence_ids=locate(c.get("quote"), sents)) for c in json.loads(m.group(0)).get("claims", []) if isinstance(c, dict)]
    good = lambda c: c.get("fact_type") in FACTS and c.get("confidence") in ("high", "medium", "low") and bool(c["sentence_ids"])
    return sents, [c for c in claims if good(c)], [c for c in claims if not good(c)]
