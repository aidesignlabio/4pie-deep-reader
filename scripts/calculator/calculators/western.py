"""
western.py - 西方占星計算

實作:用 pyswisseph 計算 Tropical Western chart

依賴:
  - pip install pyswisseph
"""

from datetime import datetime, timedelta
from typing import Dict, Any

# 12 星座(Tropical 順序,從 Aries 開始)
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# 行星代碼(swisseph)
PLANETS = {
    "Sun": 0, "Moon": 1, "Mercury": 2, "Venus": 3, "Mars": 4,
    "Jupiter": 5, "Saturn": 6, "Uranus": 7, "Neptune": 8, "Pluto": 9
}

# 主要相位(Ptolemaic 5 + Quincunx)
MAJOR_ASPECTS = {
    0: ("Conjunction", 8),
    60: ("Sextile", 6),
    90: ("Square", 8),
    120: ("Trine", 8),
    180: ("Opposition", 8),
    150: ("Quincunx", 3)
}

# Sprint 1.10: Minor aspects(v3.1.0)
MINOR_ASPECTS = {
    30: ("Semi-sextile", 1.5),
    45: ("Semi-square", 2),
    72: ("Quintile", 1.5),
    135: ("Sesqui-square", 2),
    144: ("Bi-quintile", 1),
}

# 合併(向後相容 ASPECTS 變數)
ASPECTS = {**MAJOR_ASPECTS, **MINOR_ASPECTS}


def calculate_minor_aspects(planets_data: Dict[str, float]) -> list:
    """獨立計算 Minor aspects(不回傳 Major)"""
    aspects = []
    planet_list = list(planets_data.items())
    for i, (p1, lon1) in enumerate(planet_list):
        for p2, lon2 in planet_list[i + 1:]:
            diff = abs(lon1 - lon2) % 360
            if diff > 180:
                diff = 360 - diff

            for angle, (name, orb) in MINOR_ASPECTS.items():
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "planet1": p1,
                        "planet2": p2,
                        "type": name,
                        "angle": angle,
                        "orb": round(abs(diff - angle), 2),
                        "category": "minor"
                    })
                    break
    return aspects


def calculate_aspects(planets_data: Dict[str, float]) -> list:
    """計算所有行星間主要相位"""
    aspects = []
    planet_list = list(planets_data.items())
    for i, (p1, lon1) in enumerate(planet_list):
        for p2, lon2 in planet_list[i + 1:]:
            diff = abs(lon1 - lon2) % 360
            if diff > 180:
                diff = 360 - diff

            for angle, (name, orb) in ASPECTS.items():
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "planet1": p1,
                        "planet2": p2,
                        "type": name,
                        "angle": angle,
                        "orb": round(abs(diff - angle), 2)
                    })
                    break
    return aspects


def calculate(birth_dt: datetime, lat: float, lon: float, tz_offset: float = 8.0) -> Dict[str, Any]:
    """
    主入口:用 pyswisseph 計算 Tropical Western chart
    """
    try:
        import swisseph as swe
    except ImportError:
        return {
            "error": "pyswisseph not installed. Run: pip install pyswisseph",
            "note": "西方占星需要精確行星位置 + ASC/MC"
        }

    # Swiss Ephemeris expects UT. `birth_dt` is the local civil time.
    utc_dt = birth_dt - timedelta(hours=tz_offset)
    jd = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )

    # 計算行星位置(Tropical)
    planets_data = {}
    for name, code in PLANETS.items():
        # pyswisseph returns `(positions, flags)` while the actively maintained
        # pysweph fork may append a warning string. Read the first item only.
        raw = swe.calc_ut(jd, code, swe.FLG_SPEED)
        pos = raw[0]
        longitude = pos[0]
        sign_index = int(longitude / 30)
        degree_in_sign = longitude % 30

        planets_data[name] = {
            "sign": SIGNS[sign_index],
            "degrees": round(longitude, 2),
            "degrees_in_sign": round(degree_in_sign, 2),
            "retrograde": pos[3] < 0,
            "speed_degrees_per_day": round(pos[3], 4)
        }

    # 計算 ASC / MC(需要精確 LST)
    # 用 Placidus house system
    try:
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b'P')  # P = Placidus
        # pyswisseph returns 12 zero-indexed cusps; pysweph may return a
        # 13-element sequence with an unused element at index 0.
        if len(cusps) == 13:
            cusps = cusps[1:]
        asc = ascmc[0]  # ASC
        mc = ascmc[1]   # MC
    except Exception as e:
        asc, mc = 0, 0

    asc_sign = SIGNS[int(asc / 30)] if asc else None
    asc_degree = asc % 30 if asc else None
    mc_sign = SIGNS[int(mc / 30)] if mc else None
    mc_degree = mc % 30 if mc else None

    # 計算相位
    planet_longitudes = {name: data["degrees"] for name, data in planets_data.items()}
    aspects = calculate_aspects(planet_longitudes)
    # Sprint 1.10: 額外 Minor aspects
    minor_aspects = calculate_minor_aspects(planet_longitudes)

    # v3.0.5:計算 Arabic Parts(中點公式)
    arabic_parts = _calculate_arabic_parts(asc, planets_data)

    def house_of(longitude: float) -> int:
        longitude %= 360
        for index in range(12):
            start = cusps[index] % 360
            end = cusps[(index + 1) % 12] % 360
            if start < end and start <= longitude < end:
                return index + 1
            if start >= end and (longitude >= start or longitude < end):
                return index + 1
        return 12

    for planet in planets_data.values():
        planet["house"] = house_of(planet["degrees"])

    return {
        "house_system": "Placidus",
        "zodiac": "Tropical",
        "angles": {
            "ASC": {"sign": asc_sign, "degrees": round(asc, 2) if asc else None},
            "MC": {"sign": mc_sign, "degrees": round(mc, 2) if mc else None}
        },
        "houses": [
            {"house": index + 1, "cusp_longitude": round(cusp % 360, 4)}
            for index, cusp in enumerate(cusps)
        ],
        "planets": planets_data,
        "aspects": aspects,
        "aspects_count": {"major": len(aspects), "minor": len(minor_aspects)},
        "minor_aspects_v3_1_0": minor_aspects,
        "arabic_parts": arabic_parts
    }


def _calculate_arabic_parts(asc: float, planets_data: Dict[str, Any]) -> Dict[str, Any]:
    """計算 Arabic Parts(中點公式)

    常見 Arabic Parts:
    - Lot of Fortune (Part of Fortune): ASC + Moon - Sun(日盤用此;夜盤改為 ASC + Sun - Moon)
    - Lot of Spirit (Part of Spirit): ASC + Sun - Moon
    - Lot of Eros: ASC + Venus - Mars
    - Lot of Marriage (女性): ASC + Venus - Saturn
    - Lot of Exaltation: ASC + Sun - (5° Aries = 0°)
    """
    if asc is None:
        return {"error": "ASC not available"}

    sun_lon = planets_data.get("Sun", {}).get("degrees", 0)
    moon_lon = planets_data.get("Moon", {}).get("degrees", 0)
    venus_lon = planets_data.get("Venus", {}).get("degrees", 0)
    mars_lon = planets_data.get("Mars", {}).get("degrees", 0)
    saturn_lon = planets_data.get("Saturn", {}).get("degrees", 0)

    # Sun in houses 7–12 is above the local horizon in the house model.
    sun_house = planets_data.get("Sun", {}).get("house")
    is_day_chart = isinstance(sun_house, int) and 7 <= sun_house <= 12
    if is_day_chart:
        pof = (asc + moon_lon - sun_lon) % 360
    else:
        pof = (asc + sun_lon - moon_lon) % 360

    pos = (asc + sun_lon - moon_lon) % 360
    eros = (asc + venus_lon - mars_lon) % 360
    marriage = (asc + venus_lon - saturn_lon) % 360

    def _lot_to_sign_degree(lon):
        sign_index = int(lon / 30)
        degree = lon % 30
        return {
            "sign": SIGNS[sign_index],
            "degrees": round(lon, 2),
            "degrees_in_sign": round(degree, 2)
        }

    return {
        "lot_of_fortune": {
            "longitude": round(pof, 2),
            **(_lot_to_sign_degree(pof)),
            "chart_type": "day" if is_day_chart else "night",
            "interpretation": "代表物質、身體、健康、好運的焦點"
        },
        "lot_of_spirit": {
            "longitude": round(pos, 2),
            **(_lot_to_sign_degree(pos)),
            "interpretation": "代表意志、精神、使命"
        },
        "lot_of_eros": {
            "longitude": round(eros, 2),
            **(_lot_to_sign_degree(eros)),
            "interpretation": "代表激情、慾望、創造性能量"
        },
        "lot_of_marriage": {
            "longitude": round(marriage, 2),
            **(_lot_to_sign_degree(marriage)),
            "interpretation": "代表伴侶關係、承諾"
        },
        "note": "阿拉伯點(Arabic Parts)起源於希臘化占星,中世紀阿拉伯學者系統化,公式為兩個行星中點 ± 第三點"
    }
