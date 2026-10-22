"""Review result contract, version 1. backend/sample_report.json is a real example (from a stubbed model run).

{
  "version": "1",
  "model": "gpt-oss-20b", "prompt_version": "v4", "votes": 1, "seconds": 5.2,
  "disclaimer": "...",                      # show this on every result screen
  "sentences": {"S1": "...", "S2": "..."},  # the narrative split into numbered sentences, for highlighting
  "charges": [                              # one entry per charge cited in the narrative, in order found
    {
      "citation": "212(a)(6)(A)(i)",        # null when no charge was cited or the model was unavailable
      "name": "...", "source": "INA ...",   # null for charges not in our reference table
      "status": "complete" | "gaps" | "human_review",
      "reason": null | "...",               # always set when status is human_review
      "facts": [                            # every required fact for this charge, found or not
        {"fact_type": "place_of_entry", "label": "place of entry", "found": false,
         "quote": null, "sentence_ids": [], "confidence": null}
      ],
      "missing": ["place_of_entry"],        # required facts not found
      "conflicts": [{"fact_type": "...", "quote": "...", "sentence_ids": ["S2"], "confidence": "high"}],
      "disagreed": []                       # facts repeated runs disagreed on (only with votes > 1)
    }
  ]
}

Rules for anything that displays this:
- Never show a suggested or alternative charge. The tool does not produce one.
- Show the quote and highlight sentence_ids for every found fact, so a reviewer can check it in seconds.
- Treat human_review as "a person must look", and show the reason.
"""
