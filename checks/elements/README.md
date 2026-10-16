# Charge elements reference

`charge_elements.json` maps each charge code to the facts a narrative must
state to support it. Jake's gap-check logic reads this file; it should not
hardcode charge logic elsewhere.

Each entry:
- `required_facts` — the fact types the engine checks for in the extracted
  claims. Missing any one of these = a gap flag citing that fact type.
- `source` — the statute and where in the USCIS Policy Manual it's
  described, so every rule here is traceable, not invented.

## Status

Only 3 charges encoded so far (the 2 in Unissant's sample narrative, plus
one common fraud/misrepresentation ground). Need to expand coverage —
read more of USCIS Policy Manual Vol. 7, Part L, Ch. 3
(https://www.uscis.gov/policy-manual/volume-7-part-l-chapter-3) and add
entries for other common inadmissibility grounds.

## Next step

Hand-mark the sample narrative Unissant sent against this table:
for each sentence, note which required_fact (if any) it satisfies.
Use that to sanity-check the required_facts lists above before any code
reads them.
