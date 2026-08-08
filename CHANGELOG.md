# Changelog

## 1.0.4

- Make the Skill require a 15-minute host-tool timeout for first setup and forbid setup retries while `.setup.lock` identifies a live installer.
- Require every post-install operation to use the unified `scripts/4pie.py` launcher instead of internal scripts.
- Make the standalone Bazi L1 diagnostic explicitly emit UTF-8 as a second layer of Windows protection.
- Print first-install duration and timeout guidance before setup begins.

## 1.0.3

- Force UTF-8 at every Zi Wei Node boundary and unified CLI child process, independent of the Windows console code page or `PYTHONUTF8` shell state.
- Serialize setup with a cross-platform installation lock: a retry waits for the active setup instead of launching a second pip/npm process and causing file locks.
- Add regressions for CP950-safe Zi Wei calculation and concurrent installer protection.
- Run the Windows regression suite without `PYTHONUTF8` to prevent this encoding bug from returning.

## 1.0.2

- Add a Star call-to-action and an optional author-support page.
- Add regional support options in the requested order: Hong Kong PayMe, Mainland China Alipay and international PayPal.

## 1.0.1

- Install a release-pinned Noto Sans TC font during setup and prefer it in the PDF renderer for consistent cross-platform typography.
- Fix Unix setup execution in GitHub Actions and enforce UTF-8 for Windows regression tests.
- Validate the complete setup and regression suite on both Ubuntu and Windows.

## 1.0.0

- Promote the tested Plain Deep pipeline to the first production release.
- Complete the generic Bazi L1 fallback contract from verified four pillars: seasonal authority, weighted hidden stems, roots, visible/hidden support, strength decision and conditional structure candidate.
- Preserve localized domain labels through formula-backed scoring and into the PDF dashboard.
- Require one report title and at least eight Reader chapters at Production Approval.
- Keep the hard no-degrade gate introduced in 0.9.4: incomplete calculations, dossiers, adjudication, scores, years or Reader content cannot produce a PDF.
- Validate clean installation, four-system smoke calculation, production rendering, PDF page rendering, text extraction and privacy scanning before release.

## 0.9.4-beta

- Add a non-bypassable Production Gate: no production PDF is created unless all four systems, Bazi L1, four dossiers, adjudication, eight score rows and five consecutive annual rulings pass.
- Delete partial output automatically when validation or rendering fails.
- Route the public `render` command through the production validator; keep the low-level renderer internal.
- Require exactly eight complete four-dimensional score rows with numeric values from 0 to 100.
- Require the requested five-year sequence instead of silently substituting available years.
- Add an end-to-end production render and PDF QA regression test.

## 0.9.3-beta

- Make the exact reusable `Plain_Deep_Report_v1` renderer the default and keep `dashboard` opt-in.
- Preserve its mountain cover, card contents, eight-domain bar dashboard, five-year vertical index and compact chapter-band body.
- Add generated contents, formula-backed scores and annual time index to the default PDF.
- Remove subject-specific Bazi prose from the L1 adjudicator.
- Preserve incomplete Bazi L1 only as a technical diagnostic; it cannot pass Production Approval or generate a production PDF.
- Add regression tests for cross-case Bazi isolation and PDF design selection.
- Add fast `doctor` and `smoke` commands; dependency installation remains a one-time step.
- Add cross-platform `pdf-qa` rendering with PyMuPDF, removing the runtime Poppler dependency.

## 0.9.1-beta

- Add one-command isolated runtime setup.
- Install pinned Python and Node dependencies automatically.
- Repair PyJHora/pyswisseph compatibility and enforce the configured mean-node policy.
- Add a synthetic four-system end-to-end smoke test.
