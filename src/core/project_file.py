"""Project persistence (`.wsjson`, pretty-printed JSON)."""

from __future__ import annotations

import json

from .model import Project

PROJECT_EXTENSIONS = ["wsjson", "json"]


def save_project(project: Project, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(project.to_dict(), fh, indent=2)


def load_project(path: str) -> Project:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return Project.from_dict(data)
