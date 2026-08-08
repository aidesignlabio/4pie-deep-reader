import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder) / "chart.json"
        env = os.environ.copy()
        env.pop("PYTHONUTF8", None)
        # Give the parent test readable logs without changing Python UTF-8 mode.
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "4pie.py"),
                "calculate",
                "--datetime", "2002-05-04 12:00",
                "--timezone", "Asia/Hong_Kong",
                "--lat", "22.3193",
                "--lon", "114.1694",
                "--gender", "M",
                "--as-of", "2026-08-08",
                "--output", str(output),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=env,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        chart = json.loads(output.read_text(encoding="utf-8"))
        ziwei = chart["systems"]["ziwei"]
        assert ziwei["status"] == "ok", ziwei
        assert len(ziwei["data"]["palaces"]) == 12
    print("zwds utf8 end-to-end calculation: ok")


if __name__ == "__main__":
    main()
