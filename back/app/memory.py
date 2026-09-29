import json
import re
from pathlib import Path

HISTORY_DIR = Path("data/history")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

MAX_ANSWER_CHARS = 400


def _history_file(key: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", key)
    return HISTORY_DIR / f"{safe}.json"


def _load(file: Path) -> list:
    if not file.exists():
        return []
    try:
        return json.loads(file.read_text())
    except Exception:
        return []  


def get_history(key: str, limit: int = 5) -> list:
    return _load(_history_file(key))[-limit:]


def add_to_history(key: str, question: str, answer: str):
    file = _history_file(key)
    history = _load(file)
    history.append({"question": question, "answer": answer})
    file.write_text(json.dumps(history))


def format_history(history: list) -> str:
    lines = []
    for h in history:
        answer = h["answer"]
        if len(answer) > MAX_ANSWER_CHARS:
            answer = answer[:MAX_ANSWER_CHARS] + "…"
        lines.append(f"Q: {h['question']}\nA: {answer}")
    return "\n".join(lines)