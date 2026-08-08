# Privacy policy

- The calculator strips identifying input metadata by default. Never use `--include-pii` for public or release artifacts.
- Never commit real names, exact private birth records, addresses, emails, phone numbers, local user paths, conversation exports or generated client reports.
- Keep user cases under `private_cases/` or another ignored directory.
- Public examples must say `synthetic: true` and use the bundled synthetic fixture only.
- Do not use conversation traits or biographies in `blind_chart_only` mode.
- Before release, run `python scripts/privacy_scan.py .` and require exit code 0.
- Treat birth date, exact time and coordinates together as identifying data even when the name is absent.
- Remove PDF metadata and filenames that contain client names.
