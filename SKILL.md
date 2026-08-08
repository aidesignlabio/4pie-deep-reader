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

1. Read [architecture.md](references/architecture.md) and [privacy-policy.md](references/privacy-policy.md).
2. Calculate L0 with `scripts/4pie.py calculate`. Keep only Bazi, Zi Wei, Western and Vedic systems. Stored artifacts strip identifying input metadata by default; use `--include-pii` only when the user explicitly requires it and the case remains private.
3. Reject invalid core data. Never fill missing pillars, palaces, houses, D1/Dasha or timing data with prose.
4. Read [bazi-l1-policy.md](references/bazi-l1-policy.md), then run `scripts/4pie.py bazi-l1 CHART_JSON OUTPUT_JSON --as-of YYYY-MM-DD --strict`.
5. Run prompt A from [prompts.md](references/prompts.md) independently for each school. Lock four native dossiers before fusion.
6. Challenge each dossier with prompt B. Reject generic traits, missing alternatives and conclusions inferred from one placement.
7. Use prompt C to compare competing life versions. Preserve every school's position: `support`, `refine`, `limit`, `oppose`, `not_comparable`, `not_applicable` or `insufficient`.
8. Read [scoring-contract.md](references/scoring-contract.md). Run `scripts/4pie.py score INPUT_JSON OUTPUT_JSON`; never invent scores in the Reader.
9. Write with prompt D. Lead with concrete Traditional Chinese judgments. Keep technical evidence after the judgment. Do not add conversation biography unless the user explicitly confirms it belongs to the subject.
10. Validate with `scripts/validate_fate_packet.py`, then run `scripts/4pie.py production-check CASE_DIR --start-year 2026`. Production Approval requires all four L0 systems `ok`, Bazi L1 `ok` with verified strength, four locked non-empty dossiers, complete cross-school positions without `insufficient`, exactly eight fully calculated score rows, five consecutive annual rulings, and a complete Reader. Never generate a Production PDF after a downgrade.
11. Render only through `scripts/4pie.py render CASE_DIR report.pdf --subject "..." --start-year 2026`. This hard-gated command calls the dedicated `render_plain_deep_pdf.py` and reproduces the approved `4PIE_20020312_Plain_Deep_Report_v1` template program: the original mountain-route cover, card contents with page numbers, two-column eight-domain/four-metric bar dashboard, 2026-2030 vertical timeline, pale-blue chapter bands, original typography/leading/whitespace/body density, and original header/footer/page numbers. The first four pages are fixed modules; body pages expand naturally. Birth data, scores, years and rulings must come from the current case artifacts; no reference-case value may be embedded. Never approximate this design with `render_apple_pdf.py`. Use `scripts/4pie.py render-dashboard` only when explicitly requested. Run `scripts/4pie.py pdf-qa report.pdf` and inspect its contact sheet before delivery.

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
