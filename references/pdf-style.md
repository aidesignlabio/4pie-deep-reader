# 4PIE Dashboard PDF specification

## Product role

The PDF is a personal strategy dashboard plus a deep-reading report. The dashboard exposes conclusions, school agreement, uncertainty, timing and decisions. The prose explains the native reasoning. Neither replaces the other.

## Page architecture (15-18 pages when evidence supports it)

1. Cover: identity, birth data, four schools, generated date, one core thesis.
2. Life dashboard: five consequential judgments, consensus tier, relevant years, 4-6 qualitative indicators.
3. Four-school method: role, qualified questions, verified modules and limitations for this run.
4. Consensus matrix: domains by schools, using symbols and plain counts; never percentages.
5. Life-stage timeline: stage theme, task, favourable and risk versions.
6-7. Career dashboard and native reasoning.
8-9. Wealth dashboard and native reasoning.
10-11. Relationship dashboard and native reasoning.
12. Home, family, relocation and assets.
13-14. Requested annual roadmap and ranked windows.
15-16. Decision tables: career/development and relationship/assets.
17. Ninety-day action page.
18. Technical boundary and evidence appendix opener. Continue the appendix only when needed.

Do not force a blank or weak page to reach a page count. Expand strong domains and compress unsupported ones.

## Visual system

- A4 portrait, 18-20 mm margins, high white space, one dominant question per page.
- Background `#F7F5F0`; surface `#FFFFFF`; ink `#17324D`; body `#2F3A45`; muted `#6B7785`; line `#DCE3E8`.
- Primary blue `#244E73`; secondary blue `#7398B6`; soft blue `#EAF1F6`.
- Opportunity `#DCEAE6`; caution `#F3E8D2`; risk `#F2DEDD`; single-school `#E7E3ED`.
- Traditional Chinese sans body; restrained serif-like scale may be used only for the cover title when an embeddable font exists.
- H1 28-32 pt, H2 17-20 pt, H3 12-15 pt, body 9.5-10.8 pt, support 8-9 pt.
- Cards use 3-4 mm corner radius, hairline border, almost no shadow. Avoid decorative mysticism and heavy gradients.

## Honest visual encoding

Never invent 86/100, accuracy percentages, probability stars, or pseudo-scientific gauges.

Use these qualitative labels:

- high / medium-high / medium / medium-low;
- high consensus / moderate consensus / single-school signal / conflict / insufficient;
- `●` support, `◐` refine or indirect support, `○` not applicable or no signal, `△` limit/conflict, `?` insufficient.

Every indicator must name the facts or adjudicated claims that produced it. If no explicit calculation rule exists, show a label or segmented scale without a number.

## Reusable components

### Consequential judgment card

Number, title, one-sentence ruling, consensus badge, event certainty when relevant, main years. Maximum 65 Chinese characters beyond the title.

### Four-school evidence strip

Four fixed school cells. Each shows position symbol, one plain-language reason, and claim ID in support text. Calculation details stay in the appendix.

### Domain dashboard

Top: core ruling, consensus, event certainty, largest uncertainty.

Middle: four-school evidence strip plus two columns for favourable realization and risk branch.

Bottom: validation questions and three time horizons: now (30-90 days), medium (1-2 years), long (3-5 years). Advice must be visually labelled as advice.

### Timing bar

Show background period, narrower sensitivity window, transition markers, and event carrier. Print this note on every timing overview: `日期代表週期切換或主題增強，不代表當日必然發生單一事件。`

### Consensus matrix

Rows are questions or domains; columns are Western, Zi Wei, Vedic, and Bazi. The final column uses words such as `3派支持／1派修正`, never 90%.

### Validation and action cards

Validation uses questions and a neutral surface. Action uses low-saturation green-blue. Risk uses pale amber or red. Never style advice as chart evidence.

## Content rules

- Display disagreement; never make the four schools appear unanimously supportive.
- Separate chart judgment, reality projection, advice and validation.
- Explain a global mechanism once. Later pages reference it briefly and add only domain-specific consequences.
- Keep tables to five columns when possible. Split dense decision tables across pages.
- Use no more than five principal timing windows and three event families per window.
- Each page must support the reading path: understand the ruling, inspect consensus, see risk, locate time, decide, act.

## Input contract for the renderer

Pass `--packet fate_packet.json` to generate data-backed dashboard pages. The packet should use `model_version: transparent_v1` and include:

- `consequential_judgments`;
- `school_role_manifest`;
- `consensus_matrix`;
- `fate_adjudication`;
- `timing_windows` and `annual_rulings`.

If a dashboard field is absent, omit that component. Do not infer a score or fill it with generic text.

## QA gates

1. Reopen with `pypdf` or `pdfplumber`; verify page count and extractable Traditional Chinese.
2. Render every page to PNG with Poppler.
3. Inspect cover, dashboard, matrix, all table-heavy pages, transitions, timeline and last page.
4. Reject clipping, orphan headings, table overflow, missing glyphs, black squares, blanks, uneven margins or footer collisions.
5. Save the PDF, rendered pages and `pdf_qa.json` together.
