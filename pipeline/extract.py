import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FACTS = json.loads((ROOT / "checks/elements/fact_definitions.json").read_text())
SYSTEM = (ROOT / "pipeline/prompts/extract_v1.txt").read_text().replace("{fact_definitions}", "\n".join(f"- {k}: {v}" for k, v in FACTS.items()))
norm = lambda s: " ".join(s.split()).lower()

def split_sentences(text):
    return {f"S{i}": " ".join(s.split()) for i, s in enumerate(re.split(r"(?<=\.)\s+(?=[A-Z'\"‘“])", text.strip()), 1)}

def grounded(c, sents):
    return c.get("fact_type") in FACTS and c.get("confidence") in ("high", "medium", "low") and bool(c.get("sentence_ids")) and all(s in sents for s in c["sentence_ids"]) and bool(norm(c.get("quote", ""))) and any(norm(c["quote"]) in norm(sents[s]) for s in c["sentence_ids"])

def extract(text, chat=None):
    if chat is None:
        from llm_client import chat
    sents = split_sentences(text)
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "<narrative>\n" + "\n".join(f"{k}: {v}" for k, v in sents.items()) + "\n</narrative>"}]
    try:
        raw = chat(msgs, temperature=0, response_format={"type": "json_object"})
    except Exception:
        raw = chat(msgs, temperature=0)
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        raise ValueError("model returned no JSON: " + (raw or "")[:200])
    claims = json.loads(m.group(0)).get("claims", [])
    return sents, [c for c in claims if grounded(c, sents)], [c for c in claims if not grounded(c, sents)]
