"""Structural and astronomical sanity checks for calculator output."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _result(check: str, ok: bool, detail: str = "") -> Dict[str, Any]:
    return {"check": check, "ok": bool(ok), "detail": detail}


def _longitude(value: Any) -> bool:
    return isinstance(value, (int, float)) and 0 <= float(value) < 360


def validate_bazi(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    pillars = data.get("four_pillars", {}) if isinstance(data, dict) else {}
    checks = [
        _result("four_pillars_present", all(k in pillars for k in ("year", "month", "day", "hour"))),
        _result("day_master_present", bool(data.get("day_master"))),
    ]
    for name in ("year", "month", "day", "hour"):
        pillar = pillars.get(name, {})
        checks.append(
            _result(
                f"{name}_pillar_complete",
                bool(pillar.get("stem")) and bool(pillar.get("branch")),
            )
        )
    return checks


def validate_ziwei(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    palaces = data.get("palaces", {}) if isinstance(data, dict) else {}
    count = len(palaces) if isinstance(palaces, (dict, list)) else 0
    return [
        _result("twelve_palaces", count == 12, f"count={count}"),
        _result("five_elements_class", bool(data.get("five_elements_class"))),
    ]


def validate_western(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    planets = data.get("planets", {}) if isinstance(data, dict) else {}
    expected = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
    longitudes = [p.get("degrees") for p in planets.values() if isinstance(p, dict)]
    angles = data.get("angles", {})
    return [
        _result("ten_planets", expected.issubset(planets), f"count={len(planets)}"),
        _result("planet_longitudes", bool(longitudes) and all(_longitude(x) for x in longitudes)),
        _result("asc_present", angles.get("ASC", {}).get("degrees") is not None),
        _result("mc_present", angles.get("MC", {}).get("degrees") is not None),
        _result("twelve_houses", len(data.get("houses", [])) == 12),
    ]


def validate_vedic(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    planets = data.get("planets", {}) if isinstance(data, dict) else {}
    expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    checks = [
        _result("lagna_present", bool(data.get("lagna", {}).get("sign"))),
        _result("nine_grahas", expected.issubset(planets), f"count={len(planets)}"),
    ]
    rahu = planets.get("Rahu", {}).get("longitude")
    ketu = planets.get("Ketu", {}).get("longitude")
    if _longitude(rahu) and _longitude(ketu):
        separation = abs(((rahu - ketu + 180) % 360) - 180)
        checks.append(_result("rahu_ketu_opposition", abs(separation - 180) < 0.01, f"separation={separation:.4f}"))
    sav = data.get("sav", {})
    if isinstance(sav, dict) and sav:
        total = sum(v for v in sav.values() if isinstance(v, (int, float)))
        checks.append(_result("sav_total_337", total == 337, f"total={total}"))
    return checks


def validate_human_design(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    valid_types = {"Generator", "Manifesting Generator", "Manifestor", "Projector", "Reflector"}
    gates = data.get("active_gates", []) if isinstance(data, dict) else []
    return [
        _result("type_known", data.get("type") in valid_types, str(data.get("type"))),
        _result("authority_present", bool(data.get("authority"))),
        _result("gates_in_range", bool(gates) and all(isinstance(g, int) and 1 <= g <= 64 for g in gates)),
    ]


def validate_numerology(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    life_path = data.get("life_path", {}) if isinstance(data, dict) else {}
    value = life_path.get("value") if isinstance(life_path, dict) else None
    return [_result("life_path_valid", value in set(range(1, 10)) | {11, 22, 33}, str(value))]


VALIDATORS = {
    "bazi": validate_bazi,
    "ziwei": validate_ziwei,
    "western": validate_western,
    "vedic": validate_vedic,
    "human_design": validate_human_design,
    "numerology": validate_numerology,
}


def validate_system(name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    checks = VALIDATORS[name](data)
    return {
        "ok": bool(checks) and all(check["ok"] for check in checks),
        "checks": checks,
    }

