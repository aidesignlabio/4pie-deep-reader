"""Read-only environment diagnostics for six-school-calculator."""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from calculators.vedic_adapter import locate_vedic_calculator, _prepend_runtime_paths


ROOT = Path(__file__).resolve().parent


def check() -> dict:
    result = {"python": {"ok": sys.version_info >= (3, 10), "version": sys.version.split()[0]}}
    try:
        import swisseph as swe
        result["swisseph"] = {"ok": getattr(swe, "version", "0.0.0") != "0.0.0", "version": getattr(swe, "version", "unknown")}
    except Exception as exc:
        result["swisseph"] = {"ok": False, "error": str(exc)}

    node_dir = ROOT / "node"
    try:
        completed = subprocess.run(
            ["node", "-e", "console.log(require('iztro/package.json').version)"],
            cwd=node_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=15,
        )
        result["iztro"] = {"ok": completed.returncode == 0, "version": completed.stdout.strip(), "error": completed.stderr.strip()}
    except Exception as exc:
        result["iztro"] = {"ok": False, "error": str(exc)}

    vedic_dir = locate_vedic_calculator()
    if vedic_dir is None:
        result["vedic_calculator"] = {"ok": False, "error": "skill not found"}
    else:
        try:
            _prepend_runtime_paths(vedic_dir)
            import dashaflow  # noqa: F401
            import jhora  # noqa: F401
            import pytz  # noqa: F401
            result["vedic_calculator"] = {"ok": True, "path": str(vedic_dir)}
        except Exception as exc:
            result["vedic_calculator"] = {"ok": False, "path": str(vedic_dir), "error": str(exc)}

    result["core_ready"] = all(result[k]["ok"] for k in ("python", "swisseph", "iztro", "vedic_calculator"))
    return result


if __name__ == "__main__":
    diagnostics = check()
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    raise SystemExit(0 if diagnostics["core_ready"] else 2)
