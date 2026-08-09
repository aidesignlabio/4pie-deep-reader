import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def command(case: Path) -> list[str]:
    return [
        sys.executable, str(ROOT / "scripts" / "4pie.py"), "prepare",
        "--case-dir", str(case), "--datetime", "2002-05-04 12:00",
        "--timezone", "Asia/Hong_Kong", "--lat", "22.3193", "--lon", "114.1694",
        "--gender", "M", "--as-of", "2026-08-09", "--start-year", "2026",
    ]


def main():
    with tempfile.TemporaryDirectory() as folder:
        case = Path(folder) / "case"
        first = subprocess.run(command(case) + ["--stop-after", "chart"])
        assert first.returncode == 75
        chart = case / "chart_data.json"
        assert chart.is_file()
        original_mtime = chart.stat().st_mtime_ns
        second = subprocess.run(command(case))
        assert second.returncode == 0
        assert chart.stat().st_mtime_ns == original_mtime
        bundle = json.loads((case / "analysis_bundle.json").read_text(encoding="utf-8"))
        context_path = case / "analysis_context.json"
        context = json.loads(context_path.read_text(encoding="utf-8"))
        assert context["schema_version"] == "analysis_context_v1"
        assert context["professional_gate"]["no_core_downgrades"] is True
        assert context_path.stat().st_size < (case / "analysis_bundle.json").stat().st_size * .6
        assert bundle["requested_years"] == [2026, 2027, 2028, 2029, 2030]
        assert bundle["execution_policy"]["annual_full_chart_recalculation"] == "prohibited"
        third = subprocess.run(command(case))
        assert third.returncode == 0
        state = json.loads((case / "run_state.json").read_text(encoding="utf-8"))
        assert state["stages"]["chart"]["reused"] is True
        assert state["stages"]["bazi_l1"]["reused"] is True
    print("prepare resume and cache: ok")


if __name__ == "__main__":
    main()
