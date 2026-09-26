"""
history.py - Persistent research history manager.
Stores research runs (topic, results, report, critic feedback) in research_history.json.
"""

import json
import os
from datetime import datetime

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "research_history.json")


def _load_all() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_all(records: list[dict]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def save_research(topic: str, state: dict) -> dict:
    records = _load_all()
    record = {
        "id": len(records) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic,
        "search_results": state.get("search_results", ""),
        "scraped_content": state.get("scraped_content", ""),
        "report": state.get("report", ""),
        "feedback": state.get("feedback", ""),
    }
    records.append(record)
    _save_all(records)
    return record


def get_history() -> list[dict]:
    return list(reversed(_load_all()))


def get_record(record_id: int) -> dict | None:
    for r in _load_all():
        if r.get("id") == record_id:
            return r
    return None


def delete_record(record_id: int) -> bool:
    records = _load_all()
    filtered = [r for r in records if r.get("id") != record_id]
    if len(filtered) == len(records):
        return False
    _save_all(filtered)
    return True


def clear_history() -> None:
    _save_all([])
