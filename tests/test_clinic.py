from unittest import mock

from clinic_eval.db import create_assessment, get_assessment_detail


def make_answers():
    return [{"answer": "Yes"} for _ in range(15)]


def test_edit_region_and_specialty_normalize_input(dashboard_app):
    assessment_id = create_assessment(
        "Norm Test Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers()
    )

    clinic_tab = dashboard_app.tabs["clinic"]
    clinic_tab.refresh_data()
    dashboard_app.update()
    clinic_tab.selected_clinic_var.set("Norm Test Clinic")
    clinic_tab.on_clinic_selected()
    dashboard_app.update()
    clinic_tab.current_assessment_id = assessment_id

    with mock.patch("clinic_eval.ui.clinic.messagebox.showinfo"), \
         mock.patch("clinic_eval.ui.clinic.messagebox.showerror"):
        clinic_tab.edit_region()
        dashboard_app.update()
        popup = clinic_tab.winfo_children()[-1]
        popup.value_var.set("souTH")
        popup.apply()
        dashboard_app.update()

        clinic_tab.edit_specialty()
        dashboard_app.update()
        popup2 = clinic_tab.winfo_children()[-1]
        popup2.value_var.set("ent")
        popup2.apply()
        dashboard_app.update()

    detail = get_assessment_detail(assessment_id)
    assert detail["region"] == "South"
    assert detail["specialty"] == "ENT"


def test_clinic_search_filters_and_selects(dashboard_app):
    create_assessment("PCG North Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers())
    create_assessment("PCG South Clinic", "2026-01-01", "South", "Cardiology", "", "", make_answers())
    create_assessment("Other Clinic", "2026-01-01", "East", "ENT", "", "", make_answers())

    clinic_tab = dashboard_app.tabs["clinic"]
    clinic_tab.refresh_data()
    dashboard_app.update()

    combo = clinic_tab.clinic_combobox
    combo.textvariable.set("pcg")
    dashboard_app.update()

    assert set(combo.filtered_values) == {"PCG North Clinic", "PCG South Clinic"}

    combo.select_active_listbox_item()
    dashboard_app.update()
    assert clinic_tab.current_name_var.get() in {"PCG North Clinic", "PCG South Clinic"}
