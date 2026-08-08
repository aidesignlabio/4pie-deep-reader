"""Human Design bodygraph calculation from full personality and design activations.

The design timestamp is solved at exactly 88 solar degrees before birth. Both
personality and design positions are calculated for all supported bodies.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Set, Tuple


GATE_SEQUENCE = [
    25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12,
    15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6,
    46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11,
    10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55, 37, 63, 22, 36,
]
GATE_OFFSET = -1.375
GATE_CENTER = {
    64: "Head", 61: "Head", 63: "Head",
    47: "Ajna", 24: "Ajna", 4: "Ajna", 17: "Ajna", 43: "Ajna", 11: "Ajna",
    62: "Throat", 23: "Throat", 56: "Throat", 35: "Throat", 12: "Throat", 45: "Throat", 33: "Throat", 8: "Throat", 31: "Throat", 20: "Throat", 16: "Throat",
    7: "G", 1: "G", 13: "G", 25: "G", 46: "G", 2: "G", 15: "G", 10: "G",
    21: "Ego", 40: "Ego", 26: "Ego", 51: "Ego",
    6: "Solar Plexus", 37: "Solar Plexus", 22: "Solar Plexus", 36: "Solar Plexus", 30: "Solar Plexus", 55: "Solar Plexus", 49: "Solar Plexus", 19: "Solar Plexus",
    34: "Sacral", 5: "Sacral", 14: "Sacral", 29: "Sacral", 59: "Sacral", 9: "Sacral", 3: "Sacral", 42: "Sacral", 27: "Sacral",
    48: "Spleen", 57: "Spleen", 44: "Spleen", 50: "Spleen", 32: "Spleen", 28: "Spleen", 18: "Spleen",
    53: "Root", 60: "Root", 52: "Root", 39: "Root", 41: "Root", 58: "Root", 38: "Root", 54: "Root",
}
CHANNELS = {
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15), (6, 59), (7, 31), (9, 52),
    (10, 20), (10, 34), (10, 57), (11, 56), (12, 22), (13, 33), (16, 48),
    (17, 62), (18, 58), (19, 49), (20, 34), (20, 57), (21, 45), (23, 43),
    (24, 61), (25, 51), (26, 44), (27, 50), (28, 38), (29, 46), (30, 41),
    (32, 54), (34, 57), (35, 36), (37, 40), (39, 55), (42, 53), (47, 64),
}
MOTORS = {"Sacral", "Solar Plexus", "Ego", "Root"}
ALL_CENTERS = {"Head", "Ajna", "Throat", "G", "Ego", "Solar Plexus", "Sacral", "Spleen", "Root"}
TYPE_INFO = {
    "Generator": ("To Respond", "Satisfaction", "Frustration"),
    "Manifesting Generator": ("To Respond, then Inform", "Satisfaction", "Frustration"),
    "Manifestor": ("To Inform", "Peace", "Anger"),
    "Projector": ("Wait for the Invitation", "Success", "Bitterness"),
    "Reflector": ("Wait a Lunar Cycle", "Surprise", "Disappointment"),
}


def gate_line(longitude: float) -> Tuple[int, int]:
    wrapped = (longitude - GATE_OFFSET) % 360
    index = int(wrapped // 5.625)
    gate = GATE_SEQUENCE[index]
    line = int((wrapped - index * 5.625) // 0.9375) + 1
    return gate, min(line, 6)


def _julian_day(local_dt: datetime, tz_offset: float) -> float:
    import swisseph as swe
    utc_dt = local_dt - timedelta(hours=tz_offset)
    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600,
        swe.GREG_CAL,
    )


def _positions(jd: float) -> Dict[str, float]:
    import swisseph as swe
    flags = swe.FLG_MOSEPH | swe.FLG_SPEED
    bodies = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO, "North_Node": swe.TRUE_NODE,
    }
    result = {name: swe.calc_ut(jd, body, flags)[0][0] for name, body in bodies.items()}
    result["Earth"] = (result["Sun"] + 180) % 360
    result["South_Node"] = (result["North_Node"] + 180) % 360
    return result


def _design_jd(birth_jd: float, personality_sun: float) -> float:
    import swisseph as swe
    flags = swe.FLG_MOSEPH | swe.FLG_SPEED
    target = (personality_sun - 88) % 360
    low, high = birth_jd - 100, birth_jd - 80
    for _ in range(64):
        midpoint = (low + high) / 2
        sun = swe.calc_ut(midpoint, swe.SUN, flags)[0][0]
        difference = (sun - target + 180) % 360 - 180
        if difference < 0:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2


def _graph(channels: List[Tuple[int, int]]) -> Dict[str, Set[str]]:
    graph: Dict[str, Set[str]] = {}
    for first, second in channels:
        left, right = GATE_CENTER[first], GATE_CENTER[second]
        graph.setdefault(left, set()).add(right)
        graph.setdefault(right, set()).add(left)
    return graph


def _reachable(graph: Dict[str, Set[str]], start: str, target: str) -> bool:
    if start not in graph or target not in graph:
        return False
    pending, visited = [start], set()
    while pending:
        node = pending.pop()
        if node == target:
            return True
        if node in visited:
            continue
        visited.add(node)
        pending.extend(graph.get(node, set()) - visited)
    return False


def _components(graph: Dict[str, Set[str]]) -> int:
    unseen = set(graph)
    count = 0
    while unseen:
        count += 1
        pending = [unseen.pop()]
        while pending:
            node = pending.pop()
            neighbours = graph.get(node, set()) & unseen
            unseen -= neighbours
            pending.extend(neighbours)
    return count


def calculate(birth_dt: datetime, lat: float, lon: float, tz_offset: float) -> Dict[str, Any]:
    import swisseph as swe

    birth_jd = _julian_day(birth_dt, tz_offset)
    personality = _positions(birth_jd)
    design_jd = _design_jd(birth_jd, personality["Sun"])
    design = _positions(design_jd)

    activations = []
    active_gates: Set[int] = set()
    body_order = ["Sun", "Earth", "North_Node", "South_Node", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    for side, positions in (("personality", personality), ("design", design)):
        for body in body_order:
            gate, line = gate_line(positions[body])
            active_gates.add(gate)
            activations.append({
                "side": side,
                "body": body,
                "longitude": round(positions[body], 6),
                "gate": gate,
                "line": line,
            })

    active_channels = sorted(pair for pair in CHANNELS if pair[0] in active_gates and pair[1] in active_gates)
    defined_centers = sorted({GATE_CENTER[gate] for channel in active_channels for gate in channel})
    graph = _graph(active_channels)
    sacral = "Sacral" in defined_centers
    motor_to_throat = any(_reachable(graph, motor, "Throat") for motor in MOTORS)
    if not defined_centers:
        hd_type = "Reflector"
    elif sacral and motor_to_throat:
        hd_type = "Manifesting Generator"
    elif sacral:
        hd_type = "Generator"
    elif motor_to_throat:
        hd_type = "Manifestor"
    else:
        hd_type = "Projector"

    if "Solar Plexus" in defined_centers:
        authority = "Emotional"
    elif sacral:
        authority = "Sacral"
    elif "Spleen" in defined_centers:
        authority = "Splenic"
    elif "Ego" in defined_centers:
        authority = "Ego"
    elif "G" in defined_centers:
        authority = "Self-Projected"
    else:
        authority = "Lunar" if hd_type == "Reflector" else "Environmental/Mental"

    components = _components(graph) if graph else 0
    definitions = {0: "No Definition", 1: "Single Definition", 2: "Split Definition", 3: "Triple Split Definition", 4: "Quadruple Split Definition"}
    personality_sun = next(a for a in activations if a["side"] == "personality" and a["body"] == "Sun")
    design_sun = next(a for a in activations if a["side"] == "design" and a["body"] == "Sun")
    profile = f"{personality_sun['line']}/{design_sun['line']}"
    p_earth = next(a for a in activations if a["side"] == "personality" and a["body"] == "Earth")
    d_earth = next(a for a in activations if a["side"] == "design" and a["body"] == "Earth")
    right_angle = {(1, 3), (1, 4), (2, 4), (2, 5), (3, 5), (3, 6), (4, 6)}
    left_angle = {(5, 1), (5, 2), (6, 2), (6, 3)}
    profile_pair = (personality_sun["line"], design_sun["line"])
    cross_type = "Right Angle" if profile_pair in right_angle else "Left Angle" if profile_pair in left_angle else "Juxtaposition"
    strategy, signature, not_self = TYPE_INFO[hd_type]
    design_local = swe.revjul(design_jd + tz_offset / 24, swe.GREG_CAL)
    design_date = f"{int(design_local[0]):04d}-{int(design_local[1]):02d}-{int(design_local[2]):02d}"

    return {
        "type": hd_type,
        "strategy": strategy,
        "signature": signature,
        "non_self_theme": not_self,
        "authority": authority,
        "profile": profile,
        "definition": definitions.get(components, f"{components}-way Split Definition"),
        "incarnation_cross": {
            "type": cross_type,
            "gates": [personality_sun["gate"], p_earth["gate"], design_sun["gate"], d_earth["gate"]],
        },
        "design_date": design_date,
        "defined_centers": defined_centers,
        "open_centers": sorted(ALL_CENTERS - set(defined_centers)),
        "channels": [f"{a}-{b}" for a, b in active_channels],
        "active_gates": sorted(active_gates),
        "activations": activations,
        "calculation_engine": "Swiss Ephemeris + full personality/design activation graph",
    }

