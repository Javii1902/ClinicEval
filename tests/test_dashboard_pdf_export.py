import os
from clinic_eval.db import create_assessment
from clinic_eval.validators import format_test_counts


def make_answers(yes=10, no=3, stl=1):
    answers = [{"answer": "Yes"} for _ in range(yes)]
    answers += [{"answer": "No"} for _ in range(no)]
    answers += [{"answer": "STL"} for _ in range(stl)]
    while len(answers) < 15:
        answers.append({"answer": None})
    return answers[:15]


def test_export_dashboard_pdf_end_to_end(dashboard_app, tmp_path):
    create_assessment(
        "PDF Export Clinic A", "2026-01-01", "North", "Cardiology",
        format_test_counts({"Osom RSV": 4, "Blood Glucose (Fingerstick)": 2}),
        "", make_answers(yes=12, no=2, stl=0),
    )
    create_assessment(
        "PDF Export Clinic A", "2026-02-01", "North", "Cardiology",
        format_test_counts({"Osom RSV": 4}),
        "", make_answers(yes=14, no=0, stl=1),
    )
    create_assessment(
        "PDF Export Clinic B", "2026-01-15", "South", "ENT",
        format_test_counts({"Osom RSV": 1, "Multistix 10SG - UA": 3}),
        "", make_answers(yes=5, no=8, stl=0),
    )

    dash = dashboard_app.tabs["dashboard"]
    dash.refresh_data()
    dashboard_app.update()

    from clinic_eval.ui.pdf_exports import export_dashboard_pdf
    from clinic_eval.ui.dashboard import QUESTIONS

    out_path = tmp_path / "dashboard_export.pdf"
    dataset = dash.build_dashboard_dataset()
    export_dashboard_pdf(
        file_path=str(out_path),
        dataset=dataset,
        questions=QUESTIONS,
        year_value=dash.year_var.get(),
        month_value=dash.month_var.get(),
        selected_clinics=dash.selected_clinics,
        selected_regions=dash.selected_regions,
        selected_specialties=dash.selected_specialties,
        timeline_dataset=dash.build_timeline_dataset(),
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 1000
