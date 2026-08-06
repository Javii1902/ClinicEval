from clinic_eval.db import (
    create_assessment,
    get_clinic_names,
    get_assessment_detail,
    get_latest_assessment_for_clinic,
    get_latest_region_for_clinic,
    get_latest_specialty_for_clinic,
    update_assessment_content,
    update_assessment_region,
    update_assessment_specialty,
    update_assessment_date,
    rename_clinic,
    delete_assessment,
    backup_database,
    get_connection,
)


def make_answers(yes=15, no=0, stl=0):
    answers = [{"answer": "Yes"} for _ in range(yes)]
    answers += [{"answer": "No"} for _ in range(no)]
    answers += [{"answer": "STL"} for _ in range(stl)]
    while len(answers) < 15:
        answers.append({"answer": "N/A"})
    return answers[:15]


def test_create_and_fetch_assessment(isolated_db):
    assessment_id = create_assessment(
        clinic_name="Acme Clinic", assessment_date="2026-01-01", region="North",
        specialty="Cardiology", tests_performed="Test A, Test B", notes="hello",
        answers_and_comments=make_answers(yes=10, no=5),
    )
    assert assessment_id is not None

    detail = get_assessment_detail(assessment_id)
    assert detail["clinic_name"] == "Acme Clinic"
    assert detail["region"] == "North"
    assert detail["q1_answer"] == "Yes"


def test_get_clinic_names_returns_distinct_sorted(isolated_db):
    create_assessment("Beta Clinic", "2026-01-01", "North", "ENT", "", "", make_answers())
    create_assessment("Alpha Clinic", "2026-01-02", "South", "ENT", "", "", make_answers())
    names = get_clinic_names()
    assert names == sorted(names)
    assert "Alpha Clinic" in names and "Beta Clinic" in names


def test_get_latest_assessment_and_region_specialty(isolated_db):
    create_assessment("Acme Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers())
    create_assessment("Acme Clinic", "2026-03-01", "South", "ENT", "", "", make_answers())

    latest = get_latest_assessment_for_clinic("Acme Clinic")
    assert latest[2] == "2026-03-01"
    assert get_latest_region_for_clinic("Acme Clinic") == "South"
    assert get_latest_specialty_for_clinic("Acme Clinic") == "ENT"


def test_update_assessment_content_changes_answers(isolated_db):
    assessment_id = create_assessment(
        "Acme Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers(yes=15)
    )
    updated = update_assessment_content(
        assessment_id=assessment_id, tests_performed="New Test", notes="updated",
        answers_and_comments=make_answers(yes=0, no=15),
    )
    assert updated == 1
    detail = get_assessment_detail(assessment_id)
    assert detail["q1_answer"] == "No"
    assert detail["notes"] == "updated"


def test_update_region_and_specialty(isolated_db):
    assessment_id = create_assessment("Acme Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers())
    update_assessment_region(assessment_id, "West")
    update_assessment_specialty(assessment_id, "ENT")
    detail = get_assessment_detail(assessment_id)
    assert detail["region"] == "West"
    assert detail["specialty"] == "ENT"


def test_update_assessment_date(isolated_db):
    assessment_id = create_assessment("Acme Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers())
    update_assessment_date(assessment_id, "2026-05-05")
    detail = get_assessment_detail(assessment_id)
    assert detail["assessment_date"] == "2026-05-05"


def test_rename_clinic_updates_all_rows(isolated_db):
    create_assessment("Old Name", "2026-01-01", "North", "Cardiology", "", "", make_answers())
    create_assessment("Old Name", "2026-02-01", "North", "Cardiology", "", "", make_answers())
    updated = rename_clinic("Old Name", "New Name")
    assert updated == 2
    assert "New Name" in get_clinic_names()
    assert "Old Name" not in get_clinic_names()


def test_delete_assessment(isolated_db):
    assessment_id = create_assessment("Acme Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers())
    deleted = delete_assessment(assessment_id)
    assert deleted == 1
    assert get_assessment_detail(assessment_id) is None


def test_expected_indices_exist(isolated_db):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='assessments'")
        index_names = {row[0] for row in cursor.fetchall()}

    for expected in (
        "idx_assessments_clinic_name",
        "idx_assessments_assessment_date",
        "idx_assessments_region",
        "idx_assessments_specialty",
    ):
        assert expected in index_names


def test_backup_creates_file_and_skips_second_same_day(isolated_db):
    create_assessment("Acme Clinic", "2026-01-01", "North", "Cardiology", "", "", make_answers())

    first = backup_database(force=True)
    assert first is not None and first.exists()

    skipped = backup_database(force=False)
    assert skipped is None

    forced_again = backup_database(force=True)
    assert forced_again is not None
    assert forced_again != first


def test_backup_with_no_database_file_returns_none(isolated_db, tmp_path):
    import clinic_eval.db as db
    db.DB_PATH.unlink(missing_ok=True)
    assert backup_database(force=True) is None
