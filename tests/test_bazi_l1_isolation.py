import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    chart={
        "input":{"birth_datetime":"2003-12-06T23:06:00"},
        "systems":{"bazi":{"status":"ok","data":{
            "four_pillars":{"year":{"stem":"癸","branch":"未"},"month":{"stem":"癸","branch":"亥"},"day":{"stem":"癸","branch":"丑"},"hour":{"stem":"癸","branch":"亥"}},
            "true_solar_time":{"input_birth_dt":"2003-12-06T23:06:00"},
            "luck_pillars":[],"annual_cycles":[]
        }}}
    }
    with tempfile.TemporaryDirectory() as d:
        source=Path(d)/"chart.json"; output=Path(d)/"bazi_l1.json"
        source.write_text(json.dumps(chart,ensure_ascii=False),encoding="utf-8")
        result=subprocess.run([sys.executable,str(ROOT/"scripts"/"adjudicate_bazi_l1.py"),str(source),str(output),"--as-of","2026-08-04"])
        assert result.returncode==0
        data=json.loads(output.read_text(encoding="utf-8"))
        assert data["status"]=="ok"
        assert data["strength_decision"]["status"]=="verified"
        assert data["strength_decision"]["value"]=="身旺有根"
        assert data["structure_decision"]["status"]=="conditional_structure"
        assert data["input_audit"]["missing_fields"]==[]
        assert all(x["position"]!="insufficient" for x in data["domain_positions"].values())
        rendered=json.dumps(data,ensure_ascii=False)
        for leaked in ("己土","三卯","丁偏印","庚子","午中己根"):
            assert leaked not in rendered, leaked
        print("bazi_l1_isolation_ok")

if __name__=="__main__": main()
