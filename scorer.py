from data.questions import QUESTIONS
from data.types import TYPES, DIMENSIONS


def get_compatibility(user_code: str):
    """
    Returns (compatible_top3, incompatible_top3) based on dimension-match count.
    Most compatible = most shared dimensions.
    Least compatible = fewest shared dimensions.
    """
    match_scores = {}
    for code in TYPES:
        if code == user_code:
            continue
        n = sum(1 for a, b in zip(user_code, code) if a == b)
        match_scores[code] = n

    desc = sorted(match_scores.items(), key=lambda x: (-x[1], x[0]))
    asc  = sorted(match_scores.items(), key=lambda x:  (x[1], x[0]))

    def make(pairs):
        return [{"code": c, "name": TYPES[c]["name"], "matches": s} for c, s in pairs]

    return make(desc[:3]), make(asc[:3])


def score(mode: str, answers: dict) -> dict:
    """
    answers: {q_id: raw_score (1-5)} — already converted server-side
    Returns full result dict.
    """
    if mode == "short":
        relevant = [q for q in QUESTIONS if q["mode"] == "both"]
    else:
        relevant = QUESTIONS

    dim_data: dict[str, dict] = {
        d: {"weighted_sum": 0.0, "min_possible": 0.0, "max_possible": 0.0}
        for d in DIMENSIONS
    }

    for q in relevant:
        q_id = q["id"]
        if q_id not in answers:
            continue
        raw = int(answers[q_id])
        raw = max(1, min(5, raw))

        s = (6 - raw) if q["reverse"] else raw
        w = q["weight"]
        d = q["dimension"]

        dim_data[d]["weighted_sum"] += s * w
        dim_data[d]["min_possible"] += 1 * w
        dim_data[d]["max_possible"] += 5 * w

    scores: dict[str, float] = {}
    for d, v in dim_data.items():
        rng = v["max_possible"] - v["min_possible"]
        scores[d] = (v["weighted_sum"] - v["min_possible"]) / rng * 100 if rng else 50.0

    type_letters: dict[str, str] = {}
    confidence: dict[str, float] = {}
    type_code_parts = []

    for d in ["E", "O", "P", "H", "S"]:
        sc = scores[d]
        dim = DIMENSIONS[d]
        letter = dim["high"] if sc >= 50 else dim["low"]
        type_letters[d] = letter
        type_code_parts.append(letter)
        confidence[d] = round(abs(sc - 50), 1)

    type_code = "".join(type_code_parts)
    type_info = TYPES.get(type_code, {})

    compatible, incompatible = get_compatibility(type_code)

    return {
        "type_code": type_code,
        "type_name": type_info.get("name", "不明"),
        "description": type_info.get("description", ""),
        "detail": type_info.get("detail", ""),
        "strengths": type_info.get("strengths", []),
        "weaknesses": type_info.get("weaknesses", []),
        "scores": {d: round(scores[d], 1) for d in scores},
        "confidence": confidence,
        "type_letters": type_letters,
        "compatible": compatible,
        "incompatible": incompatible,
    }
