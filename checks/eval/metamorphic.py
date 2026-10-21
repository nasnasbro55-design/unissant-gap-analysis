import random, re, sys

NAME = ["ANA LUCIA MORALES", "BRIAN K. OKAFOR", "LIAM TRAN", "SOFIA R. KOVAC", "OMAR HADDAD", "PRIYA N. SHARMA", "TOMAS BELL", "YUSUF AKIN", "HELENA DIAZ-ORTIZ", "KWAME ASANTE"]
CTRY = ["Guatemala", "Honduras", "El Salvador", "Mexico", "Ecuador", "Colombia", "Peru", "Haiti", "Venezuela"]
PLACE = ["near Hidalgo, Texas", "near Eagle Pass, Texas", "near Nogales, Arizona", "near Calexico, California", "near Lukeville, Arizona", "near Laredo, Texas"]
DOC, BEN = ["passport", "visa", "birth certificate"], ["a visitor", "a student", "a temporary worker"]
MUTS = ["none", "upper", "lower", "abbrev", "typo", "shuffle"]
CITE = ["Subject is inadmissible under INA {k}.", "Charge: section {k} of the Act."]
IDENT = ("subject_identity", ["SUBJECT {n} is the subject of this report.", "This report concerns {n}."])
# every sentence is self-contained, so sentences can be dropped or shuffled without changing what the others say
T = {
    "212(a)(6)(A)(i)": [IDENT,
        ("country_of_citizenship", ["Subject is a citizen of {c}.", "Subject is a native and national of {c}."]),
        ("manner_of_entry", ["Subject entered the United States by wading across the river.", "Subject crossed the border on foot, carrying a small bag."]),
        ("place_of_entry", ["Subject entered the United States {p}.", "Subject's point of entry was {p}."]),
        ("admitted_or_paroled_status", ["Subject was not admitted or paroled.", "Subject has never been inspected, admitted, or paroled."])],
    "212(a)(9)(A)(i)": [IDENT,
        ("prior_removal_order", ["Subject was ordered removed by an immigration judge.", "A prior order of removal was issued against subject by an immigration judge."]),
        ("prior_removal_date", ["The removal order is dated {d}.", "Subject was removed from the United States on {d}."]),
        ("reentry_or_attempted_reentry", ["Subject re-entered the United States {p}.", "Subject returned to the United States {p}."]),
        ("admitted_status_at_reentry", ["Subject was not admitted at the time of reentry.", "Subject was not inspected or admitted upon return."])],
    "212(a)(6)(C)(i)": [IDENT,
        ("misrepresentation_or_fraud_act", ["Subject made a false statement to an immigration officer during the interview.", "Subject submitted an application that contained a false statement."]),
        ("material_fact_misrepresented", ["The false statement concerned subject's prior immigration history.", "The false statement concerned subject's employment status."]),
        ("benefit_or_admission_sought", ["Subject was applying for admission as {b}.", "Subject was seeking admission to the United States as {b}."])],
}
DEP = {"prior_removal_date": "prior_removal_order", "admitted_status_at_reentry": "reentry_or_attempted_reentry", "material_fact_misrepresented": "misrepresentation_or_fraud_act"}

def generate(count, seed=1):
    r, out = random.Random(seed), []
    for i in range(count):
        k, mut = list(T)[i % len(T)], r.choice(MUTS)
        v = dict(k=k, n=r.choice(NAME), c=r.choice(CTRY), p=r.choice(PLACE), doc=r.choice(DOC), b=r.choice(BEN), d=f"{r.randint(1, 12):02d}/{r.randint(1, 28):02d}/{r.randint(2015, 2022)}")
        gone = set(r.sample([f for f, _ in T[k] if f != "subject_identity"], r.choice([0, 1, 1, 2])))  # identity is never deleted: a placeholder like "Subject" counts as identified
        gone |= {c for c, p in DEP.items() if p in gone and any(c == f for f, _ in T[k])}
        s = [r.choice(t).format(**v) for f, t in T[k] if f not in gone]
        if mut == "shuffle": r.shuffle(s)
        text = " ".join(s + [r.choice(CITE).format(**v)])
        if mut == "upper": text = text.upper()
        if mut == "lower": text = text.lower()
        if mut == "abbrev": text = text.replace("Subject", "Subj.").replace("immigration judge", "IJ")
        if mut == "typo":
            w = r.choice(re.findall(r"[A-Za-z]{7,}", text))
            text = text.replace(w, w[:2] + w[3] + w[2] + w[4:], 1)
        out.append({"id": f"m{seed}-{i:03d}", "author": "metamorphic", "tags": ["meta", mut, f"deleted{len(gone)}", k], "narrative": text, "expected": {k: {"status": "gaps" if gone else "complete", "missing": sorted(gone)}}})
    return out

if __name__ == "__main__":
    for c in generate(int(sys.argv[1]) if len(sys.argv) > 1 else 6, int(sys.argv[2]) if len(sys.argv) > 2 else 1):
        print(c["id"], c["tags"][1:], "missing:", c["expected"][list(c["expected"])[0]]["missing"], "\n   ", c["narrative"], "\n")
