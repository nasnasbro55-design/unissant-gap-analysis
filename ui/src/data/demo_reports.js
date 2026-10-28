import sampleReport from './sample_report.json';

export const DEMO_PRESETS = [
  {
    id: 'sample_unissant',
    title: "Unissant Sample Case (John Doe - Gaps)",
    description: "Real sample narrative from Unissant. Two charges with missing place_of_entry and prior_removal_date.",
    data: sampleReport
  },
  {
    id: 'clean_case',
    title: "Complete Documentation Case (All Facts Found)",
    description: "Fully documented INA 212(a)(6)(A)(i) encounter with all required statutory elements present.",
    data: {
      version: "1",
      model: "gpt-oss-20b",
      prompt_version: "v4",
      votes: 1,
      seconds: 4.8,
      disclaimer: "Flags missing documentation only. It does not judge the case or suggest charges. A person reviews every result.",
      sentences: {
        "S1": "Subject JAVIER ENRIQUE MONTIEL-CASTRO is a native and citizen of Nicaragua.",
        "S2": "On 04/12/2025 at approximately 2130 hrs, Border Patrol agents encountered the subject approximately two miles east of Del Rio, Texas.",
        "S3": "Subject stated under oath that he entered the United States by swimming across the Rio Grande river and that he was not inspected, admitted, or paroled by an immigration officer.",
        "S4": "Subject is inadmissible under INA 212(a)(6)(A)(i)."
      },
      charges: [
        {
          citation: "212(a)(6)(A)(i)",
          name: "Present without admission or parole",
          source: "INA 212(a)(6)(A)(i); USCIS Policy Manual Vol. 7, Part L, Ch. 3",
          status: "complete",
          reason: null,
          facts: [
            {
              fact_type: "subject_identity",
              label: "subject identity",
              found: true,
              quote: "JAVIER ENRIQUE MONTIEL-CASTRO",
              sentence_ids: ["S1"],
              confidence: "high"
            },
            {
              fact_type: "country_of_citizenship",
              label: "country of citizenship",
              found: true,
              quote: "citizen of Nicaragua",
              sentence_ids: ["S1"],
              confidence: "high"
            },
            {
              fact_type: "manner_of_entry",
              label: "manner of entry",
              found: true,
              quote: "swimming across the Rio Grande river",
              sentence_ids: ["S3"],
              confidence: "high"
            },
            {
              fact_type: "place_of_entry",
              label: "place of entry",
              found: true,
              quote: "approximately two miles east of Del Rio, Texas",
              sentence_ids: ["S2"],
              confidence: "high"
            },
            {
              fact_type: "admitted_or_paroled_status",
              label: "admitted or paroled status",
              found: true,
              quote: "not inspected, admitted, or paroled by an immigration officer",
              sentence_ids: ["S3"],
              confidence: "high"
            }
          ],
          missing: [],
          conflicts: [],
          disagreed: []
        }
      ]
    }
  },
  {
    id: 'contradiction_case',
    title: "Contradiction Case (Routes to Human Review)",
    description: "Narrative documents lawful admission on a B-2 visa, contradicting cited 212(a)(6)(A)(i).",
    data: {
      version: "1",
      model: "gpt-oss-20b",
      prompt_version: "v4",
      votes: 1,
      seconds: 5.1,
      disclaimer: "Flags missing documentation only. It does not judge the case or suggest charges. A person reviews every result.",
      sentences: {
        "S1": "SUBJECT GUILLERMO HERNANDEZ-RUIZ is a citizen of Mexico.",
        "S2": "On 01/20/2025, the subject arrived at the Otay Mesa Port of Entry and was formally inspected and admitted by a CBP officer as a B-2 temporary visitor with an authorized stay through 07/19/2025.",
        "S3": "Subject remained in the US past that date without extension.",
        "S4": "Subject is charged as inadmissible under INA 212(a)(6)(A)(i) as an alien present without admission or parole."
      },
      charges: [
        {
          citation: "212(a)(6)(A)(i)",
          name: "Present without admission or parole",
          source: "INA 212(a)(6)(A)(i); USCIS Policy Manual Vol. 7, Part L, Ch. 3",
          status: "human_review",
          reason: "the narrative states facts that conflict with this charge",
          facts: [
            {
              fact_type: "subject_identity",
              label: "subject identity",
              found: true,
              quote: "GUILLERMO HERNANDEZ-RUIZ",
              sentence_ids: ["S1"],
              confidence: "high"
            },
            {
              fact_type: "country_of_citizenship",
              label: "country of citizenship",
              found: true,
              quote: "citizen of Mexico",
              sentence_ids: ["S1"],
              confidence: "high"
            },
            {
              fact_type: "admitted_or_paroled_status",
              label: "admitted or paroled status",
              found: true,
              quote: "formally inspected and admitted by a CBP officer as a B-2 temporary visitor",
              sentence_ids: ["S2"],
              confidence: "high"
            }
          ],
          missing: ["manner_of_entry", "place_of_entry"],
          conflicts: [
            {
              fact_type: "stated_lawful_admission",
              quote: "formally inspected and admitted by a CBP officer as a B-2 temporary visitor",
              sentence_ids: ["S2"],
              confidence: "high"
            }
          ],
          disagreed: []
        }
      ]
    }
  },
  {
    id: 'unknown_charge_case',
    title: "Uncovered Charge Case (Routes to Human Review)",
    description: "Narrative cites INA 212(a)(2)(A)(i), which is outside the active rules table.",
    data: {
      version: "1",
      model: "gpt-oss-20b",
      prompt_version: "v4",
      votes: 1,
      seconds: 3.2,
      disclaimer: "Flags missing documentation only. It does not judge the case or suggest charges. A person reviews every result.",
      sentences: {
        "S1": "Subject MARCOS ANDRADE-SILVA, a citizen of Brazil, was convicted on 10/12/2024 in Harris County Criminal Court of felony theft.",
        "S2": "Subject is inadmissible under INA 212(a)(2)(A)(i) as an alien convicted of a crime involving moral turpitude."
      },
      charges: [
        {
          citation: "212(a)(2)(A)(i)",
          name: null,
          source: null,
          status: "human_review",
          reason: "charge not in reference table; officer must verify statutory elements manually",
          facts: [],
          missing: [],
          conflicts: [],
          disagreed: []
        }
      ]
    }
  }
];
