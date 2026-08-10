# Analysis master contract

The agent reads `analysis_context.json` once and writes exactly one `analysis_master.json`.
This reduces repeated transcription; it does not reduce calculation or reasoning requirements.

```json
{
  "schema_version": "analysis_master_v1",
  "language": "zh-TW|en",
  "dossiers": {
    "bazi": {"status": "locked", "outcomes": []},
    "ziwei": {"status": "locked", "outcomes": []},
    "western": {"status": "locked", "outcomes": []},
    "vedic": {"status": "locked", "outcomes": []}
  },
  "adjudication": {"fate_adjudication": []},
  "score_input": {"domains": []},
  "fate_packet": {
    "core_thesis": "",
    "consequential_judgments": [],
    "school_role_manifest": [],
    "consensus_matrix": [],
    "annual_rulings": []
  },
  "report_markdown": "# ..."
}
```

For each native outcome retain source facts, reasoning, the selected life version,
at least one plausible rejected version, deciding conditions, a revision condition,
time layer and confidence. Keep all four schools independent inside `dossiers`.

For each adjudicated domain include every school's explicit position. The materializer
copies adjudication into the packet, runs the fixed scoring formula and writes all
production files. Never duplicate these files manually.

Write the Reader directly in the requested language from the locked dossiers and
adjudication. Never translate a completed Reader. Keep claim meaning, scores, years,
confidence and revision conditions identical across language editions.
