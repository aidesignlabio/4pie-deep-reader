"""Small, explicit Pythagorean numerology calculator.

Numerology is auxiliary in this project. Only birth-date arithmetic and Latin
Pythagorean name values are supported; CJK stroke counts are intentionally out
of scope because they require a selected dictionary and stroke convention.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, Optional

MASTER_NUMBERS = {11, 22, 33}
VOWELS = set("AEIOUY")


def reduce_number(value: int, *, keep_master: bool = True) -> int:
    value = abs(int(value))
    while value > 9 and not (keep_master and value in MASTER_NUMBERS):
        value = sum(int(digit) for digit in str(value))
    return value


def _parse_birth_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("birth_date must be YYYY-MM-DD") from exc


def _component(value: int) -> int:
    return reduce_number(sum(int(digit) for digit in str(value)), keep_master=True)


def _birth_number(month: int, day: int, year: int) -> Dict[str, Any]:
    month_value = _component(month)
    day_value = _component(day)
    year_value = _component(year)
    raw = month_value + day_value + year_value
    return {
        "value": reduce_number(raw, keep_master=True),
        "raw_total": raw,
        "components": {"month": month_value, "day": day_value, "year": year_value},
        "method": "reduce month/day/year separately, preserve 11/22/33, then reduce total",
    }


def _letter_value(letter: str) -> int:
    return (ord(letter) - ord("A")) % 9 + 1


def _name_numbers(name: Optional[str]) -> Dict[str, Any]:
    if not name:
        return {"expression": None, "soul_urge": None, "personality": None, "letters": None}
    letters = [char for char in name.upper() if "A" <= char <= "Z"]
    if not letters or any(char.isalpha() and ord(char) > 127 for char in name):
        raise ValueError("name numerology supports Latin letters only")
    all_total = sum(_letter_value(char) for char in letters)
    vowel_total = sum(_letter_value(char) for char in letters if char in VOWELS)
    consonant_total = sum(_letter_value(char) for char in letters if char not in VOWELS)

    def result(total: int) -> Dict[str, int]:
        return {"value": reduce_number(total, keep_master=True), "raw_total": total}

    return {
        "expression": result(all_total),
        "soul_urge": result(vowel_total),
        "personality": result(consonant_total),
        "letters": "".join(letters),
    }


def _personal_year(month: int, day: int, year: int) -> Dict[str, Any]:
    raw = _component(month) + _component(day) + _component(year)
    return {
        "year": year,
        "value": reduce_number(raw, keep_master=True),
        "raw_total": raw,
    }


def calculate(birth_date: str, name: Optional[str] = None, current_year: Optional[int] = None) -> Dict[str, Any]:
    birth = _parse_birth_date(birth_date)
    life_path = _birth_number(birth.month, birth.day, birth.year)
    name_values = _name_numbers(name)
    expression = name_values["expression"]
    maturity = None
    if expression:
        maturity_raw = life_path["value"] + expression["value"]
        maturity = {"value": reduce_number(maturity_raw), "raw_total": maturity_raw}

    digit_counts = Counter(int(digit) for digit in birth_date if digit.isdigit() and digit != "0")
    personal_years = []
    if current_year is not None:
        personal_years = [
            _personal_year(birth.month, birth.day, year)
            for year in range(current_year - 1, current_year + 2)
        ]
    result = {
        "role": "auxiliary",
        "life_path": life_path,
        "birthday": {"value": reduce_number(birth.day), "raw_total": birth.day},
        "attitude": {
            "value": reduce_number(_component(birth.month) + _component(birth.day)),
            "raw_total": _component(birth.month) + _component(birth.day),
        },
        "expression": expression,
        "soul_urge": name_values["soul_urge"],
        "personality": name_values["personality"],
        "maturity": maturity,
        "birth_digits": {str(number): digit_counts.get(number, 0) for number in range(1, 10)},
        "missing_numbers": [number for number in range(1, 10) if digit_counts.get(number, 0) == 0],
        "repeated_numbers": {str(number): count for number, count in digit_counts.items() if count > 1},
        "name_letters": name_values["letters"],
        "algorithm": "Pythagorean; Latin names only; master numbers 11/22/33 preserved",
    }
    if personal_years:
        result["personal_year"] = personal_years[1]
        result["personal_years_3"] = personal_years
    return result


if __name__ == "__main__":
    import json
    import sys

    bd = sys.argv[1] if len(sys.argv) > 1 else "2000-01-01"
    supplied_name = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(calculate(bd, supplied_name), indent=2, ensure_ascii=False))
