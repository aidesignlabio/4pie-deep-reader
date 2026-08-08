"""
bazi.py - 八字四柱計算

實作:
  - 年柱(以立春切月)
  - 月柱(以節氣切月)
  - 日柱(萬年曆查表)
  - 時柱(以日干起時)
  - 五行 / 十神 / 藏干 / 納音
  - 大運排盤(陽男陰女順行 / 陰男陽女逆行)
  - 流年

節氣和均時差依賴 Swiss Ephemeris；缺少時直接報錯，不使用近似日期。
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import sys
from pathlib import Path

# 載入完整 bazi 參考表(v3.0.8 — 從 skill references/wuxing-tables.md + shichen-table.md 抄)
_TOOLS_DIR = Path(__file__).resolve().parent.parent  # calculators/ → tools/
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
try:
    from bazi_tables import (
        get_life_stage as _get_life_stage,
        get_hidden_stems as _get_hidden_stems,
        get_hidden_stems_with_weights as _get_hidden_stems_with_weights,
        analyze_branch_relations as _analyze_branch_relations,
        get_shichen_from_hour as _get_shichen_from_hour,
        get_hour_stem as _get_hour_stem,
        get_stem_combination as _get_stem_combination,
        get_branch_clash as _get_branch_clash,
        get_branch_triple_combination as _get_branch_triple,
        get_branch_six_combination as _get_branch_six,
        get_branch_punishment as _get_branch_punishment,
        get_branch_harm as _get_branch_harm,
        get_stats as _get_bazi_tables_stats,
    )
    _HAS_BAZI_TABLES = True
except ImportError:
    _HAS_BAZI_TABLES = False

# Sprint 1.2 神煞完整化
try:
    from .bazi_shensha import detect_shensha as _detect_shensha
    _HAS_SHENSHA = True
except (ImportError, ValueError):
    try:
        from bazi_shensha import detect_shensha as _detect_shensha
        _HAS_SHENSHA = True
    except ImportError:
        _HAS_SHENSHA = False

# Sprint 1.3 24 節氣精確計算
try:
    from .bazi_solar_terms import (
        find_jie_qi as _find_jie_qi,
        find_nearest_jie_qi as _find_nearest_jie_qi,
        JIE_TO_MONTH_BRANCH as _JIE_TO_MONTH_BRANCH,
    )
    _HAS_SOLAR_TERMS = True
except (ImportError, ValueError):
    try:
        from bazi_solar_terms import (
            find_jie_qi as _find_jie_qi,
            find_nearest_jie_qi as _find_nearest_jie_qi,
            JIE_TO_MONTH_BRANCH as _JIE_TO_MONTH_BRANCH,
        )
        _HAS_SOLAR_TERMS = True
    except ImportError:
        _HAS_SOLAR_TERMS = False

# 60 甲子表(標準公式:索引 i → (天干 i%10, 地支 i%12))
# 這是從甲子(0,0)開始,每天 +1 天干 +1 地支 的自然循環
JIAZI = [(i % 10, i % 12) for i in range(60)]

# 天干
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
# 地支
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五行對應
STEM_ELEMENTS = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
}
BRANCH_ELEMENTS = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

# 藏干(從 skill references/wuxing-tables.md 抄 — v3.0.8 修正巳火藏干中氣/餘氣)
# 本氣 > 中氣 > 餘氣;權重 0.6 / 0.3 / 0.1
# v3.0.8 修正:巳火正確藏干 = 丙(本氣)、庚(中氣)、戊(餘氣),舊版錯置為戊/庚
HIDDEN_STEMS = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"],
    "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
    "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"]
}

# 月支對應(以節氣切月,中氣不算)
MONTH_BRANCH_BY_TERM = {
    "立春": "寅", "驚蟄": "卯", "清明": "辰", "立夏": "巳",
    "芒種": "午", "小暑": "未", "立秋": "申", "白露": "酉",
    "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑"
}


# === Sprint 1.1 真太陽時校正(v3.1.0) ===
# 標準時(時區時)≠ 真太陽時,經度不同會有差異。
# 公式:真太陽時 = 標準時 + 4 分鐘 × (當地經度 - 標準子午線) + 均時差

def true_solar_time(
    dt: datetime,
    longitude: float,
    standard_meridian: float = 120.0,
    tz_offset: float = 8.0,
) -> Tuple[datetime, float, float]:
    """真太陽時校正

    Args:
        dt: 標準時(時區時間)
        longitude: 出生地經度(東經為正)
        standard_meridian: 標準子午線(中國/港/澳/台/星 = 120;日本 = 135;印度 = 82.5;美國 EST = -75)

    Returns:
        (真太陽時, 經度修正分鐘, 均時差分鐘)
    """
    import swisseph as swe

    # Swiss Ephemeris may differ by a few microseconds between otherwise
    # identical process runs on some platforms.  That precision is neither
    # meaningful for a two-hour Chinese time branch nor suitable for a
    # canonical, hashable chart.  Quantise the published correction and the
    # datetime used by all downstream pillar calculations.
    longitude_minutes = round((longitude - standard_meridian) * 4.0, 6)
    utc_dt = dt - timedelta(hours=tz_offset)
    utc_hours = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_hours)
    equation_of_time_minutes = round(
        float(swe.time_equ(jd_ut)) * 24.0 * 60.0,
        4,
    )
    corrected_raw = dt + timedelta(
        minutes=longitude_minutes + equation_of_time_minutes
    )
    corrected = (corrected_raw + timedelta(microseconds=500_000)).replace(
        microsecond=0
    )
    return corrected, longitude_minutes, equation_of_time_minutes

# 五虎遁年起月(年上起月)
YEAR_STEM_TO_FIRST_MONTH_STEM = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲"
}

# 五鼠遁日起時(日上起時)
DAY_STEM_TO_FIRST_HOUR_STEM = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬"
}

# 日柱計算(萬年曆錨點):1900-01-01 = 甲戌日(第 11 位)
ANCHOR_DATE = datetime(1900, 1, 1)
ANCHOR_JIAZI_INDEX = 10  # 甲戌 = 0-indexed 10


def get_year_pillar(birth_dt: datetime, longitude: float, tz_offset: float) -> Tuple[str, str]:
    """年柱:以立春切年"""
    # 找出生時間之前的立春日
    year = birth_dt.year
    if not _HAS_SOLAR_TERMS:
        raise RuntimeError("precise Bazi solar-term module is unavailable")
    lichun_year = _find_jie_qi(year, longitude, tz_offset)["立春"]
    if birth_dt < lichun_year:
        # 還沒立春,屬於上一年
        year -= 1
    # 年干支:1984 = 甲子年(60 甲子第 1 個)
    year_offset = (year - 1984) % 60
    stem = STEMS[year_offset % 10]
    branch = BRANCHES[year_offset % 12]
    return (stem, branch)


def get_month_pillar(birth_dt: datetime, year_stem: str, longitude: float = 120.0, tz_offset: float = 8.0) -> Tuple[str, str]:
    """月柱:以節氣切月,五虎遁年起月(v3.1.0 用 pyswisseph 精確節氣)"""
    year = birth_dt.year

    if not _HAS_SOLAR_TERMS:
        raise RuntimeError("precise Bazi solar-term module is unavailable")
    nearest_jie_name, nearest_jie_time = _find_nearest_jie_qi(
        birth_dt, longitude, tz_offset
    )
    branch = _JIE_TO_MONTH_BRANCH.get(nearest_jie_name, "")

    if not nearest_jie_name:
        raise RuntimeError("could not determine the precise Bazi month boundary")

    # 五虎遁:由年干起正月
    first_month_stem = YEAR_STEM_TO_FIRST_MONTH_STEM[year_stem]
    first_month_index = STEMS.index(first_month_stem)

    # 月支對應索引
    branch_index = BRANCHES.index(branch)
    # 寅月為正月(索引 2)
    month_offset = (branch_index - BRANCHES.index("寅")) % 12
    month_stem = STEMS[(first_month_index + month_offset) % 10]

    return (month_stem, branch)


def get_day_pillar(birth_dt: datetime) -> Tuple[str, str]:
    """日柱:基於 1900-01-01 = 甲戌日的錨點計算"""
    delta_days = (birth_dt - ANCHOR_DATE).days
    jiazi_index = (ANCHOR_JIAZI_INDEX + delta_days) % 60
    stem, branch = JIAZI[jiazi_index]
    return (STEMS[stem], BRANCHES[branch])


def get_hour_pillar(birth_dt: datetime, day_stem: str) -> Tuple[str, str]:
    """時柱:由日干起時"""
    hour = birth_dt.hour
    # 時辰切換：23:00–00:59 為子時。
    if hour == 23 or hour == 0:
        branch = "子"
    elif 1 <= hour < 3:
        branch = "丑"
    elif 3 <= hour < 5:
        branch = "寅"
    elif 5 <= hour < 7:
        branch = "卯"
    elif 7 <= hour < 9:
        branch = "辰"
    elif 9 <= hour < 11:
        branch = "巳"
    elif 11 <= hour < 13:
        branch = "午"
    elif 13 <= hour < 15:
        branch = "未"
    elif 15 <= hour < 17:
        branch = "申"
    elif 17 <= hour < 19:
        branch = "酉"
    elif 19 <= hour < 21:
        branch = "戌"
    else:  # 21-23
        branch = "亥"

    # 五鼠遁:由日干起子時
    first_hour_stem = DAY_STEM_TO_FIRST_HOUR_STEM[day_stem]
    first_hour_index = STEMS.index(first_hour_stem)

    # 時支對應索引
    branch_index = BRANCHES.index(branch)
    # 子時為首(索引 0)
    hour_offset = (branch_index - BRANCHES.index("子")) % 12
    hour_stem = STEMS[(first_hour_index + hour_offset) % 10]

    return (hour_stem, branch)


def ten_god(day_master: str, target_stem: str) -> str:
    """算 target_stem 對 day_master 的十神"""
    if target_stem == day_master:
        return "比肩"

    dm_element = STEM_ELEMENTS[day_master]
    target_element = STEM_ELEMENTS[target_stem]

    # 同我者:比肩 / 劫財
    if target_element == dm_element:
        if STEMS.index(target_stem) % 2 != STEMS.index(day_master) % 2:
            return "劫財"
        return "比肩"

    # 我生者:食神 / 傷官
    produces = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    if produces[dm_element] == target_element:
        if STEMS.index(target_stem) % 2 != STEMS.index(day_master) % 2:
            return "傷官"
        return "食神"

    # 我克者:偏財 / 正財
    controls = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
    if controls[dm_element] == target_element:
        if STEMS.index(target_stem) % 2 != STEMS.index(day_master) % 2:
            return "偏財"
        return "正財"

    # 克我者:七殺 / 正官
    is_controlled_by = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
    if is_controlled_by[dm_element] == target_element:
        if STEMS.index(target_stem) % 2 != STEMS.index(day_master) % 2:
            return "七殺"
        return "正官"

    # 生我者:偏印 / 正印
    produces_by = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}
    if produces_by[dm_element] == target_element:
        if STEMS.index(target_stem) % 2 != STEMS.index(day_master) % 2:
            return "偏印"
        return "正印"

    return "未知"


def calculate_starting_age(
    birth_dt: datetime,
    is_forward: bool,
    longitude: float,
    tz_offset: float = 8.0,
) -> int:
    """起運歲數計算(基於 skill references/dayun-rules.md)

    順排:從出生日數到下一個節,總天數 ÷ 3
    逆排:從出生日逆數到上一個節,總天數 ÷ 3
    """
    if not _HAS_SOLAR_TERMS:
        raise RuntimeError("precise Bazi solar-term module is unavailable")

    terms = []
    for candidate_year in (birth_dt.year - 1, birth_dt.year, birth_dt.year + 1):
        terms.extend(_find_jie_qi(candidate_year, longitude, tz_offset).values())

    if is_forward:
        boundary = min(instant for instant in terms if instant > birth_dt)
        interval = boundary - birth_dt
    else:
        boundary = max(instant for instant in terms if instant < birth_dt)
        interval = birth_dt - boundary

    # 傳統換算：三天為一歲。對輸出年齡取最接近整數。
    interval_days = interval.total_seconds() / 86400.0
    return max(0, round(interval_days / 3.0))


def calculate_luck_pillars(
    year_stem: str,
    gender: str,
    birth_dt: datetime,
    year_branch: str,
    month_stem: str = "",
    month_branch: str = "",
    longitude: float = 120.0,
    tz_offset: float = 8.0,
) -> List[Dict[str, Any]]:
    """大運排盤(標準版 — 從 skill references/dayun-rules.md 抄)

    算法:
    1. 陽年男 / 陰年女 → 順排
    2. 陰年男 / 陽年女 → 逆排
    3. 從月柱基準,順/逆推排列 8 步大運(每步 10 年)
    4. 計算起運歲數
    """
    pillars = []
    is_yang_year = STEMS.index(year_stem) % 2 == 0
    is_male = gender.upper() in ["M", "男", "MALE"]
    # 順排 = 陽年男 + 陰年女
    is_forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)
    direction = 1 if is_forward else -1

    # 起運歲數
    starting_age = calculate_starting_age(birth_dt, is_forward, longitude, tz_offset)

    # 從月柱基準推大運(需要月柱的 stem-branch)
    if not month_stem or not month_branch:
        raise ValueError("month pillar is required for luck-pillar calculation")

    # 月柱基準 → 大運
    month_stem_idx = STEMS.index(month_stem)
    month_branch_idx = BRANCHES.index(month_branch)
    for i in range(1, 9):
        # 每步大運:天干地支各 +1(順)或 -1(逆)
        stem_idx = (month_stem_idx + direction * i) % 10
        branch_idx = (month_branch_idx + direction * i) % 12
        age = starting_age + (i - 1) * 10
        pillars.append({
            "start_age": age,
            "end_age": age + 9,
            "stem": STEMS[stem_idx],
            "branch": BRANCHES[branch_idx],
            "ten_god": "calculated from month pillar"
        })

    # 加交運前的小運(用月柱)
    pillars.insert(0, {
        "start_age": 0,
        "end_age": starting_age - 1,
        "stem": month_stem,
        "branch": month_branch,
        "ten_god": "小運(交運前用月柱)"
    })

    return pillars


def calculate(
    birth_dt: datetime,
    lat: float,
    lon: float,
    tz_offset: float,
    gender: str = "X",
) -> Dict[str, Any]:
    """主入口:計算八字四柱(v3.1.0 含真太陽時校正)"""
    if str(gender).upper() not in {"M", "F", "MALE", "FEMALE", "男", "女"}:
        raise ValueError("八字大運順逆排需要 M/F 性別")
    # Sprint 1.1: 真太陽時校正
    # tz_offset 是時區小時數,推算 standard_meridian
    standard_meridian = tz_offset * 15.0  # UTC+8 = 東 120°
    true_solar_dt, longitude_minutes, equation_of_time_minutes = true_solar_time(
        birth_dt, lon, standard_meridian, tz_offset
    )
    solar_correction_minutes = longitude_minutes + equation_of_time_minutes

    # 用真太陽時計算四柱
    # 年、月界線以節氣的當地民用時間比較；日、時使用真太陽時。
    year_stem, year_branch = get_year_pillar(birth_dt, lon, tz_offset)
    month_stem, month_branch = get_month_pillar(birth_dt, year_stem, lon, tz_offset)
    day_stem, day_branch = get_day_pillar(true_solar_dt)
    hour_stem, hour_branch = get_hour_pillar(true_solar_dt, day_stem)

    # 四柱天干對日主的十神。
    four_pillars = {
        "year": {
            "stem": year_stem, "branch": year_branch,
            "hidden_stems": HIDDEN_STEMS[year_branch],
            "ten_god": ten_god(day_stem, year_stem)
        },
        "month": {
            "stem": month_stem, "branch": month_branch,
            "hidden_stems": HIDDEN_STEMS[month_branch],
            "ten_god": ten_god(day_stem, month_stem)
        },
        "day": {
            "stem": day_stem, "branch": day_branch,
            "hidden_stems": HIDDEN_STEMS[day_branch],
            "ten_god": "日主"
        },
        "hour": {
            "stem": hour_stem, "branch": hour_branch,
            "hidden_stems": HIDDEN_STEMS[hour_branch],
            "ten_god": ten_god(day_stem, hour_stem)
        }
    }

    four_branches = [year_branch, month_branch, day_branch, hour_branch]

    # 大運(標準算法:從月柱基準順/逆排)
    luck_pillars = calculate_luck_pillars(
        year_stem, gender, birth_dt, year_branch,
        month_stem=month_stem, month_branch=month_branch,
        longitude=lon, tz_offset=tz_offset
    )

    dm_element = STEM_ELEMENTS[day_stem]

    # === v3.0.8 — 完整規則引擎輸出(從 bazi_tables 整合) ===
    enhanced = _enhance_with_tables(
        day_stem=day_stem,
        four_pillars=four_pillars,
        four_branches=four_branches,
    )

    return {
        "four_pillars": four_pillars,
        "true_solar_time": {
            "input_birth_dt": birth_dt.isoformat(),
            "input_longitude": lon,
            "standard_meridian": standard_meridian,
            "longitude_correction_minutes": longitude_minutes,
            "equation_of_time_minutes": equation_of_time_minutes,
            "solar_correction_minutes": solar_correction_minutes,
            "true_solar_dt": true_solar_dt.isoformat(),
            "note": "真太陽時 = 經度修正 + Swiss Ephemeris 均時差"
        },
        "shensha_v3_1_0": _detect_shensha(day_stem, four_branches, month_branch) if _HAS_SHENSHA else {"_warning": "bazi_shensha module not loaded"},
        "month_lord": HIDDEN_STEMS[month_branch][0],
        "day_master": day_stem,
        "day_master_element": dm_element,
        "luck_pillars": luck_pillars,
        "enhanced_v3_0_8": enhanced
    }


def _enhance_with_tables(
    day_stem: str,
    four_pillars: Dict[str, Any],
    four_branches: List[str],
) -> Dict[str, Any]:
    """v3.0.8 增強輸出 — 從 bazi_tables 整合十二長生 + 地支關係 + 五鼠遁元 + 十神標準命名

    Returns:
        {
          "twelve_life_stages": {"year": ..., "month": ..., "day": ..., "hour": ...},
          "branch_relations": {six_clashes, triple_combinations, six_combinations, punishments, harms},
          "hidden_stems_with_weights": {year, month, day, hour},
          "stem_combinations": [{"stems": ["甲","己"], "element": "土"}, ...],
          "shichen_full_table": {所有 12 時辰的天干}
        }
    """
    if not _HAS_BAZI_TABLES:
        return {"_warning": "bazi_tables module not loaded", "_version": "v3.0.8"}

    # 1. 十二長生(每柱地支對日干)
    life_stages = {}
    for pillar, branch in [
        ("year", four_pillars["year"]["branch"]),
        ("month", four_pillars["month"]["branch"]),
        ("day", four_pillars["day"]["branch"]),
        ("hour", four_pillars["hour"]["branch"]),
    ]:
        life_stages[pillar] = {
            "branch": branch,
            "stage": _get_life_stage(day_stem, branch) or "未知"
        }

    # 2. 地支關係完整分析
    branch_relations = _analyze_branch_relations(four_branches)

    # 3. 藏干(含權重)— 用 bazi_tables 標準版
    hidden_with_weights = {}
    for pillar, branch in [
        ("year", four_pillars["year"]["branch"]),
        ("month", four_pillars["month"]["branch"]),
        ("day", four_pillars["day"]["branch"]),
        ("hour", four_pillars["hour"]["branch"]),
    ]:
        hidden_with_weights[pillar] = {
            "branch": branch,
            "stems": _get_hidden_stems_with_weights(branch)
        }

    # 4. 天干五合(檢查原局四柱是否有合)
    stem_combinations = []
    stems_in_chart = [
        four_pillars["year"]["stem"],
        four_pillars["month"]["stem"],
        four_pillars["day"]["stem"],
        four_pillars["hour"]["stem"],
    ]
    seen_pairs = set()
    for i in range(len(stems_in_chart)):
        for j in range(i+1, len(stems_in_chart)):
            pair_key = tuple(sorted([stems_in_chart[i], stems_in_chart[j]]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            combo = _get_stem_combination(stems_in_chart[i], stems_in_chart[j])
            if combo:
                stem_combinations.append({
                    "stems": [stems_in_chart[i], stems_in_chart[j]],
                    "element": combo["合化"],
                    "conditions": combo["條件"]
                })

    # 5. 五鼠遁元(日主全 12 時辰天干)
    day_stem_key = None
    if day_stem in ["甲", "己"]:
        day_stem_key = "甲/己"
    elif day_stem in ["乙", "庚"]:
        day_stem_key = "乙/庚"
    elif day_stem in ["丙", "辛"]:
        day_stem_key = "丙/辛"
    elif day_stem in ["丁", "壬"]:
        day_stem_key = "丁/壬"
    elif day_stem in ["戊", "癸"]:
        day_stem_key = "戊/癸"

    shichen_full_table = {}
    if day_stem_key:
        from bazi_tables import _TABLES
        hour_table = _TABLES.get("_wuhudun_starting_stems", {}).get(day_stem_key, {})
        shichen_full_table = {
            "day_stem": day_stem,
            "day_stem_key": day_stem_key,
            "hour_stems": hour_table
        }

    return {
        "_version": "v3.0.8",
        "_source": "bazi skill references/wuxing-tables.md + shichen-table.md",
        "twelve_life_stages": life_stages,
        "branch_relations": branch_relations,
        "hidden_stems_with_weights": hidden_with_weights,
        "stem_combinations": stem_combinations,
        "shichen_full_table": shichen_full_table,
        "tables_stats": _get_bazi_tables_stats()
    }


if __name__ == "__main__":
    import sys
    dt = datetime(2002, 3, 12, 5, 52)
    if len(sys.argv) > 1:
        dt = datetime.strptime(sys.argv[1], "%Y-%m-%d %H:%M")
    result = calculate(dt, 22.302, 114.177, 8.0)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
