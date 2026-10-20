# Sample narrative markup worksheet

Mark up the sample narrative Unissant sent, sentence by sentence, against
`charge_elements.json`. Fill in the "Fact satisfied?" column yourself —
don't let a model do this pass. The point is to find out by hand whether
the required_facts lists are even right before any code depends on them.

## Narrative (as sent by Vasu)

| ID | Sentence |
|----|----------|
| S1 | INADMISSIBILITY: 'John Doe' a citizen of Mexico. |
| S2 | He has never had any documents that would allow him to be, or remain, in the United States legally. |
| S3 | 'John Doe' is inadmissible under section 212(a)(6)(A)(i) of the INA, in that he entered the United States at a place not designated by the Attorney General and was not then admitted or paroled after inspection by an immigration officer. |
| S4 | INADMISSIBILITY: Subject is inadmissible under Section 212(A)(9)(A)(I) of the Immigration and Nationality Act, as amended, in that he was previously ordered removed and entered or attempted to enter without being admitted. |
| S5 | REMOVABILITY: Subject is removable under Section 212 because he was found inadmissible as an arriving alien in proceedings under section 235(b)(1) of the Act. |

## Markup — Charge 212(a)(6)(A)(i)

| Required fact | Satisfied by | Notes |
|---|---|---|
| subject_identity | S1 ("'John Doe'") | Placeholder name, not a real identifier — fine for synthetic data |
| country_of_citizenship | S1 ("a citizen of Mexico") | Satisfied |
| manner_of_entry | S3 ("entered ... at a place not designated by the Attorney General") | Satisfied |
| place_of_entry | — | NOT satisfied. S3 says entry was at an undesignated place but never names which place/location — this is the gap Vasu's own email used as the example |
| admitted_or_paroled_status | S3 ("was not then admitted or paroled after inspection") | Satisfied |

**Gap found:** place_of_entry is missing. Matches Unissant's own example
of what a flag should look like (they used "Country of Citizenship" as
their example fact — worth double-checking whether they consider
"place of entry" at this level of specificity a required fact, or whether
it's optional detail. This is exactly the kind of ambiguity to ask about
once we have more sample narratives.)

## Markup — Charge 212(a)(9)(A)(i)

| Required fact | Satisfied by | Notes |
|---|---|---|
| subject_identity | S1 (carried over — same subject) | Satisfied, but only because S1 established it earlier. Confirms the extractor needs to track subject identity across the whole narrative, not sentence-by-sentence in isolation |
| prior_removal_order | S4 ("previously ordered removed") | Satisfied |
| prior_removal_date | — | NOT satisfied — no date given anywhere |
| reentry_or_attempted_reentry | S4 ("entered or attempted to enter") | Satisfied |
| admitted_status_at_reentry | S4 ("without being admitted") | Satisfied |

**Gap found:** prior_removal_date is missing.

## Takeaways from doing this by hand

1. Subject identity and citizenship established once in S1 apply to the
   whole narrative — extraction can't be purely per-sentence, it needs to
   carry facts forward across sentences for the same subject.
2. Two real gaps surfaced just from this one narrative: missing
   place_of_entry and missing prior_removal_date. If the actual model
   doesn't catch both of these on this exact sample, the required_facts
   lists or the extraction logic are wrong — this sample is now a basic
   regression test.
3. REMOVABILITY (S5) cites Section 212 generally for a different purpose
   (removability under 235(b)(1), not inadmissibility) — need a separate
   required_facts entry for removability grounds, not just inadmissibility
   ones. Added as an open item below.

## Open items

- [ ] Add a removability-grounds section to charge_elements.json (235(b)(1) referenced in S5)
- [ ] Confirm with Unissant whether "place of entry" is a required fact or optional detail
- [ ] Get more sample narratives — one data point isn't enough to trust the required_facts lists
