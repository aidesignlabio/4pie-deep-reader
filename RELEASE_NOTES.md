# 4PIE Deep Reader 1.1.0 International Edition

International bilingual release of the four-system deep-reading and branded Plain Deep PDF pipeline.

This release adds first-class Traditional Chinese and English Readers. Both languages use the same locked chart calculations, native dossiers, adjudication, scores, timing windows and professional gates. The English Reader is composed directly from approved claims rather than translated from a completed Chinese report. The complete Plain Deep PDF interface is localized.

This release removes the 7,000-character padding incentive. Deep reports pass on complete native derivations and eight-domain coverage with a 5,000-character anti-truncation floor. Delivery packaging accepts custom PDF names, and the PDF uses deterministic Noto Sans TC SemiBold 600 body text plus Bold 750 headings on every supported platform.

This release replaces repeated Agent artifact authoring with one compact context, one canonical master analysis and deterministic materialization. Standard and Deep modes share the same calculation, native-analysis and Production Approval gates. The PDF adds AiDesignLab.io branding and stronger Traditional Chinese typography, while delivery packaging avoids rescanning private technical artifacts.

This release introduces the fast resumable report pipeline. One command checks or installs the environment, calculates the four-school natal chart once, completes Bazi L1 once, caches stages by input fingerprint and produces a single analysis bundle. Five-year reporting reuses the bundle rather than recalculating five charts, and divisional sensitivity runs only when a final claim requires it. The Agent performs one bounded analysis pass and at most one validation revision.

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
