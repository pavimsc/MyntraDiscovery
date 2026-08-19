"""Shared JSON load/save helpers and data paths for Myntra wishlist friction analysis."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RAW_REVIEWS_PATH = DATA_DIR / "raw_reviews.json"
THEMES_PATH = DATA_DIR / "themes.json"
INSIGHTS_PATH = DATA_DIR / "insights.json"


def load_json(path: Path):
    """Load JSON from path. Return list or dict based on file content. Returns empty if file doesn't exist."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Return appropriate default
    if path.name == "raw_reviews.json":
        return []
    return {}


def save_json(path: Path, data) -> None:
    """Save JSON to path with proper formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
