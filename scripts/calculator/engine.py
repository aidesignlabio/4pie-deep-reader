"""Canonical deterministic pipeline for six astrology-related systems."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Optional
from zoneinfo import ZoneInfo

from calculators import bazi, humandesign, numerology, vedic_adapter, western, zwds
from validator import validate_system


SCHEMA_VERSION = "1.1.0"
ENGINE_VERSION = "1.1.0"
SYSTEM_ORDER = ("bazi", "ziwei", "western", "vedic", "human_design", "numerology")
SYSTEM_ROLES = {
    "bazi": "core",
    "ziwei": "core",
    "western": "core",
    "vedic": "core",
    "human_design": "auxiliary",
    "numerology": "auxiliary",
}
ENGINE_NAMES = {
    "bazi": "native-python-bazi",
    "ziwei": "iztro",
    "western": "swiss-ephemeris-tropical-placidus",
    "vedic": "vedic-calculator",
    "human_design": "swiss-ephemeris-rave-iching",
    "numerology": "native-python-numerology",
}
ENGINE_VERSIONS = {
    "bazi": "3.1.0",
    "ziwei": "2.5.8",
    "western": "1.0.0",
    "vedic": "external",
    "human_design": "1.0.0",
    "numerology": "1.1.0",
}
MAINLAND_PRE_1949_TZ = {
    "Asia/Shanghai", "Asia/Chongqing", "Asia/Harbin", "Asia/Urumqi",
}


def parse_birth_datetime(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError("birth_datetime_local must be YYYY-MM-DD HH:MM[:SS]")


def _zoneinfo_resolution(timezone_name: str, local_dt: datetime, dst_fold: Optional[int]) -> Dict[str, Any]:
    """Resolve a wall time while detecting DST gaps and duplicated times."""
    zone = ZoneInfo(timezone_name)
    candidates = []
    for fold in (0, 1):
        aware = local_dt.replace(tzinfo=zone, fold=fold)
        round_trip = aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
        if round_trip == local_dt:
            candidates.append((fold, aware))
    unique_offsets = {aware.utcoffset() for _, aware in candidates}
    if not candidates:
        raise ValueError(f"Local time {local_dt} does not exist in {timezone_name} (DST gap)")
    if len(unique_offsets) > 1:
        if dst_fold not in (0, 1):
            raise ValueError("Ambiguous local time; pass dst_fold=0 or dst_fold=1")
        aware = next((value for fold, value in candidates if fold == dst_fold), None)
        if aware is None:
            raise ValueError(f"dst_fold={dst_fold} is not valid for this local time")
        chosen_fold = dst_fold
    else:
        aware = candidates[0][1]
        chosen_fold = 0
    offset = aware.utcoffset()
    if offset is None:
        raise ValueError(f"Cannot resolve timezone offset: {timezone_name}")
    return {
        "iana_tz": timezone_name,
        "utc_offset_minutes": int(offset.total_seconds() // 60),
        "dst_applied": bool((aware.dst() or timedelta(0)).total_seconds()),
        "dst_fold": chosen_fold,
        "resolution_method": "iana_tzdata",
    }


def resolve_timezone(
    timezone_name: str,
    local_dt: datetime,
    *,
    utc_offset_override_minutes: Optional[int] = None,
    dst_fold: Optional[int] = None,
) -> Dict[str, Any]:
    if local_dt.year < 1949 and timezone_name in MAINLAND_PRE_1949_TZ and utc_offset_override_minutes is None:
        raise ValueError(
            "Pre-1949 Mainland China time requires --utc-offset-override-minutes and manual review"
        )
    if utc_offset_override_minutes is not None:
        if not -840 <= utc_offset_override_minutes <= 840:
            raise ValueError("utc_offset_override_minutes must be between -840 and 840")
        return {
            "iana_tz": timezone_name,
            "utc_offset_minutes": int(utc_offset_override_minutes),
            "dst_applied": False,
            "dst_fold": None,
            "resolution_method": "manual_review",
        }
    try:
        return _zoneinfo_resolution(timezone_name, local_dt, dst_fold)
    except ValueError:
        raise
    except Exception:
        # Windows Python distributions may omit IANA tzdata. Reuse pytz from
        # the standalone Vedic runtime while preserving explicit ambiguity.
        vedic_dir = vedic_adapter.locate_vedic_calculator()
        if vedic_dir is not None:
            vedic_adapter._prepend_runtime_paths(vedic_dir)
        try:
            import pytz
            zone = pytz.timezone(timezone_name)
            is_dst = None if dst_fold is None else dst_fold == 0
            aware = zone.localize(local_dt, is_dst=is_dst)
            offset = aware.utcoffset()
            if offset is None:
                raise ValueError(f"Cannot resolve timezone offset: {timezone_name}")
            return {
                "iana_tz": timezone_name,
                "utc_offset_minutes": int(offset.total_seconds() // 60),
                "dst_applied": bool((aware.dst() or timedelta(0)).total_seconds()),
                "dst_fold": dst_fold,
                "resolution_method": "iana_tzdata",
            }
        except pytz.NonExistentTimeError as exc:
            raise ValueError(f"Local time {local_dt} does not exist in {timezone_name} (DST gap)") from exc
        except pytz.AmbiguousTimeError as exc:
            raise ValueError("Ambiguous local time; pass dst_fold=0 or dst_fold=1") from exc
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(
                f"Cannot resolve IANA timezone {timezone_name!r}; install tzdata or pytz"
            ) from exc


def timezone_offset_hours(timezone_name: str, local_dt: datetime) -> float:
    """Compatibility helper retained for callers using the 1.0 API."""
    return resolve_timezone(timezone_name, local_dt)["utc_offset_minutes"] / 60


def parse_as_of(
    value: Optional[str],
    timezone_name: str,
    utc_offset_minutes: Optional[int] = None,
) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text += "T12:00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("as_of must be an ISO 8601 date or datetime") from exc
    if parsed.tzinfo is None:
        try:
            parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
        except Exception:
            if utc_offset_minutes is None:
                raise ValueError(f"Cannot attach timezone {timezone_name} to as_of")
            parsed = parsed.replace(tzinfo=timezone(timedelta(minutes=utc_offset_minutes)))
    return parsed


def _validate_input(gender: str, lat: float, lon: float) -> str:
    normalized = str(gender).upper()
    aliases = {"男": "M", "女": "F", "MALE": "M", "FEMALE": "F", "M": "M", "F": "F", "X": "X"}
    if normalized not in aliases:
        raise ValueError("gender must be M, F, X, 男, or 女")
    if not -90 <= lat <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return aliases[normalized]


def _latin_name_or_none(name: Optional[str]) -> Optional[str]:
    if name and re.fullmatch(r"[A-Za-z .'-]+", name):
        return name
    return None


def _calculate_one(
    system: str,
    birth_dt: datetime,
    timezone_name: str,
    tz_offset: float,
    lat: float,
    lon: float,
    gender: str,
    name: Optional[str],
    as_of: Optional[datetime],
) -> Dict[str, Any]:
    try:
        if system == "bazi":
            data = bazi.calculate(birth_dt, lat, lon, tz_offset, gender)
        elif system == "ziwei":
            data = zwds.calculate(birth_dt, lat, lon, tz_offset, gender)
        elif system == "western":
            data = western.calculate(birth_dt, lat, lon, tz_offset)
        elif system == "vedic":
            data = vedic_adapter.calculate(birth_dt, lat, lon, timezone_name, as_of=as_of)
        elif system == "human_design":
            data = humandesign.calculate(birth_dt, lat, lon, tz_offset)
        elif system == "numerology":
            data = numerology.calculate(
                birth_dt.strftime("%Y-%m-%d"),
                _latin_name_or_none(name),
                as_of.year if as_of else None,
            )
            data["role_note"] = "Auxiliary only in core_plus_aux; no CJK name numerology."
        else:
            raise ValueError(f"Unknown system: {system}")
        if not isinstance(data, dict):
            raise TypeError(f"{system} returned {type(data).__name__}, expected dict")
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        engine_version = str(data.pop("_engine_version", ENGINE_VERSIONS[system]))
        validation = validate_system(system, data)
        return {
            "role": SYSTEM_ROLES[system],
            "status": "ok" if validation["ok"] else "invalid",
            "engine": ENGINE_NAMES[system],
            "engine_version": engine_version,
            "data": data,
            "validation": validation,
        }
    except Exception as exc:
        return {
            "role": SYSTEM_ROLES[system],
            "status": "failed",
            "engine": ENGINE_NAMES[system],
            "engine_version": ENGINE_VERSIONS[system],
            "error": f"{type(exc).__name__}: {exc}",
            "data": None,
            "validation": {"ok": False, "checks": []},
        }


def _boundary_warnings(effective_dt: datetime) -> list[str]:
    minute_of_day = effective_dt.hour * 60 + effective_dt.minute
    boundaries = [hour * 60 for hour in range(1, 24, 2)]
    distance = min(abs(minute_of_day - value) for value in boundaries)
    distance = min(distance, 1440 - distance)
    if distance <= 15:
        return [f"East Asian chart time is {distance} minutes from a shichen boundary"]
    return []


def calculate_chart(
    *,
    birth_datetime_local: str,
    timezone_name: str,
    lat: float,
    lon: float,
    gender: str = "X",
    name: Optional[str] = None,
    place: Optional[str] = None,
    current_year: Optional[int] = None,
    as_of: Optional[str] = None,
    utc_offset_override_minutes: Optional[int] = None,
    dst_fold: Optional[int] = None,
    east_asian_time_basis: str = "civil",
    systems: Iterable[str] = SYSTEM_ORDER,
) -> Dict[str, Any]:
    birth_dt = parse_birth_datetime(birth_datetime_local)
    normalized_gender = _validate_input(gender, lat, lon)
    if east_asian_time_basis not in {"civil", "true_solar"}:
        raise ValueError("east_asian_time_basis must be civil or true_solar")
    timezone_resolution = resolve_timezone(
        timezone_name,
        birth_dt,
        utc_offset_override_minutes=utc_offset_override_minutes,
        dst_fold=dst_fold,
    )
    tz_offset = timezone_resolution["utc_offset_minutes"] / 60
    selected = tuple(dict.fromkeys(systems))
    unknown = sorted(set(selected) - set(SYSTEM_ORDER))
    if unknown:
        raise ValueError(f"Unknown systems: {', '.join(unknown)}")
    if current_year is not None and as_of is not None:
        raise ValueError("Use either current_year/--year or as_of/--as-of, not both")
    if current_year is not None:
        as_of = f"{current_year:04d}-07-01"
    as_of_dt = parse_as_of(as_of, timezone_name, timezone_resolution["utc_offset_minutes"])

    true_solar_dt = (
        bazi.true_solar_time(birth_dt, lon, tz_offset)[0]
        if any(s in selected for s in ("bazi", "ziwei")) else birth_dt
    )
    ziwei_dt = true_solar_dt if east_asian_time_basis == "true_solar" else birth_dt

    results = {
        system: _calculate_one(
            system,
            ziwei_dt if system == "ziwei" else birth_dt,
            timezone_name,
            tz_offset,
            lat,
            lon,
            normalized_gender,
            name,
            as_of_dt,
        )
        for system in selected
    }
    core_failures = [
        key for key, result in results.items()
        if result["role"] == "core" and result["status"] != "ok"
    ]
    auxiliary_failures = [
        key for key, result in results.items()
        if result["role"] == "auxiliary" and result["status"] != "ok"
    ]
    result = {
        "schema_version": SCHEMA_VERSION,
        "engine": {"name": "six-school-calculator", "version": ENGINE_VERSION},
        "subject": {
            "name": name,
            "gender": normalized_gender,
            "birth_datetime_local": birth_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": timezone_name,
            "utc_offset_hours": tz_offset,
            "place": place,
            "latitude": lat,
            "longitude": lon,
        },
        "calculation_context": {
            "timezone_resolution": timezone_resolution,
            "as_of": as_of_dt.isoformat() if as_of_dt else None,
            "east_asian_time_basis": {"bazi": "true_solar", "ziwei": east_asian_time_basis},
            "civil_datetime_local": birth_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "true_solar_datetime_local": true_solar_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "ziwei_effective_datetime_local": ziwei_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "true_solar_time_correction_minutes": round((true_solar_dt - birth_dt).total_seconds() / 60, 6),
            "boundary_warnings": {
                "bazi": _boundary_warnings(true_solar_dt),
                "ziwei": _boundary_warnings(ziwei_dt),
            },
            "canonical_excludes_wall_clock_timestamp": True,
        },
        "system_policy": {
            "core": [s for s in selected if SYSTEM_ROLES[s] == "core"],
            "auxiliary": [s for s in selected if SYSTEM_ROLES[s] == "auxiliary"],
            "numerology_equal_weight": False,
            "default_convergence_profile": "core_plus_aux",
        },
        "systems": results,
        "validation_summary": {
            "ok": not core_failures,
            "core_failures": core_failures,
            "auxiliary_failures": auxiliary_failures,
        },
    }
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    fingerprint = hashlib.sha256(encoded).hexdigest()
    result["calc_version_hash"] = fingerprint
    result["chart_id"] = f"chart_{fingerprint[:20]}"
    return result


def strip_pii(chart: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(chart)
    subject = result.get("subject", {})
    subject["name"] = "[REDACTED]"
    birth = subject.pop("birth_datetime_local", None)
    if birth:
        subject["birth_year"] = birth[:4]
    subject.pop("latitude", None)
    subject.pop("longitude", None)
    return result
