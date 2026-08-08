"""Adapter to the mature standalone vedic-calculator skill."""
from __future__ import annotations

import importlib.util
import os
import sys
import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def locate_vedic_calculator() -> Optional[Path]:
    bundled = Path(__file__).resolve().parents[2] / "vedic_engine"
    candidates = [bundled]
    configured = os.environ.get("VEDIC_CALCULATOR_DIR")
    if configured:
        candidates.append(Path(configured).expanduser())
    home = Path.home()
    candidates.extend(
        [
            home / ".minimax" / "skills" / "vedic-calculator",
            home / ".agents" / "skills" / "vedic-calculator",
            home / ".codex" / "skills" / "vedic-calculator",
        ]
    )
    for candidate in candidates:
        if (candidate / "scripts" / "engine.py").is_file():
            return candidate
    return None


def _prepend_runtime_paths(skill_dir: Path) -> None:
    scripts_dir = skill_dir / "scripts"
    site_packages = skill_dir / "venv" / "Lib" / "site-packages"
    for path in (site_packages, scripts_dir):
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def _load_engine(skill_dir: Path):
    _prepend_runtime_paths(skill_dir)
    engine_path = skill_dir / "scripts" / "engine.py"
    spec = importlib.util.spec_from_file_location("six_school_vedic_engine", engine_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Vedic engine: {engine_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _configure_ephemeris() -> None:
    """Pin Swiss Ephemeris state before every external-engine invocation.

    PyJHora changes the process-global ephemeris path while calculating
    dashas.  Without resetting it up front, the first chart in a process can
    use a different ephemeris source from later charts.
    """
    import swisseph as swe
    from jhora.panchanga import drik

    ephe_dir = Path(drik.__file__).resolve().parents[1] / "data" / "ephe"
    if ephe_dir.is_dir():
        swe.set_ephe_path(str(ephe_dir))
    swe.set_sid_mode(swe.SIDM_TRUE_CITRA)


def calculate(
    birth_dt: datetime,
    lat: float,
    lon: float,
    timezone_name: str,
    as_of: Optional[datetime] = None,
) -> Dict[str, Any]:
    skill_dir = locate_vedic_calculator()
    if skill_dir is None:
        raise RuntimeError(
            "vedic-calculator not found; set VEDIC_CALCULATOR_DIR to its skill directory"
        )
    engine = _load_engine(skill_dir)
    _configure_ephemeris()
    raw = engine.calculate_full_chart(
        year=birth_dt.year,
        month=birth_dt.month,
        day=birth_dt.day,
        hour=birth_dt.hour,
        minute=birth_dt.minute,
        lat=lat,
        lon=lon,
        tz_str=timezone_name,
    )
    data = copy.deepcopy(raw)
    data.pop("transits", None)
    _normalize_dasha_boundaries(data)
    _rewrite_current_markers(data, as_of)
    if as_of is not None:
        data["transits"] = _calculate_transits_at(data, as_of)
    data["_engine_version"] = str(getattr(engine, "ENGINE_VERSION", "vedic-calculator-2026.07"))
    return data


def _normalize_dasha_boundaries(data: Dict[str, Any]) -> None:
    """Make adjacent PyJHora periods share one canonical boundary date.

    PyJHora derives a mahadasha end separately from the next period's start.
    A Julian-day value extremely close to midnight can therefore truncate to
    either adjacent civil date across repeated calls.  The next period's first
    antardasha start is the authoritative shared boundary already present in
    the result.
    """
    dashas = data.get("dashas")
    if not isinstance(dashas, list):
        return
    for current, following in zip(dashas, dashas[1:]):
        current_ads = current.get("antardashas") if isinstance(current, dict) else None
        next_ads = following.get("antardashas") if isinstance(following, dict) else None
        if not current_ads or not next_ads:
            continue
        boundary = next_ads[0].get("start")
        if isinstance(boundary, str):
            current_ads[-1]["end"] = boundary


def _date_key(value: Any) -> Optional[tuple[int, int, int]]:
    if not isinstance(value, str):
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.year, parsed.month, parsed.day
        except ValueError:
            pass
    return None


def _rewrite_current_markers(value: Any, as_of: Optional[datetime]) -> None:
    """Replace hidden wall-clock markers from the external engine."""
    if isinstance(value, dict):
        if "is_current" in value:
            start = _date_key(value.get("start"))
            end = _date_key(value.get("end"))
            target = (as_of.year, as_of.month, as_of.day) if as_of else None
            value["is_current"] = bool(target and start and end and start <= target <= end)
        for child in value.values():
            _rewrite_current_markers(child, as_of)
    elif isinstance(value, list):
        for child in value:
            _rewrite_current_markers(child, as_of)


def _calculate_transits_at(chart: Dict[str, Any], as_of: datetime) -> Dict[str, Any]:
    """Reproduce the standalone engine's sidereal transit method at an explicit instant."""
    import swisseph as swe

    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    instant = as_of.astimezone(timezone.utc)
    jd = swe.julday(instant.year, instant.month, instant.day,
                    instant.hour + instant.minute / 60 + instant.second / 3600)
    swe.set_sid_mode(swe.SIDM_TRUE_CITRA)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    lagna_idx = int(chart["lagna"]["sign_idx"])
    moon_idx = int(chart["planets"]["Moon"]["sign_idx"])

    def item(pid: int) -> Dict[str, Any]:
        longitude = swe.calc_ut(jd, pid, flags)[0][0]
        sign_idx = int(longitude / 30)
        return {
            "sign": signs[sign_idx],
            "sign_idx": sign_idx,
            "house": ((sign_idx - lagna_idx) % 12) + 1,
            "longitude": round(longitude, 8),
        }

    transits = {"Saturn": item(swe.SATURN), "Jupiter": item(swe.JUPITER), "Rahu": item(swe.MEAN_NODE)}
    ketu_idx = (transits["Rahu"]["sign_idx"] + 6) % 12
    transits["Ketu"] = {
        "sign": signs[ketu_idx], "sign_idx": ketu_idx,
        "house": ((ketu_idx - lagna_idx) % 12) + 1,
        "longitude": round((transits["Rahu"]["longitude"] + 180) % 360, 8),
    }
    saturn_idx = transits["Saturn"]["sign_idx"]
    relative = (saturn_idx - moon_idx) % 12
    transits["sade_sati"] = {
        11: "phase1_rising", 0: "phase2_peak", 1: "phase3_fading"
    }.get(relative, "inactive")
    sat_h = transits["Saturn"]["house"]
    jup_h = transits["Jupiter"]["house"]
    sat_houses = {((sat_h - 1 + offset) % 12) + 1 for offset in (0, 2, 6, 9)}
    jup_houses = {((jup_h - 1 + offset) % 12) + 1 for offset in (0, 4, 6, 8)}
    transits["double_transit_houses"] = sorted(sat_houses & jup_houses)
    transits["timestamp"] = instant.isoformat()
    transits["method"] = "explicit-as-of; true-citra sidereal; mean node"
    return transits
