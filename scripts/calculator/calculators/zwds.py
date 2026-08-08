"""Zi Wei Dou Shu calculator backed exclusively by pinned iztro 2.5.8."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json
import subprocess

# Module-level paths(供 calculate_via_node 使用)
_CALC_DIR = Path(__file__).parent
_TOOLS_DIR = _CALC_DIR.parent
_NODE_DIR = _TOOLS_DIR / "node"


def _hour_to_chinese_hour_index(hour: int) -> int:
    """把整點小時(0-23)轉成時辰地支索引(0-12)

    規則(對應 iztro 內部邏輯):
    - 23:00-00:59 → 0 子時(23 點算晚子時,dayDivide='current' 時歸 0)
    - 00:00-00:59 → 0 子時(早子時)
    - 01:00-02:59 → 1 丑時
    - 03:00-04:59 → 2 寅時
    - 05:00-06:59 → 3 卯時
    - 07:00-08:59 → 4 辰時
    - 09:00-10:59 → 5 巳時
    - 11:00-12:59 → 6 午時
    - 13:00-14:59 → 7 未時
    - 15:00-16:59 → 8 申時
    - 17:00-18:59 → 9 酉時
    - 19:00-20:59 → 10 戌時
    - 21:00-22:59 → 11 亥時
    """
    if hour == 23:
        return 12  # 晚子時
    return (hour + 1) // 2  # 0→0, 1→1, 2→1, 3→2, 4→2, 5→3, ...


def calculate_via_node(
    birth_dt: datetime,
    lat: float,
    lon: float,
    tz_offset: float,
    gender: str = "X",
) -> Dict[str, Any]:
    """透過 Node.js 呼叫 iztro (v2.5.8 API)"""
    # iztro 2.5.8 exports: { data, star, util, astro }
    # 正確 API: bySolar(solarDate, timeIndex, gender, fixLeap, language)
    #   solarDate: "YYYY-M-D H:m"  含時間
    #   timeIndex: 0-12(時辰地支索引;0=子時、1=丑時、2=寅時、3=卯時...、11=亥時、12=晚子時)
    #   gender: '男' / '女'(中文字符串)
    #   fixLeap: true 處理閏月
    #   language: 'zh-CN' / 'en-US'
    # 注意:經緯度/時區由 date string 隱含(zoSolar 不需要單獨傳,默認以當地時間排盤)
    # ⚠ v3.1.0 修正:之前用 0-23(整點小時)會導致 iztro 把 5 當作巳時,造成命宮地支錯誤
    #    修正為 0-12(時辰地支索引)
    date_str = f"{birth_dt.year}-{birth_dt.month}-{birth_dt.day} {birth_dt.hour}:{birth_dt.minute}"
    time_index = _hour_to_chinese_hour_index(birth_dt.hour)  # 0-12(時辰地支索引)
    gender_str = "男" if str(gender).upper() in {"M", "MALE", "男"} else "女"

    node_script = (
        "const { astro } = require('iztro');\n"
        "const astro_result = astro.bySolar(\n"
        "  __DATE_STR__,\n"
        "  __TIME_IDX__,\n"
        "  '__GENDER__',\n"
        "  true,\n"
        "  'zh-CN'\n"
        ");\n"
        "const result = {\n"
        "  five_elements_class: astro_result.fiveElementsClass,\n"
        "  ming_zhu: astro_result.soul,\n"
        "  shen_zhu: astro_result.body,\n"
        "  earthly_branch_of_soul_palace: astro_result.earthlyBranchOfSoulPalace,\n"
        "  earthly_branch_of_body_palace: astro_result.earthlyBranchOfBodyPalace,\n"
        "  sign: astro_result.sign,\n"
        "  zodiac: astro_result.zodiac,\n"
        "  chinese_date: astro_result.chineseDate,\n"
        "  lunar_date: astro_result.lunarDate,\n"
        "  palaces: {}\n"
        "};\n"
        "astro_result.palaces.forEach((p) => {\n"
        "  result.palaces[p.name] = {\n"
        "    index: p.index,\n"
        "    is_body_palace: p.isBodyPalace,\n"
        "    is_original_palace: p.isOriginalPalace,\n"
        "    heavenly_stem: p.heavenlyStem,\n"
        "    earthly_branch: p.earthlyBranch,\n"
        "    main_star: (p.majorStars && p.majorStars[0]) ? p.majorStars[0].name : null,\n"
        "    all_major_stars: (p.majorStars || []).map(s => s.name),\n"
        "    minor_stars: (p.minorStars || []).map(s => s.name),\n"
        "    shen_sha: (p.adjectiveStars || []).map(s => s.name),\n"
        "    changsheng12: p.changsheng12 || null,\n"
        "    decadal_range: (p.decadal && p.decadal.range) ? p.decadal.range : null,\n"
        "    decadal_stem_branch: (p.decadal && p.decadal.heavenlyStem && p.decadal.earthlyBranch) ? (p.decadal.heavenlyStem + p.decadal.earthlyBranch) : null,\n"
        "    ages: p.ages || []\n"
        "  };\n"
        "});\n"
        "console.log(JSON.stringify(result));\n"
    ).replace("__DATE_STR__", f'"{date_str}"').replace("__TIME_IDX__", str(time_index)).replace("__GENDER__", gender_str)

    try:
        result = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(_NODE_DIR)
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise RuntimeError(f"Node error: {result.stderr}")
    except FileNotFoundError:
        raise RuntimeError("Node.js not installed")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Node.js call timeout")


# v3.1.0 P1-8:從 12 宮動態找身宮所在宮位
# iztro `earthlyBranchOfSoulPalace` 給的是「身宮地支」,真正的身宮 = 12 宮中地支為該值的宮位
# 注意:不能用固定 mapping(命宮是動態的,不是固定在子)
def find_palace_by_earthly_branch(earthly_branch: Optional[str], palaces: Dict[str, Any]) -> Optional[str]:
    """從 12 宮找地支為指定值的宮位名稱

    Args:
        earthly_branch: 目標地支("子"/"丑"/...)
        palaces: iztro 12 宮(用簡體 key 也行,因為只看 earthly_branch)

    Returns:
        對應的宮位名稱(簡體,讓 analyzer adapter 標準化為繁體)/或 None
    """
    if not earthly_branch:
        return None
    for palace_name, palace_data in palaces.items():
        if isinstance(palace_data, dict) and palace_data.get("earthly_branch") == earthly_branch:
            return palace_name
    return None


def calculate(
    birth_dt: datetime,
    lat: float,
    lon: float,
    tz_offset: float,
    gender: str = "X",
) -> Dict[str, Any]:
    """主入口"""
    if str(gender).upper() not in {"M", "F", "MALE", "FEMALE", "男", "女"}:
        raise ValueError("Zi Wei Dou Shu requires M/F gender for direction-dependent calculations")
    data = calculate_via_node(birth_dt, lat, lon, tz_offset, gender)
    body_branch = data.get("earthly_branch_of_body_palace")
    palaces = data.get("palaces", {})
    data["body_palace"] = find_palace_by_earthly_branch(body_branch, palaces)
    if not data["body_palace"]:
        raise RuntimeError("iztro did not return a resolvable body palace")
    return data
