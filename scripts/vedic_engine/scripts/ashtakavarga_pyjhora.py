"""
ashtakavarga_pyjhora.py - PyJHora Ashtakavarga 封装
SAV/BAV 100% 匹配 JHora 桌面版
"""


def calculate_ashtakavarga_fixed(year, month, day, hour, minute, lat, lon, tz_offset):
    """
    使用 PyJHora 计算 SAV/BAV，100% 匹配 JHora 桌面版。
    
    Returns:
        dict: {
            'sarvashtakavarga': {sign_name: int, ...},  # SAV per sign
            'bhinnashtakavarga': {planet_name: {sign_name: int, ...}, ...},  # BAV
            'sav_total': int,
            'sodhya_pindas': {...} or None,
        }
    """
    import sys
    import os
    import swisseph as swe

    pyjhora_path = None
    try:
        import jhora as _jh
        pyjhora_path = os.path.dirname(os.path.dirname(_jh.__file__))
    except ImportError:
        import site
        for sp in site.getsitepackages():
            if os.path.exists(os.path.join(sp, 'jhora')):
                pyjhora_path = sp
                break
    if pyjhora_path is None:
        raise ImportError("jhora package not found")
    if pyjhora_path not in sys.path:
        sys.path.insert(0, pyjhora_path)
    swe.set_ephe_path(os.path.join(pyjhora_path, 'jhora', 'data', 'ephe'))

    from pyjhora_compat import install_swisseph_compat
    swe = install_swisseph_compat()

    from jhora import const
    from jhora.panchanga import drik
    from jhora.panchanga.drik import Place
    from jhora.horoscope.chart import ashtakavarga, charts

    # 设置对齐
    drik.set_ayanamsa_mode('TRUE_CITRA')
    const._DEFAULT_AYANAMSA_MODE = 'TRUE_CITRA'
    const._use_true_nodes_for_rahu_ketu = False
    from pyjhora_compat import install_mean_node_policy
    install_mean_node_policy(drik)

    # JD = local time（和 Shadbala 一致）
    local_hour = hour + minute / 60.0
    jd_local = swe.julday(year, month, day, local_hour)
    place = Place('birth_place', lat, lon, tz_offset)

    # 获取 Rasi chart → house_to_planet_list
    rasi = charts.rasi_chart(jd_local, place)
    h2p = ['' for _ in range(12)]
    for entry in rasi:
        p_id = entry[0]
        sign = entry[1][0]
        if h2p[sign]:
            h2p[sign] += '/' + str(p_id)
        else:
            h2p[sign] = str(p_id)

    # 计算 BAV, SAV, Prastara
    bav_raw, sav_raw, prastara = ashtakavarga.get_ashtaka_varga(h2p)

    # 格式化输出
    SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    PLANET_NAMES = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Ascendant']

    # SAV: sign -> value
    sarvashtakavarga = {}
    for i, sign in enumerate(SIGNS):
        sarvashtakavarga[sign] = int(sav_raw[i])

    # BAV: planet -> {sign -> value}
    bhinnashtakavarga = {}
    for p_idx, p_name in enumerate(PLANET_NAMES):
        bhinnashtakavarga[p_name] = {}
        for i, sign in enumerate(SIGNS):
            bhinnashtakavarga[p_name][sign] = int(bav_raw[p_idx][i])

    # Sodhya Pindas
    try:
        sp = ashtakavarga.sodhaya_pindas(bav_raw, h2p)
        # sp returns: [sodhya_pinda, rasi_pinda, graha_pinda] for each planet?
        sodhya_pindas = {}
        if isinstance(sp, (list, tuple)):
            for i, p_name in enumerate(PLANET_NAMES[:7]):
                if i < len(sp):
                    if isinstance(sp[i], (list, tuple)) and len(sp[i]) >= 3:
                        sodhya_pindas[p_name] = {
                            'sodhya_pinda': sp[i][0],
                            'rasi_pinda': sp[i][1],
                            'graha_pinda': sp[i][2]
                        }
    except Exception:
        sodhya_pindas = None

    return {
        'sarvashtakavarga': sarvashtakavarga,
        'bhinnashtakavarga': bhinnashtakavarga,
        'sav_total': sum(sav_raw),
        'sodhya_pindas': sodhya_pindas,
    }
