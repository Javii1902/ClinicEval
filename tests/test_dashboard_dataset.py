from clinic_eval.db import create_assessment


def make_answers(yes=15, no=0, stl=0):
    answers = [{"answer": "Yes"} for _ in range(yes)]
    answers += [{"answer": "No"} for _ in range(no)]
    answers += [{"answer": "STL"} for _ in range(stl)]
    while len(answers) < 15:
        answers.append({"answer": "N/A"})
    return answers[:15]


def test_total_assessments_counts_all_not_just_latest(dashboard_app):
    create_assessment("Clinic A", "2026-01-01", "North", "Cardiology", "", "", make_answers())
    create_assessment("Clinic A", "2026-02-01", "North", "Cardiology", "", "", make_answers())
    create_assessment("Clinic B", "2026-01-01", "South", "ENT", "", "", make_answers())

    dash = dashboard_app.tabs["dashboard"]
    dash.refresh_data()
    dashboard_app.update()

    dataset = dash.last_dataset
    assert dataset["total_assessment_count"] == 3
    assert len(dataset["clinic_rows"]) == 2  # distinct clinics, latest-per-clinic


def test_timeline_sequences_by_visit_number_not_calendar_time(dashboard_app):
    create_assessment("Clinic A", "2025-01-01", "North", "Cardiology", "", "", make_answers(yes=15))
    create_assessment("Clinic A", "2026-06-01", "North", "Cardiology", "", "", make_answers(yes=0, no=15))
    create_assessment("Clinic B", "2026-01-01", "South", "ENT", "", "", make_answers(yes=15))

    dash = dashboard_app.tabs["dashboard"]
    dash.refresh_data()
    dashboard_app.update()

    timeline = dash.build_timeline_dataset()
    assert len(timeline["points"]) == 2  # Clinic A has 2 visits, Clinic B has 1

    point1 = timeline["points"][0]
    assert {c["clinic_name"] for c in point1["clinics"]} == {"Clinic A", "Clinic B"}

    point2 = timeline["points"][1]
    clinics_in_point2 = point2["clinics"]
    assert {c["clinic_name"] for c in clinics_in_point2} == {"Clinic A"}
    assert clinics_in_point2[0]["compliance"] == 0.0


def test_compliant_and_non_compliant_use_latest_assessment_only(dashboard_app):
    create_assessment("Clinic A", "2026-01-01", "North", "Cardiology", "", "", make_answers(yes=0, no=15))
    create_assessment("Clinic A", "2026-02-01", "North", "Cardiology", "", "", make_answers(yes=15))

    dash = dashboard_app.tabs["dashboard"]
    dash.refresh_data()
    dashboard_app.update()

    dataset = dash.last_dataset
    assert dataset["compliant_clinics"] == 1
    assert dataset["non_compliant_clinics"] == 0


def test_ungraded_clinic_not_forced_into_non_compliant(dashboard_app):
    # A clinic whose latest assessment has zero Yes/No/STL answers has
    # nothing to grade (calculate_percentage returns None) - it must not be
    # dumped into "non-compliant" regardless of the threshold, since even a
    # 0% bar can't be failed by a clinic with no score at all.
    create_assessment("Ungraded Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers(yes=0))
    create_assessment("Graded Clinic", "2026-01-01", "South", "ENT", "", "", make_answers(yes=1, no=14))

    dash = dashboard_app.tabs["dashboard"]
    dash.compliance_threshold_var.set("0")
    dash.apply_compliance_threshold()
    dashboard_app.update()

    dataset = dash.last_dataset
    assert dataset["non_compliant_clinics"] == 0
    assert dataset["compliant_clinics"] == 1
    assert len(dataset["clinic_rows"]) == 2


def test_compliance_threshold_setting_changes_compliant_count(dashboard_app):
    # Clinic sits at exactly 90% - should count as non-compliant at the
    # default 100% bar, then compliant once the bar is lowered to 90%.
    create_assessment(
        "Ninety Percent Clinic", "2026-01-01", "North", "Cardiology", "", "",
        make_answers(yes=9, no=1),
    )

    dash = dashboard_app.tabs["dashboard"]
    dash.refresh_data()
    dashboard_app.update()

    assert dash.last_dataset["compliant_clinics"] == 0
    assert dash.last_dataset["non_compliant_clinics"] == 1

    dash.compliance_threshold_var.set("90")
    dash.apply_compliance_threshold()
    dashboard_app.update()

    assert dash.last_dataset["compliant_clinics"] == 1
    assert dash.last_dataset["non_compliant_clinics"] == 0
