# file: task.py
import ast
import json


def parse_any(x):
    if isinstance(x, (dict, list)):
        return x
    s = x.strip()
    try:
        return json.loads(s)
    except Exception:
        return ast.literal_eval(s)


def normalize_term(term):
    if term is None:
        return term

    t = str(term).strip().lower()
    aliases = {
        "нормально": "комфортно",
        "комф": "комфортно",
        "слабо": "слабый",
        "слаб": "слабый",
        "умеренно": "умеренный",
        "умерен": "умеренный",
        "интенсивно": "интенсивный",
        "интенс": "интенсивный",
    }
    return aliases.get(t, t)


def _clamp01(v):
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def membership(x, points):
    if not points:
        return 0.0

    pts = [(float(px), float(py)) for px, py in points]
    pts.sort(key=lambda p: p[0])

    if x <= pts[0][0]:
        return _clamp01(pts[0][1])
    if x >= pts[-1][0]:
        return _clamp01(pts[-1][1])

    ys_at_x = [py for px, py in pts if px == x]
    if ys_at_x:
        return _clamp01(max(ys_at_x))

    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        if x1 <= x <= x2:
            if x2 == x1:
                y = max(y1, y2)
            else:
                k = (x - x1) / (x2 - x1)
                y = y1 + k * (y2 - y1)
            return _clamp01(y)

    return 0.0


def build_term_map(var_obj, var_name):
    out = {}
    for term in var_obj[var_name]:
        term_id = normalize_term(term.get("id"))
        out[term_id] = term.get("points")
    return out


def main(temperature_json, heating_json, rules_json, t_current):
    temp_obj = parse_any(temperature_json)
    heat_obj = parse_any(heating_json)
    rules = parse_any(rules_json)

    temp_terms = build_term_map(temp_obj, "температура")
    heat_terms = build_term_map(heat_obj, "уровень нагрева")

    t = float(t_current)
    mu_t = {term: membership(t, pts) for term, pts in temp_terms.items()}

    xs = []
    for pts in heat_terms.values():
        for px, _py in pts:
            xs.append(float(px))

    s_min, s_max = min(xs), max(xs)
    if s_max < s_min:
        s_min, s_max = s_max, s_min

    span = s_max - s_min
    if span == 0:
        return float(s_min)

    n = 10000
    step = span / n
    mu_out = [0.0] * (n + 1)

    for pair in rules:
        ant = normalize_term(pair[0])
        cons = normalize_term(pair[1])

        activation = float(mu_t[ant])
        if activation <= 0.0:
            continue

        cons_pts = heat_terms[cons]
        for i in range(n + 1):
            s = s_min + step * i
            mu_cons = membership(s, cons_pts)
            mu_rule = activation if activation < mu_cons else mu_cons
            if mu_rule > mu_out[i]:
                mu_out[i] = mu_rule

    max_mu = max(mu_out) if mu_out else 0.0
    eps = 1e-12
    for i, v in enumerate(mu_out):
        if v >= max_mu - eps:
            return float(s_min + step * i)

    return float(s_min)


if __name__ == "__main__":
    from constants import NAGREV, TEMP

    t = main(
        TEMP,
        NAGREV,
        "[['холодно','интенсивно'],['нормально','умеренно'],['жарко','слабо']]",
        21.0,
    )
    print(t)

