"""
Bazi 完整查詢模組(v3.0.8)
從 bazi skill references/wuxing-tables.md + shichen-table.md 抄

提供:
- 十二長生查詢
- 地支藏干(本氣/中氣/餘氣)
- 十神推導
- 天干五合
- 地支六沖 / 三合 / 三會 / 六合 / 相刑 / 相害
- 時辰對照 + 早子時/夜子時 + 五鼠遁元
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

_DATA_PATH = Path(__file__).parent / "data" / "bazi_tables.json"


def _load() -> Dict[str, Any]:
    if not _DATA_PATH.exists():
        return {}
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_TABLES = _load()


# === 1. 十二長生 ===

def get_life_stage(day_stem: str, branch: str) -> Optional[str]:
    """查詢日干在某地支的十二長生狀態

    Args:
        day_stem: 日干(甲乙丙丁戊己庚辛壬癸)
        branch: 地支(子丑寅卯辰巳午未申酉戌亥)

    Returns:
        長生狀態(長生/沐浴/冠帶/臨官/帝旺/衰/病/死/墓/絕/胎/養)或 None
    """
    table = _TABLES.get("_twelve_life_stages", {})
    stages = table.get(day_stem, {})
    for stage, b in stages.items():
        if b == branch:
            return stage
    return None


# === 2. 地支藏干 ===

def get_hidden_stems(branch: str) -> List[str]:
    """查詢地支藏干(從本氣到餘氣)"""
    return _TABLES.get("_hidden_stems", {}).get(branch, [])


def get_hidden_stems_with_weights(branch: str) -> List[Dict[str, Any]]:
    """查詢地支藏干(含權重)

    Returns:
        [{"stem": "己", "type": "本氣", "weight": 0.6}, ...]
    """
    raw = get_hidden_stems(branch)
    weights = _TABLES.get("_hidden_stem_weights", {})
    types = ["本氣", "中氣", "餘氣"]
    result = []
    for i, stem in enumerate(raw):
        result.append({
            "stem": stem,
            "type": types[i] if i < len(types) else "餘氣",
            "weight": weights.get(types[i] if i < len(types) else "餘氣", 0.1)
        })
    return result


# === 3. 十神推導 ===

# 五行生剋
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
GENERATED_BY = {v: k for k, v in GENERATES.items()}
CONTROLLED_BY = {v: k for k, v in CONTROLS.items()}


def _yin_yang(stem: str) -> str:
    return _TABLES.get("_ten_stems", {}).get(stem, {}).get("yin_yang", "")


def _wuxing_of(stem: str) -> str:
    return _TABLES.get("_ten_stems", {}).get(stem, {}).get("wuxing", "")


def get_ten_god(day_stem: str, other_stem: str) -> str:
    """從日干推導其他天干的十神

    Args:
        day_stem: 日主(我)
        other_stem: 另一個天干

    Returns:
        十神名稱(比肩/劫財/食神/傷官/偏財/正財/偏官/正官/偏印/正印)
    """
    if day_stem == other_stem:
        return "比肩"

    my_elem = _wuxing_of(day_stem)
    other_elem = _wuxing_of(other_stem)
    if not my_elem or not other_elem:
        return ""

    my_yy = _yin_yang(day_stem)
    other_yy = _yin_yang(other_stem)
    same_yin_yang = (my_yy == other_yy)

    # 判斷關係
    if other_elem == GENERATED_BY.get(my_elem):
        # 生我 → 印(陰陽同=偏印梟神,陰陽異=正印)
        return "偏印(梟神)" if same_yin_yang else "正印"
    elif other_elem == GENERATES.get(my_elem):
        # 我生 → 子(陰陽同=食神,陰陽異=傷官)
        return "食神" if same_yin_yang else "傷官"
    elif other_elem == CONTROLLED_BY.get(my_elem):
        # 剋我 → 官(陰陽同=偏官七殺,陰陽異=正官)
        return "偏官(七殺)" if same_yin_yang else "正官"
    elif other_elem == CONTROLS.get(my_elem):
        # 我剋 → 財(陰陽同=偏財,陰陽異=正財)
        return "偏財" if same_yin_yang else "正財"
    elif other_elem == my_elem:
        # 同我 → 劫財(陰陽異)
        return "比肩" if same_yin_yang else "劫財"
    return ""


# === 4. 天干五合 ===

def get_stem_combination(s1: str, s2: str) -> Optional[Dict[str, Any]]:
    """查詢天干五合

    Returns:
        {"合化": "土", "條件": "..."} 或 None(不合)
    """
    pair1 = s1 + s2
    pair2 = s2 + s1
    table = _TABLES.get("_stem_combinations", {})
    for key in [pair1, pair2]:
        if key in table:
            return table[key]
    return None


# === 5. 地支關係 ===

def get_branch_clash(b1: str, b2: str) -> bool:
    """是否地支六沖"""
    if b1 == b2:
        return False
    clashes = _TABLES.get("_branch_clashes", [])
    for pair in clashes:
        if (b1 == pair[0] and b2 == pair[1]) or (b1 == pair[1] and b2 == pair[0]):
            return True
    return False


def get_branch_triple_combination(branches: List[str]) -> Optional[str]:
    """查詢三合局(水/木/火/金)

    Args:
        branches: 3 個地支列表

    Returns:
        五行元素('水'/'木'/'火'/'金')或 None
    """
    table = _TABLES.get("_branch_triple_combinations", {})
    for elem, group in table.items():
        if all(b in group for b in branches):
            return elem
    return None


def get_branch_half_combination(branches: List[str]) -> Optional[Tuple[str, int]]:
    """查詢半合局(2 字成局,力量減半)

    Returns:
        (元素, 缺字數) — 例:('水', 1) 表示申子半合,缺辰
    """
    table = _TABLES.get("_branch_triple_combinations", {})
    for elem, group in table.items():
        if all(b in group for b in branches):
            return (elem, 3 - len(branches))
    return None


def get_branch_direction_combination(branches: List[str]) -> Optional[str]:
    """查詢三會局(方局)"""
    table = _TABLES.get("_branch_direction_combinations", {})
    for elem, group in table.items():
        if all(b in group for b in branches):
            return elem
    return None


def get_branch_six_combination(b1: str, b2: str) -> Optional[str]:
    """查詢六合"""
    if b1 == b2:
        return None
    table = _TABLES.get("_branch_six_combinations", {})
    for pair, elem in table.items():
        if (b1 == pair[0] and b2 == pair[1]) or (b1 == pair[1] and b2 == pair[0]):
            return elem
    return None


def get_branch_punishment(branches: List[str]) -> Optional[str]:
    """查詢相刑(三刑或自刑)"""
    table = _TABLES.get("_branch_punishments", {})
    for key, value in table.items():
        if key.startswith("_"):
            continue
        if all(b in key for b in branches) and all(c in branches for c in key):
            return value
    return None


def get_branch_harm(b1: str, b2: str) -> bool:
    """是否相害(相穿)"""
    if b1 == b2:
        return False
    harms = _TABLES.get("_branch_harms", [])
    for pair in harms:
        if (b1 == pair[0] and b2 == pair[1]) or (b1 == pair[1] and b2 == pair[0]):
            return True
    return False


def analyze_branch_relations(branches: List[str]) -> Dict[str, Any]:
    """完整分析地支關係

    Args:
        branches: 4 個地支(年/月/日/時柱)

    Returns:
        {
          "six_clashes": [...],
          "triple_combinations": [...],
          "direction_combinations": [...],
          "six_combinations": [...],
          "punishments": [...],
          "harms": [...]
        }
    """
    clashes = []
    for i in range(len(branches)):
        for j in range(i+1, len(branches)):
            if get_branch_clash(branches[i], branches[j]):
                clashes.append([branches[i], branches[j]])

    triple = get_branch_triple_combination(branches)
    direction = get_branch_direction_combination(branches)
    six = []
    for i in range(len(branches)):
        for j in range(i+1, len(branches)):
            elem = get_branch_six_combination(branches[i], branches[j])
            if elem:
                six.append([branches[i], branches[j], elem])

    punish = get_branch_punishment(branches)
    harms = []
    for i in range(len(branches)):
        for j in range(i+1, len(branches)):
            if get_branch_harm(branches[i], branches[j]):
                harms.append([branches[i], branches[j]])

    return {
        "six_clashes": clashes,
        "triple_combinations": triple,
        "direction_combinations": direction,
        "six_combinations": six,
        "punishments": punish,
        "harms": harms,
        "data_source": "bazi skill references/wuxing-tables.md"
    }


# === 6. 時辰判斷 ===

def get_shichen_from_hour(hour: int, minute: int = 0) -> Tuple[str, bool]:
    """從小時判斷時辰地支

    Returns:
        (地支, 是否夜子時)
        是否夜子時=True 表示 23:00 後,日柱需要算次日
    """
    time_decimal = hour + minute / 60.0
    if 23.0 <= time_decimal or time_decimal < 1.0:
        return ("子", time_decimal >= 23.0)  # 子時
    elif 1.0 <= time_decimal < 3.0:
        return ("丑", False)
    elif 3.0 <= time_decimal < 5.0:
        return ("寅", False)
    elif 5.0 <= time_decimal < 7.0:
        return ("卯", False)
    elif 7.0 <= time_decimal < 9.0:
        return ("辰", False)
    elif 9.0 <= time_decimal < 11.0:
        return ("巳", False)
    elif 11.0 <= time_decimal < 13.0:
        return ("午", False)
    elif 13.0 <= time_decimal < 15.0:
        return ("未", False)
    elif 15.0 <= time_decimal < 17.0:
        return ("申", False)
    elif 17.0 <= time_decimal < 19.0:
        return ("酉", False)
    elif 19.0 <= time_decimal < 21.0:
        return ("戌", False)
    elif 21.0 <= time_decimal < 23.0:
        return ("亥", False)
    return ("", False)


def get_hour_stem(day_stem: str, hour: int, minute: int = 0) -> Optional[str]:
    """從日干 + 時辰小時 → 時辰天干(五鼠遁元)"""
    branch, is_ye_zi = get_shichen_from_hour(hour, minute)
    if not branch:
        return None
    # 找到日干對應的子時天干表
    wuhudun = _TABLES.get("_wuhudun_starting_stems", {})
    day_stem_key = None
    for key in wuhudun:
        if day_stem in key.split("/"):
            day_stem_key = key
            break
    if not day_stem_key:
        return None
    return wuhudun[day_stem_key].get(branch)


def get_shichen_info(branch: str) -> Dict[str, Any]:
    """查詢時辰詳細資料"""
    return _TABLES.get("_shichen_table", {}).get(branch, {})


# === 7. 統計 ===

def _count_dict_keys(d: Any, exclude_meta: bool = True) -> int:
    """計算「dict 本身」的「非 _note metadata」鍵數(不遞迴,只算當層)"""
    if not isinstance(d, dict):
        return 0
    if not exclude_meta:
        return len(d)
    return sum(1 for k in d if not k.startswith("_"))


def _count_list_items(d: Any) -> int:
    """計算 list 的總元素數(遞迴展開所有 list 層,跳過 dict)"""
    if isinstance(d, list):
        return len(d)
    if isinstance(d, dict):
        # 跳過 _note metadata
        return sum(_count_list_items(v) for k, v in d.items() if not k.startswith("_"))
    return 0


def get_stats() -> Dict[str, Any]:
    """回報當前表覆蓋的數據規模"""
    stages_dict = _TABLES.get("_twelve_life_stages", {})
    hidden_dict = _TABLES.get("_hidden_stems", {})

    return {
        "天干": _count_dict_keys(_TABLES.get("_ten_stems", {})),
        "地支": _count_dict_keys(_TABLES.get("_twelve_branches", {})),
        "十二長生表(10干×12狀態=120)": _count_dict_keys(stages_dict) * 12,
        "地支藏干(12支共 28 字)": _count_list_items(hidden_dict),
        "天干五合(5 對)": _count_dict_keys(_TABLES.get("_stem_combinations", {})),
        "地支六沖(6 對)": len(_TABLES.get("_branch_clashes", [])),
        "三合局(4 組)": _count_dict_keys(_TABLES.get("_branch_triple_combinations", {})),
        "三會局(4 組)": _count_dict_keys(_TABLES.get("_branch_direction_combinations", {})),
        "六合(6 對)": _count_dict_keys(_TABLES.get("_branch_six_combinations", {})),
        "相刑(4 組含自刑)": 4,
        "相害(6 對)": len(_TABLES.get("_branch_harms", [])),
        "五鼠遁元(5 組)": _count_dict_keys(_TABLES.get("_wuhudun_starting_stems", {})),
        "時辰(12 個)": _count_dict_keys(_TABLES.get("_shichen_table", {}))
    }


# === 自我測試 ===

if __name__ == "__main__":
    print("=== Bazi Tables Stats ===")
    stats = get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print()
    print("=== Sample Tests ===")
    # 1. 十二長生
    print(f"甲木在卯 = {get_life_stage('甲', '卯')}")  # 帝旺
    print(f"戊土在子 = {get_life_stage('戊', '子')}")  # 胎

    # 2. 藏干
    print(f"寅藏干 = {get_hidden_stems('寅')}")  # ['甲', '丙', '戊']
    print(f"寅藏干(含權重) = {get_hidden_stems_with_weights('寅')}")

    # 3. 十神
    print(f"日主甲,乙 = {get_ten_god('甲', '乙')}")  # 劫財(陰陽異)
    print(f"日主甲,丙 = {get_ten_god('甲', '丙')}")  # 食神(陰陽同)
    print(f"日主甲,辛 = {get_ten_god('甲', '辛')}")  # 正官(陰陽異,金剋木)
    print(f"日主甲,癸 = {get_ten_god('甲', '癸')}")  # 正印(陰陽異,水生木)

    # 4. 天干五合
    print(f"甲己合 = {get_stem_combination('甲', '己')}")  # 合化土
    print(f"甲乙合 = {get_stem_combination('甲', '乙')}")  # None

    # 5. 地支關係
    relations = analyze_branch_relations(['子', '午', '寅', '申'])
    print(f"子午寅申 關係 = {relations}")

    # 6. 時辰
    print(f"06:00 時辰 = {get_shichen_from_hour(6, 0)}")  # 卯
    print(f"23:30 時辰 = {get_shichen_from_hour(23, 30)}")  # 子(夜)
    print(f"日主甲,06:00 = {get_hour_stem('甲', 6, 0)}")  # 丁
