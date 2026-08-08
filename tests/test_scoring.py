import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    with tempfile.TemporaryDirectory() as d:
        out=Path(d)/"scores.json"
        subprocess.run([sys.executable,str(ROOT/"scripts"/"score_domains.py"),str(ROOT/"examples"/"synthetic_score_input.json"),str(out)],check=True)
        data=json.loads(out.read_text(encoding="utf-8")); row=data["domains"][0]
        assert row["formula_version"]=="4pie-score-1.0"
        assert 0<=row["flow_score"]<=100 and 0<=row["confidence_score"]<=100
        print("scoring_ok")
if __name__=="__main__": main()

