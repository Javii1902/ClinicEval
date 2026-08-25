from clinic_eval.db import create_assessment


def make_answers(yes=15):
    answers = [{"answer": "Yes"} for _ in range(yes)]
    while len(answers) < 15:
        answers.append({"answer": "N/A"})
    return answers[:15]


def test_view_clinic_dashboard_filters_to_selected_clinic(dashboard_app):
    create_assessment("Focus Clinic A", "2026-01-01", "North", "Cardiology", "", "", make_answers())
    create_assessment("Focus Clinic B", "2026-01-01", "South", "ENT", "", "", make_answers())

    clinic_tab = dashboard_app.tabs["clinic"]
    dashboard_tab = dashboard_app.tabs["dashboard"]

    clinic_tab.refresh_data()
    dashboard_app.update()
    clinic_tab.selected_clinic_var.set("Focus Clinic A")
    clinic_tab.on_clinic_selected()
    dashboard_app.update()

    clinic_tab.view_clinic_dashboard()
    dashboard_app.update()

    assert dashboard_tab.selected_clinics == ["Focus Clinic A"]
    assert dashboard_tab.clinics_filter_is_all is False
    assert len(dashboard_tab.last_dataset["clinic_rows"]) == 1
    assert dashboard_tab.last_dataset["clinic_rows"][0][0] == "Focus Clinic A"
