"""过运计算模块 - 计算当前行星位置、Sade Sati、双过运"""
import swisseph as swe
from datetime import datetime
import pytz

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

def calc_transit(lagna_sign_idx, moon_sign_idx, tz_str="Asia/Kolkata"):
    """计算当前过运数据"""
    swe.set_sid_mode(swe.SIDM_TRUE_CITRA)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    now = datetime.now(pytz.timezone(tz_str))
    utc = now.astimezone(pytz.utc)
    jd = swe.julday(utc.year, utc.month, utc.day, 
                     utc.hour + utc.minute/60.0)
    
    # 慢行星过运
    slow_planets = {
        'Saturn': (swe.SATURN, '~2.5年/星座'),
        'Jupiter': (swe.JUPITER, '~1年/星座'),
        'Rahu': (swe.MEAN_NODE, '~1.5年/星座')
    }
    
    transit = {}
    for name, (pid, cycle) in slow_planets.items():
        result = swe.calc_ut(jd, pid, flags)
        lon = result[0][0]
        sign_idx = int(lon / 30)
        house = ((sign_idx - lagna_sign_idx) % 12) + 1
        transit[name] = {
            'sign': SIGNS[sign_idx], 'sign_idx': sign_idx,
            'house': house, 'cycle': cycle
        }
    
    # Ketu = Rahu对冲
    rahu_idx = transit['Rahu']['sign_idx']
    ketu_idx = (rahu_idx + 6) % 12
    transit['Ketu'] = {
        'sign': SIGNS[ketu_idx], 'sign_idx': ketu_idx,
        'house': ((ketu_idx - lagna_sign_idx) % 12) + 1,
        'cycle': '自动取Rahu对冲'
    }
    
    # Sade Sati
    saturn_idx = transit['Saturn']['sign_idx']
    relative = (saturn_idx - moon_sign_idx) % 12
    if relative == 11:
        sade_sati = '第一阶段(升起)'
        position = 'Moon前1宫'
    elif relative == 0:
        sade_sati = '第二阶段(顶峰)'
        position = 'Moon本宫'
    elif relative == 1:
        sade_sati = '第三阶段(消退)'
        position = 'Moon后1宫'
    else:
        sade_sati = '未激活'
        position = '非Sade Sati'
    
    sade_sati_data = {
        'moon_sign': SIGNS[moon_sign_idx],
        'saturn_sign': transit['Saturn']['sign'],
        'position': position,
        'status': sade_sati
    }
    
    # 双过运 (Saturn-Jupiter Double Transit)
    saturn_house = transit['Saturn']['house']
    jupiter_house = transit['Jupiter']['house']
    
    # Saturn aspects: 合相(1), 3rd, 7th, 10th
    saturn_covers = set()
    for offset in [0, 2, 6, 9]:
        saturn_covers.add(((saturn_house - 1 + offset) % 12) + 1)
    
    # Jupiter aspects: 合相(1), 5th, 7th, 9th
    jupiter_covers = set()
    for offset in [0, 4, 6, 8]:
        jupiter_covers.add(((jupiter_house - 1 + offset) % 12) + 1)
    
    double_transit = sorted(saturn_covers & jupiter_covers)
    
    return {
        'planets': transit,
        'sade_sati': sade_sati_data,
        'saturn_covers': sorted(saturn_covers),
        'jupiter_covers': sorted(jupiter_covers),
        'double_transit': double_transit,
        'date': now.strftime('%Y-%m-%d')
    }

if __name__ == '__main__':
    # Test with Virgo Lagna, Cancer Moon
    t = calc_transit(5, 3)  # Virgo=5, Cancer=3
    print(f"Transit date: {t['date']}")
    for name, data in t['planets'].items():
        print(f"  {name}: {data['sign']} (H{data['house']})")
    print(f"Sade Sati: {t['sade_sati']['status']}")
    print(f"Double Transit: {t['double_transit']}")
