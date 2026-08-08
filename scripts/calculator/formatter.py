"""Human-readable, calculation-only Markdown formatter."""
from __future__ import annotations

from typing import Any, Dict, List


def _value(obj: Any, *keys: str, default: str = "—") -> Any:
    for key in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(key)
    return default if obj in (None, "") else obj


def _system_data(chart: Dict[str, Any], name: str) -> Dict[str, Any]:
    item = chart.get("systems", {}).get(name, {})
    return item.get("data") or {}


def format_structured_data(chart: Dict[str, Any]) -> str:
    subject = chart.get("subject", {})
    lines: List[str] = [
        "# Multi-system chart data",
        "",
        f"> Engine: six-school-calculator {chart.get('engine', {}).get('version', '?')}",
        f"> Schema: {chart.get('schema_version', '?')}",
        "> This file contains calculated data, not an interpretation.",
        "",
        "## Subject",
        "",
        f"- Name: {subject.get('name') or '—'}",
        f"- Gender: {subject.get('gender', '—')}",
        f"- Local birth time: {subject.get('birth_datetime_local', '—')}",
        f"- Timezone: {subject.get('timezone', '—')} (UTC{subject.get('utc_offset_hours', 0):+g})",
        f"- Place: {subject.get('place') or '—'}",
        f"- Coordinates: {subject.get('latitude', '—')}, {subject.get('longitude', '—')}",
        "",
        "## Engine status",
        "",
    ]
    for name, item in chart.get("systems", {}).items():
        lines.append(
            f"- {name}: {item.get('status')} · {item.get('role')} · {item.get('engine')}"
            + (f" · {item.get('error')}" if item.get("error") else "")
        )

    bazi = _system_data(chart, "bazi")
    if bazi:
        pillars = bazi.get("four_pillars", {})
        pillar_text = " / ".join(
            f"{_value(pillars, p, 'stem')}{_value(pillars, p, 'branch')}"
            for p in ("year", "month", "day", "hour")
        )
        lines.extend([
            "", "## Bazi", "",
            f"- Four pillars: {pillar_text}",
            f"- Day master: {bazi.get('day_master', '—')}",
            f"- Strength: {bazi.get('day_master_strength', '—')}",
            f"- Useful god: {bazi.get('useful_god', '—')}",
        ])

    ziwei = _system_data(chart, "ziwei")
    if ziwei:
        lines.extend(["", "## Zi Wei Dou Shu", "", f"- Five-elements class: {ziwei.get('five_elements_class', '—')}"])
        palaces = ziwei.get("palaces", {})
        iterable = palaces.items() if isinstance(palaces, dict) else ((p.get("name", "?"), p) for p in palaces)
        for name, palace in iterable:
            stars = palace.get("all_major_stars") or palace.get("major_stars") or []
            lines.append(f"- {name}: {', '.join(stars) if stars else 'empty palace'}")

    western = _system_data(chart, "western")
    if western:
        lines.extend([
            "", "## Western astrology", "",
            f"- ASC: {_value(western, 'angles', 'ASC', 'sign')} {_value(western, 'angles', 'ASC', 'degrees')}",
            f"- MC: {_value(western, 'angles', 'MC', 'sign')} {_value(western, 'angles', 'MC', 'degrees')}",
        ])
        for name, planet in western.get("planets", {}).items():
            lines.append(f"- {name}: {planet.get('sign', '—')} · house {planet.get('house', '—')} · {planet.get('degrees', '—')}°")

    vedic = _system_data(chart, "vedic")
    if vedic:
        lines.extend(["", "## Vedic astrology", "", f"- Lagna: {_value(vedic, 'lagna', 'sign')} {_value(vedic, 'lagna', 'deg_str')}"])
        for name, planet in vedic.get("planets", {}).items():
            lines.append(f"- {name}: {planet.get('sign', '—')} · house {planet.get('house', '—')} · {planet.get('deg_str', '—')}")

    hd = _system_data(chart, "human_design")
    if hd:
        lines.extend([
            "", "## Human Design (auxiliary)", "",
            f"- Type: {hd.get('type', '—')}",
            f"- Strategy: {hd.get('strategy', '—')}",
            f"- Authority: {hd.get('authority', '—')}",
            f"- Profile: {hd.get('profile', '—')}",
            f"- Definition: {hd.get('definition', '—')}",
        ])

    num = _system_data(chart, "numerology")
    if num:
        lines.extend([
            "", "## Numerology (auxiliary)", "",
            f"- Life Path: {_value(num, 'life_path', 'value')}",
            f"- Personal year: {_value(num, 'personal_year', 'value')}",
            "- Policy: auxiliary in core_plus_aux; equal_six is a downstream reader option",
        ])

    lines.extend(["", "## Validation", "", f"- Core valid: {chart.get('validation_summary', {}).get('ok', False)}"])
    return "\n".join(lines) + "\n"
