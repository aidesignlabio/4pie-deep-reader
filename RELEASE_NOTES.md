# 4PIE Deep Reader 1.0.4

Cross-platform production release of the four-system deep-reading and Plain Deep PDF pipeline.

This maintenance release fixes the remaining agent-execution failure mode: first setup is explicitly treated as a 2–10 minute operation with a required 15-minute host timeout, and a timed-out outer tool must wait for the live `.setup.lock` owner instead of invoking setup again. All post-install commands now route through the UTF-8-safe unified launcher; standalone Bazi L1 output is UTF-8-safe as a fallback.

## Release guarantees

- Fresh setup verifies Python, Swiss Ephemeris, PyJHora, DashaFlow, `iztro@2.5.8` and PDF dependencies.
- Fresh setup installs the release-pinned Noto Sans TC font so PDF typography stays consistent on Windows, macOS and Linux.
- Production PDF generation is blocked unless all four core systems, Bazi L1, four dossiers, eight-domain adjudication, eight complete scores, five consecutive annual rulings and the Reader pass validation.
- Failed validation or rendering leaves no partial production PDF.
- The default PDF uses the fixed `Plain_Deep_Report_v1` editorial design and dynamic case data.
- Release archives exclude private cases, generated reports, virtual environments, `node_modules` and local paths.
- GitHub Actions validates clean setup and the regression suite on both Ubuntu and Windows.

## Supported runtime

- Python 3.8-3.13
- Node.js with npm
- Windows, macOS or Linux

## Important boundary

The software pipeline is tested. Astrology is not scientifically validated, and the report must not be treated as medical, legal or guaranteed financial advice.
