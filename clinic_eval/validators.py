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


def classify_answer(answer):
    # An item with no recorded answer at all isn't a compliance failure -
    # it's simply not applicable/graded, exactly like an explicit "N/A"
    # selection - so blanks are folded into "na" here rather than being
    # silently dropped from every count that reads this classification.
    text = (answer or "").strip()
    if text == "Yes":
        return "yes"
    if text == "No":
        return "no"
    if text == "STL":
        return "stl"
    return "na"


def parse_test_counts(value):
    # Stored tests_performed strings are "Name:Count" pairs, comma separated
    # ("Osom RSV:4, Blood Glucose (Fingerstick):2"). Older records were saved
    # before machine counts existed - just a plain comma-separated list of
    # names with no colon - each of those is treated as a single machine.
    counts = {}
    for part in (value or "").split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            name, _, count_text = part.rpartition(":")
            name = name.strip()
            try:
                count = int(count_text.strip())
            except ValueError:
                count = 1
        else:
            name = part
            count = 1
        if name:
            counts[name] = counts.get(name, 0) + count
    return counts


def format_test_counts(counts):
    parts = []
    for name, count in (counts or {}).items():
        try:
            count_int = int(count)
        except (TypeError, ValueError):
            continue
        if count_int > 0:
            parts.append(f"{name}:{count_int}")
    return ", ".join(parts)
