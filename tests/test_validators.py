from clinic_eval.validators import is_valid_date, normalize_choice


def test_is_valid_date_accepts_correct_format():
    assert is_valid_date("2026-01-01") is True


def test_is_valid_date_rejects_bad_format():
    assert is_valid_date("01/01/2026") is False
    assert is_valid_date("not-a-date") is False
    assert is_valid_date("") is False


def test_normalize_choice_snaps_to_canonical_casing():
    options = ["North", "South", "ENT"]
    assert normalize_choice("north", options) == "North"
    assert normalize_choice("NORTH", options) == "North"
    assert normalize_choice("  north  ", options) == "North"


def test_normalize_choice_preserves_acronym_casing():
    # A blind .title() would mangle "ENT" into "Ent" - this must not happen.
    options = ["ENT", "Cardiology"]
    assert normalize_choice("ent", options) == "ENT"
    assert normalize_choice("Ent", options) == "ENT"


def test_normalize_choice_preserves_unknown_values_as_typed():
    options = ["North", "South"]
    assert normalize_choice("Somewhere New", options) == "Somewhere New"


def test_normalize_choice_collapses_internal_whitespace():
    assert normalize_choice("North   America", ["North America"]) == "North America"
    assert normalize_choice("Custom   Value", ["North"]) == "Custom Value"


def test_normalize_choice_blank_stays_blank():
    assert normalize_choice("   ", ["North"]) == ""
    assert normalize_choice(None, ["North"]) == ""
    assert normalize_choice("", []) == ""
