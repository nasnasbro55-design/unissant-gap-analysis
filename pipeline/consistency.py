"""Internal consistency checks, in plain code (no model): impossible dates, future dates,
and a prior removal dated after the reentry. Each returns a flag with a reason and the sentence behind it."""
import re, datetime as dt

MON = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
NUM = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})\b")
CTZ = re.compile(r"\b(?:citizen|national)s?(?:\s+and\s+(?:citizen|national))?\s+of\s+(?:the\s+)?([A-Za-z]+)", re.I)
TXT = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b", re.I)

def dates(text):
    """Every date written as MM/DD/YYYY, M/D/YY or 'Month D, YYYY': (as written, date or None if impossible)."""
    found = [(m[0], int(m[1]), int(m[2]), int(m[3]) + (2000 if len(m[3]) == 2 else 0)) for m in NUM.finditer(text)]
    found += [(m[0], MON[m[1][:3].lower()], int(m[2]), int(m[3])) for m in TXT.finditer(text)]
    out = []
    for raw, mo, d, y in found:
        try:
            out.append((raw, dt.date(y, mo, d)))
        except ValueError:
            out.append((raw, None))
    return out

def check(sents, claims, today=None):
    today, flags = today or dt.date.today(), []
    add = lambda why, ids: flags.append({"type": "inconsistency", "charge": None, "fact_type": None, "reason": why, "sentence_ids": ids})
    for sid, s in sents.items():
        for raw, d in dates(s):
            if d is None:
                add(f"“{raw}” is not a valid date. The officer should correct it.", [sid])
            elif d > today:
                add(f"“{raw}” is in the future. The officer should check it.", [sid])
    removed = [(raw, d) for c in claims if c["fact_type"] == "prior_removal_date" for raw, d in dates(str(c.get("quote"))) if d]
    for sid in sorted({i for c in claims if c["fact_type"] == "reentry_or_attempted_reentry" for i in c.get("sentence_ids", [])}):
        if any(raw in sents[sid] for raw, _ in removed):
            continue  # the removal date sits in the reentry sentence itself; too ambiguous to compare
        for raw, d in dates(sents[sid]):
            for rraw, rd in removed:
                if d and d < rd:
                    add(f"The prior removal date (“{rraw}”) is after the reentry date (“{raw}”). A reentry has to follow the removal, so one of these dates is likely wrong.", [sid])
    seen = {}
    for sid, s in sents.items():
        for m in CTZ.finditer(s):
            seen.setdefault(m[1].lower(), (m[0], sid))
    if len(seen) > 1:
        add("The narrative gives more than one country of citizenship (" + ", ".join(f"\u201c{q}\u201d" for q, _ in seen.values()) + "). The officer should confirm which is correct.",
            sorted({sid for _, sid in seen.values()}))
    return flags
