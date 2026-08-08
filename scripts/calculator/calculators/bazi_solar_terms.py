"""
bazi_solar_terms.py — 24 節氣精確計算(v3.1.0)

原本用 ±1 天近似日期,改成用 pyswisseph 計算太陽黃經到 0°/15°/30°...
精確到分鐘,大幅提升月柱/大運起運時間準確度

24 節氣 = 太陽黃經每 15° 一個,從 0°(春分)開始
但命理學以「節」切月(不用中氣):
- 立春(315°) 寅月
- 驚蟄(345°) 卯月
- 清明(15°) 辰月
- 立夏(45°) 巳月
- 芒種(75°) 午月
- 小暑(105°) 未月
- 立秋(135°) 申月
- 白露(165°) 酉月
- 寒露(195°) 戌月
- 立冬(225°) 亥月
- 大雪(255°) 子月
- 小寒(285°) 丑月

注意:太陽黃經從春分(0°)開始,立春是 315°(黃道帶從冬至開始算)
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple


def _try_swisseph():
    """嘗試載入 pyswisseph"""
    try:
        import swisseph as swe
        return swe
    except ImportError:
        return None


# 12 節(不用中氣)
JIE_LONGITUDES = {
    "立春": 315.0, "驚蟄": 345.0, "清明": 15.0, "立夏": 45.0,
    "芒種": 75.0, "小暑": 105.0, "立秋": 135.0, "白露": 165.0,
    "寒露": 195.0, "立冬": 225.0, "大雪": 255.0, "小寒": 285.0,
}

JIE_TO_MONTH_BRANCH = {
    "立春": "寅", "驚蟄": "卯", "清明": "辰", "立夏": "巳",
    "芒種": "午", "小暑": "未", "立秋": "申", "白露": "酉",
    "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑",
}


def find_jie_qi(year: int, longitude: float, tz_offset: float = 8.0) -> Dict[str, datetime]:
    """找該年所有 12 節的精確時間

    Args:
        year: 西元年
        longitude: 出生地經度(用於真太陽時校正)

    Returns:
        {
          "立春": datetime(2002, 2, 4, 13, 25),
          "驚蟄": datetime(2002, 3, 6, 1, 15),
          ...
        }
    """
    swe = _try_swisseph()
    if swe is None:
        raise RuntimeError(
            "swisseph is required for precise Bazi solar terms; "
            "the approximate-date fallback is disabled"
        )

    swe.set_ephe_path()  # 使用內建 ephemeris
    result = {}

    # 24 節氣跨越兩個年(立春在前年,小寒在本年)
    # 所以要算 [year-1, year] 兩個年的節氣
    for jie_name, target_longitude in JIE_LONGITUDES.items():
        # 找最近的節氣時間
        # 太陽黃經每年增加 ~360°,所以節氣時間在固定月份附近
        # 立春通常在 2/4 附近,但有 ±1-2 天變動
        # 用二分搜尋找到精確時間

        # 粗估開始時間
        approx_month_day = {
            "立春": (2, 4), "驚蟄": (3, 5), "清明": (4, 4), "立夏": (5, 5),
            "芒種": (6, 5), "小暑": (7, 7), "立秋": (8, 7), "白露": (9, 7),
            "寒露": (10, 8), "立冬": (11, 7), "大雪": (12, 7), "小寒": (1, 5),
        }
        m, d = approx_month_day[jie_name]
        approx_year = year

        # 二分搜尋:在 ±15 天內找精確時間
        start = datetime(approx_year, m, d) - timedelta(days=15)
        end = datetime(approx_year, m, d) + timedelta(days=15)

        # 確保跨年正確
        if start.year < year - 1 or end.year > year + 1:
            # 跨年情況,用更寬範圍
            start = datetime(approx_year, m, d) - timedelta(days=20)
            end = datetime(approx_year, m, d) + timedelta(days=20)

        # Swiss Ephemeris uses UT. Convert the resulting instant to the local
        # civil time used by the birth input before comparing month boundaries.
        result[jie_name] = (
            _find_exact_jie_qi(swe, start, end, target_longitude)
            + timedelta(hours=tz_offset)
        )

    return result


def _find_exact_jie_qi(swe, start_dt: datetime, end_dt: datetime, target_longitude: float) -> datetime:
    """二分搜尋精確節氣時間"""
    # 太陽黃經從春分(0°)開始算,所以要對 target_longitude 做調整
    # 立春是 315°,但實際上是「太陽到達黃經 315°」
    # 春分 = 0°,立春 = 315°
    # 在 pyswisseph 中,swe.calc_ut 返回黃經(0-360°,從春分開始)
    # 315° = 從春分往後退 45°

    for _ in range(50):  # 最多 50 次迭代
        mid = start_dt + (end_dt - start_dt) / 2

        # 計算 mid 時太陽黃經
        jd = swe.julday(mid.year, mid.month, mid.day, mid.hour + mid.minute / 60.0)
        sun_data = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
        sun_longitude = sun_data[0][0]  # 黃經

        # 計算差異(考慮 360° 循環)
        diff = (target_longitude - sun_longitude) % 360
        if diff > 180:
            diff -= 360

        # 精度 < 0.001°(~36 秒)
        if abs(diff) < 0.001:
            return mid

        # 太陽每天移動 ~1°,所以一天差 diff°
        # 如果太陽黃經還沒到 target,需要向後找
        if diff > 0:
            start_dt = mid
        else:
            end_dt = mid

    return start_dt + (end_dt - start_dt) / 2


def find_nearest_jie_qi(dt: datetime, longitude: float, tz_offset: float = 8.0) -> Tuple[str, datetime]:
    """找離指定時間最近的節氣(向後找最近已過的節)

    Args:
        dt: 時間
        longitude: 出生地經度

    Returns:
        (節氣名, 節氣時間)
    """
    candidates = []
    for candidate_year in (dt.year - 1, dt.year, dt.year + 1):
        candidates.extend(
            find_jie_qi(candidate_year, longitude, tz_offset).items()
        )

    passed = [(name, instant) for name, instant in candidates if instant <= dt]
    if not passed:
        return ("", dt)
    return max(passed, key=lambda item: item[1])


# === 自我測試 ===

if __name__ == "__main__":
    # Synthetic CLI smoke example only.
    import sys
    sys.path.insert(0, '.')
    from datetime import datetime
    birth_dt = datetime(2000, 1, 1, 12, 0)
    longitude = 0.0

    jie_qi = find_jie_qi(2000, longitude)
    print(f"=== 2000 年 12 節精確時間 ===")
    for name, time in jie_qi.items():
        print(f"  {name}: {time.strftime('%Y-%m-%d %H:%M')}")

    # 找最近的節
    nearest, nearest_time = find_nearest_jie_qi(birth_dt, longitude)
    print(f"\n=== 合成測試時間最近的節氣 ===")
    print(f"  {nearest}: {nearest_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"  距出生: {(birth_dt - nearest_time).total_seconds() / 60:.1f} 分鐘")
