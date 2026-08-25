from clinic_eval.db import create_assessment
from clinic_eval.validators import format_test_counts


def make_answers():
    return [{"answer": "Yes"} for _ in range(15)]


def test_bar_chart_tooltip_breakdown_by_clinic(dashboard_app):
    create_assessment(
        "Tooltip Clinic A", "2026-01-01", "North", "Cardiology",
        format_test_counts({"Osom RSV": 4, "Blood Glucose (Fingerstick)": 2}),
        "", make_answers(),
    )
    create_assessment(
        "Tooltip Clinic B", "2026-01-01", "South", "ENT",
        format_test_counts({"Osom RSV": 1}),
        "", make_answers(),
    )

    dash = dashboard_app.tabs["dashboard"]
    dash.refresh_data()
    dashboard_app.update()

    dataset = dash.last_dataset
    assert dataset["test_counts"]["Osom RSV"] == 5
    breakdown = dataset["test_clinic_counts"]["Osom RSV"]
    assert breakdown == {"Tooltip Clinic A": 4, "Tooltip Clinic B": 1}
