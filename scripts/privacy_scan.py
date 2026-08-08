#!/usr/bin/env python3
import argparse, re, sys
from pathlib import Path

TEXT_EXT={".md",".txt",".json",".yaml",".yml",".py",".ps1",".sh",".toml",".cfg"}
PATTERNS={
 "windows_user_path":re.compile(r"[A-Za-z]:\\Users\\(?!example|runner)[^\\\s]+",re.I),
 "email":re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",re.I),
 "known_private_fixture":re.compile(r"2002[-年/]0?3[-月/]1?2|05[:：]52",re.I),
 "known_private_name":re.compile(r"張小姐",re.I),
}
SKIP={".git","__pycache__","node_modules",".venv","venv"}
def main():
 p=argparse.ArgumentParser(); p.add_argument("path",nargs="?",default="."); a=p.parse_args(); root=Path(a.path); findings=[]
 for f in root.rglob("*"):
  if not f.is_file() or f.suffix.lower() not in TEXT_EXT or any(x in SKIP for x in f.parts): continue
  if f.resolve() == Path(__file__).resolve(): continue
  try: text=f.read_text(encoding="utf-8")
  except UnicodeDecodeError: continue
  for name,rx in PATTERNS.items():
   for m in rx.finditer(text): findings.append((str(f),name,m.group(0)[:80]))
 for row in findings: print(" | ".join(row))
 print(f"privacy_findings={len(findings)}")
 return 1 if findings else 0
if __name__=="__main__": raise SystemExit(main())
