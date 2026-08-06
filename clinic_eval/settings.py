import json

from .db import DATA_DIR

SETTINGS_PATH = DATA_DIR / "settings.json"
DEFAULT_SETTINGS = {"compliance_threshold": 100}


def load_settings():
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data or {})
        return merged

    return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def get_compliance_threshold():
    return load_settings().get("compliance_threshold", 100)


def set_compliance_threshold(value):
    settings = load_settings()
    settings["compliance_threshold"] = value
    save_settings(settings)
