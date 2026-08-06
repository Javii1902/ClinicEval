from unittest import mock

from clinic_eval.db import get_assessments_for_clinic, get_assessment_detail


def test_save_assessment_normalizes_region_and_specialty(dashboard_app):
    new_tab = dashboard_app.tabs["new_assessment"]
    new_tab.clinic_name_var.set("Norm Clinic")
    new_tab.region_var.set("north")
    new_tab.specialty_var.set("ent")
    new_tab.assessment_date_var.set("2026-01-01")
    for var in new_tab.answer_vars:
        var.set("Yes")

    with mock.patch("clinic_eval.ui.new_assessment.messagebox.showinfo"), \
         mock.patch("clinic_eval.ui.new_assessment.messagebox.showerror") as mock_error:
        new_tab.save_assessment()
    dashboard_app.update()

    assert not mock_error.called

    rows = get_assessments_for_clinic("Norm Clinic")
    assert len(rows) == 1

    detail = get_assessment_detail(rows[0][0])
    assert detail["region"] == "North"
    assert detail["specialty"] == "ENT"


def test_save_assessment_preserves_new_custom_region(dashboard_app):
    new_tab = dashboard_app.tabs["new_assessment"]
    new_tab.clinic_name_var.set("Custom Region Clinic")
    new_tab.region_var.set("  Somewhere New  ")
    new_tab.specialty_var.set("Cardiology")
    new_tab.assessment_date_var.set("2026-01-01")
    for var in new_tab.answer_vars:
        var.set("Yes")

    with mock.patch("clinic_eval.ui.new_assessment.messagebox.showinfo"), \
         mock.patch("clinic_eval.ui.new_assessment.messagebox.showerror") as mock_error:
        new_tab.save_assessment()
    dashboard_app.update()

    assert not mock_error.called

    rows = get_assessments_for_clinic("Custom Region Clinic")
    detail = get_assessment_detail(rows[0][0])
    assert detail["region"] == "Somewhere New"
