"""StudyBuddy - a practice-partner quiz app built for E. Amoani.

Hacktoberfest 2026 DEV Weekend Challenge: "Build for a Friend".
Open-source AI at its core: Gemma 3 (open weights) running locally via llama.cpp.
No API keys, no internet needed after the model is downloaded, notes never leave the machine.

Run:
    # one-time: download llama-server (llama.cpp) and the Gemma 3 GGUF, then:
    ./llama-server -m gemma3-1b-q4km.gguf -c 2048 --port 8000
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""
import json
import os
import re
from difflib import SequenceMatcher

import requests
from flask import Flask, jsonify, render_template, request

LLM_URL = os.environ.get("LLM_URL", "http://localhost:8000").rstrip("/")
MODEL = os.environ.get("STUDYBUDDY_MODEL", "gemma3-1b")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)


def llm_generate(prompt: str, num_predict: int = 1500) -> str:
    """One blocking call to the local model (OpenAI-compatible). Raises on failure."""
    resp = requests.post(
        f"{LLM_URL}/v1/chat/completions",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": num_predict,
        },
        timeout=900,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def extract_json(text: str):
    """Pull the first JSON object/array out of model output, tolerating fences."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start = min(
        (i for i in (text.find("{"), text.find("[")) if i != -1),
        default=-1,
    )
    if start == -1:
        raise ValueError("no JSON found")
    end_candidates = [text.rfind("}"), text.rfind("]")]
    end = max(end_candidates)
    return json.loads(text[start : end + 1])


QUIZ_PROMPT = """You are a study assistant helping a university student revise.
Based ONLY on the study notes below, write {n} quiz questions ({mix}).
Return STRICT JSON only, no markdown, no commentary:
{{"questions": [
  {{"id": 1, "type": "mcq", "question": "...", "options": ["...", "...", "...", "..."], "answer": "<exact text of the correct option>", "explanation": "one sentence why"}},
  {{"id": 2, "type": "short", "question": "...", "answer": "model answer in 1-2 sentences", "explanation": "one sentence"}}
]}}
Rules:
- Every question MUST be answerable from the notes. Do not invent facts outside the notes.
- mcq questions have exactly 4 options; "answer" must match one option exactly.
- Keep questions clear and concise. Vary the topics across the notes.
- Output valid JSON only.

STUDY NOTES:
{notes}"""

GRADE_ONE_PROMPT = """You are a fair university tutor grading one short answer.
Question: {question}
Reference answer: {answer}
Student answer: {student}
Does the student's answer express the key idea of the reference answer? Accept different wording, but the key idea must be there.
Reply with STRICT JSON only, no markdown, no extra text.
Example of the exact shape: {{"correct": false, "feedback": "Not quite - the key idea is missing, re-read the section and try again."}}"""


def build_quiz(notes: str, n: int, qtype: str):
    mix = {"mixed": "a mix of multiple-choice and short-answer", "mcq": "multiple-choice",
           "short": "short-answer"}[qtype]
    prompt = QUIZ_PROMPT.format(n=n, mix=mix, notes=notes[:4500])
    last_err = None
    for _ in range(2):  # one retry if the model fumbles the JSON
        try:
            data = extract_json(llm_generate(prompt))
            questions = data["questions"] if isinstance(data, dict) else data
            questions = questions[:n]
            # light validation
            clean = []
            for i, q in enumerate(questions, 1):
                q["id"] = i
                if q.get("type") == "mcq" and len(q.get("options", [])) == 4 and q.get("answer"):
                    clean.append(q)
                elif q.get("type") == "short" and q.get("answer"):
                    clean.append(q)
            if clean:
                return clean
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"quiz generation failed: {last_err}")


def _norm(s):
    return " ".join(re.sub(r"[^a-z0-9\s]", "", (s or "").lower()).split())


def short_is_clearly_right(student, ref):
    """Deterministic pre-check for short answers: a near-verbatim or very-high-
    overlap answer is always correct, without consulting the small local model
    (which can be flaky on obvious matches)."""
    ns, nr = _norm(student), _norm(ref)
    if not ns or not nr:
        return False
    if ns == nr:
        return True
    st, rt = set(ns.split()), set(nr.split())
    if len(st & rt) / len(rt) >= 0.85:
        return True
    return SequenceMatcher(None, ns, nr).ratio() >= 0.88


def grade_one(it):
    """Grade a single answer. MCQs are checked deterministically; short answers go to the model."""
    if it.get("type") == "mcq":
        # compare normalized: option text may carry trailing punctuation
        # ("efficiently.") while the key doesn't ("efficiently")
        correct = bool(_norm(it.get("answer"))) and _norm(it.get("student")) == _norm(it.get("answer"))
        return correct, ("Correct - nice!" if correct else "Not quite - see the answer below.")
    if short_is_clearly_right(it.get("student"), it.get("answer")):
        return True, "Correct - nice!"
    prompt = GRADE_ONE_PROMPT.format(
        question=it["question"], answer=it["answer"],
        student=it["student"] or "(no answer given)",
    )
    last_err = None
    for _ in range(2):
        try:
            v = extract_json(llm_generate(prompt, num_predict=150))
            return bool(v.get("correct", False)), v.get("feedback", "")
        except Exception as e:  # noqa: BLE001
            last_err = e
    # last resort: exact/close match instead of failing the whole submission
    truth = (it["answer"] or "").strip().lower()
    given = (it["student"] or "").strip().lower()
    return (truth and truth in given), f"(auto-graded; model hiccup: {last_err})"


def grade_answers(items):
    results = []
    for it in items:
        correct, feedback = grade_one(it)
        results.append({
            "id": it["id"],
            "correct": correct,
            "feedback": feedback,
            "user_answer": it["student"],
            "correct_answer": it["answer"],
            "explanation": it.get("explanation", ""),
        })
    return results


@app.get("/")
def index():
    return render_template("index.html", model=MODEL)


@app.get("/api/health")
def health():
    try:
        r = requests.get(f"{LLM_URL}/health", timeout=5)
        ok = r.json().get("status") == "ok"
        return jsonify({"llm": ok, "model": MODEL, "backend": "llama.cpp (local)"})
    except Exception as e:  # noqa: BLE001
        return jsonify({"llm": False, "error": str(e)}), 503


@app.get("/api/sample-notes")
def sample_notes():
    with open(os.path.join(BASE_DIR, "sample_notes.md")) as f:
        return jsonify({"notes": f.read()})


@app.post("/api/quiz")
def quiz():
    body = request.get_json(force=True)
    notes = (body.get("notes") or "").strip()
    if len(notes) < 50:
        return jsonify({"error": "Paste some study notes first (at least a paragraph)."}), 400
    n = max(1, min(10, int(body.get("num_questions", 5))))
    qtype = body.get("qtype", "mixed")
    if qtype not in ("mixed", "mcq", "short"):
        qtype = "mixed"
    try:
        return jsonify({"questions": build_quiz(notes, n, qtype), "model": MODEL})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


@app.post("/api/grade")
def grade():
    body = request.get_json(force=True)
    items = body.get("items", [])
    if not items:
        return jsonify({"error": "nothing to grade"}), 400
    try:
        results = grade_answers(items)
        score = sum(1 for r in results if r["correct"])
        return jsonify({"results": results, "score": score, "total": len(results)})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
