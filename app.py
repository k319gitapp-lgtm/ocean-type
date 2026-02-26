import json
from flask import Flask, jsonify, request, render_template
from data.questions import QUESTIONS
from data.types import TYPES
from scorer import score as compute_score

app = Flask(__name__)

# Pre-build client-safe type data (no server-only fields)
_TYPE_DATA_JSON = json.dumps(
    {k: {
        "name":        v["name"],
        "description": v["description"],
        "detail":      v["detail"],
        "strengths":   v["strengths"],
        "weaknesses":  v["weaknesses"],
    } for k, v in TYPES.items()},
    ensure_ascii=False,
)


@app.get("/")
def index():
    return render_template("index.html", type_data_json=_TYPE_DATA_JSON)


@app.get("/questions")
def get_questions():
    mode = request.args.get("mode", "short")
    if mode == "short":
        qs = [q for q in QUESTIONS if q["mode"] == "both"]
    else:
        qs = QUESTIONS
    safe = [{"id": q["id"], "dimension": q["dimension"], "text": q["text"]} for q in qs]
    return jsonify(safe)


@app.post("/score")
def score_route():
    data = request.get_json(force=True)
    mode = data.get("mode", "short")
    answers = data.get("answers", {})
    if not answers:
        return jsonify({"error": "answers is required"}), 400
    result = compute_score(mode, answers)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
