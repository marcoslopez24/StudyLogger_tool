"""JSON storage helpers for StudyTrack."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, TypedDict


DATA_FILE_ENV_VAR = "STUDYTRACK_DATA_FILE"
DEFAULT_DATA_FILE = Path.home() / ".studytrack" / "data.json"


class StudyTrackData(TypedDict):
    """Top-level StudyTrack data file shape."""

    active_session: dict[str, Any] | None
    sessions: list[dict[str, Any]]
    goals: dict[str, float]


def empty_data() -> StudyTrackData:
    """Return a fresh StudyTrack data structure."""
    return {
        "active_session": None,
        "sessions": [],
        "goals": {},
    }


def get_data_file() -> Path:
    """Return the JSON data file path."""
    data_file = os.environ.get(DATA_FILE_ENV_VAR)
    if data_file:
        return Path(data_file).expanduser()
    return DEFAULT_DATA_FILE


def load_data(data_file: Path | None = None) -> StudyTrackData:
    """Load StudyTrack data from disk, creating an empty structure if missing."""
    path = data_file or get_data_file()
    if not path.exists():
        return empty_data()

    with path.open(encoding="utf-8") as file:
        raw_data = json.load(file)

    data = empty_data()
    if isinstance(raw_data, dict):
        active_session = raw_data.get("active_session")
        sessions = raw_data.get("sessions")
        goals = raw_data.get("goals")

        if isinstance(active_session, dict) or active_session is None:
            data["active_session"] = active_session
        if isinstance(sessions, list):
            data["sessions"] = sessions
        if isinstance(goals, dict):
            data["goals"] = {
                str(course): float(hours)
                for course, hours in goals.items()
                if isinstance(hours, int | float)
            }

    return data


def save_data(data: StudyTrackData, data_file: Path | None = None) -> None:
    """Save StudyTrack data to disk as formatted JSON."""
    path = data_file or get_data_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")
