from datetime import datetime
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "calculator" / "calculators" / "zwds.py"
spec = importlib.util.spec_from_file_location("zwds_under_test", PATH)
zwds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zwds)


def main():
    captured = {}

    class Result:
        returncode = 0
        stdout = json.dumps({"palaces": {}}, ensure_ascii=False)
        stderr = ""

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return Result()

    original = zwds.subprocess.run
    zwds.subprocess.run = fake_run
    try:
        zwds.calculate_via_node(datetime(2002, 5, 4, 12, 0), 22.3193, 114.1694, 8, "M")
    finally:
        zwds.subprocess.run = original
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "strict"
    assert captured["env"]["PYTHONIOENCODING"] == "utf-8"
    print("zwds utf8 subprocess contract: ok")


if __name__ == "__main__":
    main()
