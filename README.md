# 4PIE Deep Reader

A traceable four-system destiny interpretation framework for Bazi, Zi Wei Dou Shu, Western astrology and Vedic astrology. Technical intermediates may report insufficiency, but production output never degrades: any incomplete core module stops the run before a PDF is created.

4PIE compares competing life hypotheses instead of blending placement keywords into a generic story. Each school is interpreted independently, challenged, then adjudicated with visible support, limits, conflicts and falsifiers.

## What it produces

- validated four-system `chart_data.json`;
- independent native dossiers;
- competing life versions and adjudication;
- Flow, Potential, Friction and Confidence scores;
- Traditional Chinese natal and annual report;
- compact editorial Plain Deep Report PDF by default;
- expanded Dashboard PDF on explicit request.

Scores are reading indices, not empirical probabilities or guarantees.

## Quick start

Install and verify the complete isolated runtime:

```powershell
.\setup.ps1
```

If Windows resolves `python` to a broken launcher, pass a real interpreter explicitly:

```powershell
.\setup.ps1 -Python "C:\path\to\python.exe"
```

Setup is one-time. For later cases, run `.venv\Scripts\python scripts\4pie.py doctor`; do not reinstall dependencies. PDF output defaults to the compact `plain-deep` edition. The expanded `dashboard` edition is opt-in.

```bash
./setup.sh
```

The installer creates the ignored `.venv`, installs Python dependencies in the required order, downloads the release-pinned Noto Sans TC font into an ignored local asset directory, runs `npm install` for pinned `iztro@2.5.8`, and executes a synthetic four-system chart. This keeps the PDF typography consistent on Windows, macOS and Linux without requiring a system CJK font. A successful install ends with `FONT_READY`, `FOUR_SYSTEM_SMOKE_OK` and `4PIE_READY`.

```powershell
python scripts/4pie.py calculate --datetime "2000-01-01 12:00" --timezone UTC --lat 0 --lon 0 --gender F --as-of 2026-01-01 --output private_cases/demo/chart_data.json
python scripts/4pie.py bazi-l1 private_cases/demo/chart_data.json private_cases/demo/bazi_l1.json
python scripts/4pie.py score examples/synthetic_score_input.json private_cases/demo/domain_scores.json
python scripts/4pie.py production-check private_cases/demo --start-year 2026
python scripts/4pie.py render private_cases/demo private_cases/demo/report.pdf --start-year 2026 --subject "Birth summary"
```

The public `render` command always reruns the Production Gate. All four L0 systems, verified Bazi L1, four approved dossiers, adjudication, exactly eight complete score rows and five consecutive annual rulings must pass. Failure returns a non-zero exit status and leaves no partial PDF.

The production renderer uses the fixed `4PIE_20020312_Plain_Deep_Report_v1` visual system: mountain-route cover, card contents, eight-domain dashboard, five-year vertical timeline, pale-blue chapter bands and consistent typography, spacing, headers, footers and page numbering. All subject data is dynamic.

Python 3.8-3.13 and Node.js/npm are required. Use the setup scripts instead of installing `requirements.txt` directly because DashaFlow and PyJHora require a controlled installation order.

Use the Skill instructions in [SKILL.md](SKILL.md) for the independent analysis and adjudication stages. Interpretation is authored by the executing agent; deterministic scripts must not manufacture Reader prose.

## Privacy

Real case folders are ignored. Calculation strips identifying input metadata unless `--include-pii` is explicitly passed. Before publishing:

```powershell
python scripts/privacy_scan.py .
```

Only the synthetic fixtures under `examples/` are safe to commit.

## Status

Production release 1.0.2. The software pipeline, validation gates and PDF rendering are regression-tested; astrological interpretation itself is not scientifically validated and is not a guaranteed prediction. Do not use it for medical diagnosis, guaranteed financial outcomes or deterministic life decisions.

## Star or support the author

If 4PIE helps your work, please [give the repository a Star ⭐](https://github.com/aidesignlabio/4pie-deep-reader). It helps more people discover the project.

If you would also like to support continued development, choose the payment method that matches your region. See [SUPPORT.md](SUPPORT.md):

1. Hong Kong — PayMe
2. Mainland China — Alipay
3. International — PayPal

## License

MIT. Third-party astrology engines retain their own licenses.
