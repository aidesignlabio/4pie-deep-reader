"""Compatibility helpers for PyJHora and supported pyswisseph releases."""


def install_swisseph_compat():
    """Install one idempotent result-shape adapter shared by every Vedic module."""
    import swisseph as swe

    if getattr(swe, "_fourpie_compat_installed", False):
        return swe

    original_calc_ut = swe.calc_ut
    original_calc = swe.calc
    original_houses_ex = getattr(swe, "houses_ex", None)

    def _two_item(result):
        if isinstance(result, tuple) and len(result) >= 2:
            return result[0], result[1]
        return result

    def calc_ut(jd, planet, flags=0):
        return _two_item(original_calc_ut(jd, planet, flags=flags))

    def calc(jd, planet, flags=0):
        return _two_item(original_calc(jd, planet, flags=flags))

    swe.calc_ut = calc_ut
    swe.calc = calc

    if original_houses_ex is not None:
        def houses_ex(*args, **kwargs):
            return _two_item(original_houses_ex(*args, **kwargs))

        swe.houses_ex = houses_ex

    swe._fourpie_compat_installed = True
    return swe


def install_mean_node_policy(drik):
    """Make PyJHora honour the configured mean-node policy in nested chart calls."""
    current = drik.dhasavarga
    if getattr(current, "_fourpie_mean_node_installed", False):
        return

    def dhasavarga(jd, place, divisional_chart_factor=1,
                   set_rahu_ketu_as_true_nodes=None, **kwargs):
        return current(
            jd,
            place,
            divisional_chart_factor=divisional_chart_factor,
            set_rahu_ketu_as_true_nodes=set_rahu_ketu_as_true_nodes,
            **kwargs,
        )

    dhasavarga._fourpie_mean_node_installed = True
    drik.dhasavarga = dhasavarga
