"""
divisional_pyjhora.py - PyJHora 分盘计算封装
支持所有标准分盘 (D1-D60)
使用 charts.divisional_chart(chart_method=1) — JHora Traditional Parasara
"""


def calculate_divisional_charts(year, month, day, hour, minute, lat, lon, tz_offset,
                                 chart_factors=None):
    """
    使用 PyJHora 计算分盘，与 JHora 桌面版一致。

    Returns:
        dict: {'D9': {planet: {'sign':..., 'sign_idx':..., 'degree':...}, ...}, ...}
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
    from jhora.horoscope.chart import charts

    drik.set_ayanamsa_mode('TRUE_CITRA')
    const._DEFAULT_AYANAMSA_MODE = 'TRUE_CITRA'
    const._use_true_nodes_for_rahu_ketu = False
    from pyjhora_compat import install_mean_node_policy
    install_mean_node_policy(drik)

    local_hour = hour + minute / 60.0
    jd_local = swe.julday(year, month, day, local_hour)
    place = Place('birth_place', lat, lon, tz_offset)

    SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    PLANET_MAP = {'L': 'Lagna', 0: 'Sun', 1: 'Moon', 2: 'Mars', 3: 'Mercury',
                  4: 'Jupiter', 5: 'Venus', 6: 'Saturn', 7: 'Rahu', 8: 'Ketu'}

    if chart_factors is None:
        chart_factors = [1, 2, 3, 4, 5, 7, 9, 10, 12, 16, 20, 24, 27, 30, 60]

    result = {}
    for dcf in chart_factors:
        key = f'D{dcf}'
        try:
            # Ensure Mean Node consistency
            const._use_true_nodes_for_rahu_ketu = False

            pp = charts.divisional_chart(jd_local, place,
                    divisional_chart_factor=dcf, chart_method=1)

            chart_data = {}
            for entry in pp:
                p_id = entry[0]
                sign_idx = int(entry[1][0])
                degree = entry[1][1] if len(entry[1]) > 1 else 0
                p_name = PLANET_MAP.get(p_id, str(p_id))
                chart_data[p_name] = {
                    'sign': SIGNS[sign_idx],
                    'sign_idx': sign_idx,
                    'degree': round(degree, 4) if isinstance(degree, float) else degree,
                }
            result[key] = chart_data
        except Exception as e:
            result[key] = {'error': str(e)}

    return result
