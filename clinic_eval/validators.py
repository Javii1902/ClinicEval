import re
from datetime import datetime


def is_valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def normalize_choice(value, canonical_options):
    # Trims/collapses whitespace unconditionally, then - only if the typed
    # value case-insensitively matches one of the canonical options - snaps
    # it to that option's exact casing. A genuinely new custom value (one
    # that doesn't match anything canonical) is left as typed, so this only
    # closes the "North" vs "north" vs "North " style drift against known
    # options rather than forcing arbitrary casing rules onto real new data.
    value = (value or "").strip()
    value = re.sub(r"\s+", " ", value)
    if not value:
        return value

    canonical_by_lower = {option.lower(): option for option in canonical_options}
    return canonical_by_lower.get(value.lower(), value)
