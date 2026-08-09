---
name: 4pie-deep-reader
description: "Calculate, validate and independently interpret Bazi, Zi Wei Dou Shu, Western astrology and Vedic astrology; adjudicate competing life hypotheses, compute transparent Flow/Potential/Friction/Confidence scores, and generate Traditional Chinese Markdown or an editorial Plain Deep Report PDF, with an expanded Dashboard edition available on request. Use for 四派命理深讀、人生版本裁決、流年分析、可追蹤評分、命理報告或4PIE PDF。Privacy-first: never reuse conversation biography or ship identifiable case data."
---

# 4PIE Deep Reader

Treat calculation, interpretation, adjudication, scoring and presentation as separate layers.

## Runtime setup

First run `.venv\Scripts\python.exe scripts\4pie.py doctor` when `.venv` exists. If it reports `core_ready: true`, skip setup.

Otherwise run `setup.ps1` on Windows or `setup.sh` on macOS/Linux exactly once. First installation commonly takes 2–10 minutes. When invoking it through an execution tool, set that tool's hard timeout to at least 15 minutes (`900000 ms`); the script cannot extend a timeout imposed by the host tool. A successful setup ends with `4PIE_READY`.

Never run setup a second time merely because the outer execution tool timed out. Check `.setup.lock`: while its recorded process is alive, wait for that process and then run `scripts/4pie.py doctor`. If a retry prints `SETUP_WAITING`, stop the retry and wait for the active installer. Zi Wei subprocess output is decoded explicitly as UTF-8, so users must not need to set `PYTHONUTF8` manually.

After setup, invoke every deterministic operation through `scripts/4pie.py`; do not call internal scripts such as `adjudicate_bazi_l1.py`, `score_domains.py` or renderers directly. The unified launcher supplies the required UTF-8 child environment and validation gates.

## Required workflow

1. Read [architecture.md](references/architecture.md), [privacy-policy.md](references/privacy-policy.md), [bazi-l1-policy.md](references/bazi-l1-policy.md), [prompts.md](references/prompts.md), and [scoring-contract.md](references/scoring-contract.md) once, preferably in one read operation.
2. Run the single preparation entry point once with a host timeout of at least 15 minutes. Select `-Mode standard` for a 3,500-5,500 character Reader or `-Mode deep` for a 7,000-10,000 character Reader. Both modes use identical calculation, native-analysis and Production Approval gates:

   `./run-report.ps1 -Birth "YYYY-MM-DD HH:MM" -Timezone "Area/City" -Latitude 0 -Longitude 0 -Gender F -CaseDir "private_cases/CASE" -AsOf "YYYY-MM-DD" -StartYear 2026`

   It runs doctor, performs setup only when required, calculates one four-school natal chart, completes Bazi L1, writes resumable state, and creates `analysis_context.json`. Never call `calculate` separately after this command.
3. Reject invalid core data. Never fill missing pillars, palaces, houses, D1/Dasha or timing data with prose.
4. Read `analysis_context.json` once. Do not reopen `analysis_bundle.json` or `structured_data.md`. Use its existing Bazi annual activation, Dasha and transit data for all requested annual rulings. Do not calculate five full charts for five years or create arbitrary yearly snapshots.
5. Read [analysis-master-contract.md](references/analysis-master-contract.md). Perform native analysis, challenge, cross-school adjudication and Reader composition as one bounded analysis pass. Write exactly one `analysis_master.json`; do not hand-write duplicate dossier, packet, score or Reader files. Run `scripts/4pie.py materialize analysis_master.json CASE_DIR`, which deterministically creates all production artifacts and scores. Allow at most one revision pass after validation.
6. Run D9/D10/UL minute sensitivity only when a final claim actually depends on one of those features. Otherwise record it as unused; do not perform a precautionary sensitivity run.
7. Preserve every school's position: `support`, `refine`, `limit`, `oppose`, `not_comparable`, `not_applicable` or `insufficient`. Run `scripts/4pie.py score INPUT_JSON OUTPUT_JSON`; never invent scores in the Reader.
8. Validate with `scripts/4pie.py validate fate_packet.json`, then run `scripts/4pie.py production-check CASE_DIR --start-year 2026`. Production Approval requires all four L0 systems `ok`, Bazi L1 `ok` with verified strength, four locked non-empty dossiers, complete cross-school positions without `insufficient`, exactly eight fully calculated score rows, five consecutive annual rulings, and a complete Reader. Never generate a Production PDF after a downgrade.
9. Render only through `scripts/4pie.py render CASE_DIR report.pdf --subject "..." --start-year 2026`. The fixed Plain Deep template includes the mountain-route cover, AiDesignLab.io logo/credit, stronger Traditional Chinese typography, card contents, eight-domain dashboard, vertical timeline, pale-blue bands, headers, footers and dynamic body pagination. Never approximate it with `render_apple_pdf.py`. Run `pdf-qa`, inspect the contact sheet, then run `package-delivery CASE_DIR DELIVERY_DIR`. Run privacy scanning only on `DELIVERY_DIR`; never scan `private_cases/CASE`, because calculation artifacts intentionally contain birth data.

## Non-negotiable reasoning rules

- Keep four schools independent until native analysis is locked.
- Compare answers to the same real-world question at the same time layer. Similar words are not consensus.
- Propose at least two plausible life versions before choosing one.
- Preserve a rejected alternative and a concrete condition that would overturn the ruling.
- Separate natal permission, long-period background, annual trigger and real-world carrier.
- A time window is evidence, not a promised event.
- Keep relationship partner quality as a single-school signal unless independently established.
- Keep D9/D10/UL features downgraded when minute sensitivity changes them.
- Never diagnose illness, predict death, guarantee wealth or claim empirical accuracy without validation data.
- Never convert `insufficient`, missing scores, missing years or a failed dossier into a polished Reader. Stop before rendering and report the failed production gates.

## Reader output

Produce in the Reader body:

- five consequential judgments;
- life-stage trajectory;
- career, wealth, relationship, home/family, network/reputation, learning and stress sections;
- competing versions and the reason one ranks higher;
- 2026-2030 annual rulings when requested and supported;
- domain scores with plain-language definitions;
- technical limits and falsifiers.

The Reader is the product. Technical dossiers, matrices and audit fields support it but may not replace detailed plain-language analysis.

Do not use repeated coaching language, fixed “not X but Y” constructions, or generic advice as analysis.

## Output contract

Write artifacts under a case-specific output directory:

```text
chart_data.json
validation.json
bazi_l1.json
dossiers/{bazi,ziwei,western,vedic}.json
adjudication.json
score_input.json
domain_scores.json
report.md
report.pdf
pdf_qa.json
```

Default render command:

```text
python scripts/4pie.py production-check private_cases/CASE --start-year 2026
python scripts/4pie.py render private_cases/CASE private_cases/CASE/report.pdf --start-year 2026 --title "命運裁決報告" --subject "去識別化個案資料"
python scripts/4pie.py pdf-qa private_cases/CASE/report.pdf --output-dir private_cases/CASE/pdf-qa
```

Before publishing or sharing any artifact, run `scripts/privacy_scan.py` on the target directory.
