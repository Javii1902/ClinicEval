import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

# This file lives in clinic_eval/db.py, so the project root (where Data/
# actually is) is two levels up from here.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"
DB_PATH = DATA_DIR / "clinic_eval.db"
BACKUP_DIR = DATA_DIR / "backups"
MAX_BACKUPS = 10

_database_initialized = False


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    # A plain `with sqlite3.connect(...) as conn:` only commits/rolls back
    # the transaction on exit - it does NOT close the connection, so the
    # underlying file handle can outlive the `with` block until garbage
    # collection gets around to it. On Windows that's long enough to make
    # an immediately-following file operation (backup, delete) fail with
    # "file in use". Wrapping it as a real context manager guarantees the
    # connection - and its file handle - is released deterministically.
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def ensure_assessments_column(cursor, column_name, column_definition):
    cursor.execute("PRAGMA table_info(assessments)")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE assessments ADD COLUMN {column_name} {column_definition}")


def initialize_database():
    # Every function below calls this defensively, so without this guard the
    # full schema/migration check (~50 PRAGMA/ALTER statements) reran on
    # every single database call in the app - every filter change, every
    # treeview sort-triggered reload, every clinic selection. It only ever
    # needs to actually run once per process.
    global _database_initialized
    if _database_initialized:
        return

    ensure_data_dir()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic_name TEXT NOT NULL,
            assessment_date TEXT NOT NULL,

            q1_answer TEXT,
            q1_comment TEXT,
            q2_answer TEXT,
            q2_comment TEXT,
            q3_answer TEXT,
            q3_comment TEXT,
            q4_answer TEXT,
            q4_comment TEXT,
            q5_answer TEXT,
            q5_comment TEXT,
            q6_answer TEXT,
            q6_comment TEXT,
            q7_answer TEXT,
            q7_comment TEXT,
            q8_answer TEXT,
            q8_comment TEXT,
            q9_answer TEXT,
            q9_comment TEXT,
            q10_answer TEXT,
            q10_comment TEXT,
            q11_answer TEXT,
            q11_comment TEXT,
            q12_answer TEXT,
            q12_comment TEXT,
            q13_answer TEXT,
            q13_comment TEXT,
            q14_answer TEXT,
            q14_comment TEXT,
            q15_answer TEXT,
            q15_comment TEXT,

            notes TEXT,
            tests_performed TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comment_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_type TEXT NOT NULL,
            question_number INTEGER,
            template_text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_comment_templates_unique
        ON comment_templates (template_type, question_number, template_text)
        """)

        ensure_assessments_column(cursor, "region", "TEXT")
        ensure_assessments_column(cursor, "specialty", "TEXT")
        ensure_assessments_column(cursor, "tests_performed", "TEXT")
        ensure_assessments_column(cursor, "created_at", "TEXT DEFAULT CURRENT_TIMESTAMP")

        for i in range(1, 16):
            ensure_assessments_column(cursor, f"q{i}_template_comment", "TEXT")
            ensure_assessments_column(cursor, f"q{i}_manual_comment", "TEXT")
            ensure_assessments_column(cursor, f"q{i}_custom_comment", "TEXT")

        # These four columns are exactly what every dashboard filter query
        # (clinic/region/specialty pickers, Year/Month, the timeline) filters
        # or sorts on, so they're the ones worth indexing. Created last,
        # after the ensure_assessments_column() calls above, since region/
        # specialty don't exist yet on a database migrating up from old data.
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessments_clinic_name ON assessments (clinic_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessments_assessment_date ON assessments (assessment_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessments_region ON assessments (region)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessments_specialty ON assessments (specialty)")

        conn.commit()

    _database_initialized = True


def backup_database(force=True):
    # A cheap insurance policy against an accidental delete or a corrupted
    # write: a timestamped copy of the whole database file. force=True
    # (the manual "Backup Database Now" button) always makes a fresh copy;
    # force=False (the automatic startup backup) skips it if today already
    # has one, so restarting the app repeatedly during a single day doesn't
    # pile up near-duplicate backups.
    initialize_database()

    if not DB_PATH.exists():
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y%m%d")

    if not force and any(BACKUP_DIR.glob(f"clinic_eval_{date_str}_*.db")):
        return None

    # Microsecond precision, not just seconds: two force=True backups
    # (e.g. the manual button clicked twice quickly, or a test) within the
    # same second would otherwise collide on an identical filename.
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    backup_path = BACKUP_DIR / f"clinic_eval_{timestamp}.db"
    shutil.copy2(DB_PATH, backup_path)

    _prune_old_backups()

    return backup_path


def _prune_old_backups(keep=MAX_BACKUPS):
    backups = sorted(
        BACKUP_DIR.glob("clinic_eval_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old_backup in backups[keep:]:
        old_backup.unlink(missing_ok=True)


def get_clinic_names():
    initialize_database()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT DISTINCT clinic_name
        FROM assessments
        WHERE clinic_name IS NOT NULL
          AND TRIM(clinic_name) <> ''
        ORDER BY clinic_name
        """)
        rows = cursor.fetchall()

    return [row[0] for row in rows]


def get_latest_region_for_clinic(clinic_name):
    initialize_database()

    clinic_name = (clinic_name or "").strip()
    if not clinic_name:
        return None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT region
        FROM assessments
        WHERE clinic_name = ?
          AND region IS NOT NULL
          AND TRIM(region) <> ''
        ORDER BY assessment_date DESC, id DESC
        LIMIT 1
        """, (clinic_name,))
        row = cursor.fetchone()

    if not row:
        return None

    return row[0]


def get_latest_specialty_for_clinic(clinic_name):
    initialize_database()

    clinic_name = (clinic_name or "").strip()
    if not clinic_name:
        return None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT specialty
        FROM assessments
        WHERE clinic_name = ?
          AND specialty IS NOT NULL
          AND TRIM(specialty) <> ''
        ORDER BY assessment_date DESC, id DESC
        LIMIT 1
        """, (clinic_name,))
        row = cursor.fetchone()

    if not row:
        return None

    return row[0]


def get_comment_templates(template_type, question_number=None):
    initialize_database()

    with get_connection() as conn:
        cursor = conn.cursor()

        if template_type == "overall":
            cursor.execute("""
            SELECT template_text
            FROM comment_templates
            WHERE template_type = 'overall'
            ORDER BY template_text
            """)
        else:
            cursor.execute("""
            SELECT template_text
            FROM comment_templates
            WHERE template_type = ?
              AND question_number = ?
            ORDER BY template_text
            """, (template_type, question_number))

        rows = cursor.fetchall()

    return [row[0] for row in rows]


def get_all_question_comment_templates():
    # Building the New Assessment / Clinic forms calls get_comment_templates
    # once per question (15 separate round-trips) every time either tab is
    # built or refreshed. One query for every question's templates, grouped
    # in Python, replaces all 15.
    initialize_database()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT question_number, template_text
        FROM comment_templates
        WHERE template_type = 'question'
        ORDER BY question_number, template_text
        """)
        rows = cursor.fetchall()

    templates_by_question = {}
    for question_number, template_text in rows:
        templates_by_question.setdefault(question_number, []).append(template_text)

    return templates_by_question


def add_comment_template(template_type, template_text, question_number=None):
    initialize_database()

    cleaned_text = (template_text or "").strip()
    if not cleaned_text:
        return

    normalized_question_number = question_number if template_type == "question" else None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO comment_templates (
            template_type,
            question_number,
            template_text
        )
        VALUES (?, ?, ?)
        """, (template_type, normalized_question_number, cleaned_text))
        conn.commit()


def delete_comment_template(template_type, template_text, question_number=None):
    initialize_database()

    cleaned_text = (template_text or "").strip()
    if not cleaned_text:
        return

    normalized_question_number = question_number if template_type == "question" else None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        DELETE FROM comment_templates
        WHERE template_type = ?
          AND template_text = ?
          AND (
                (question_number IS NULL AND ? IS NULL)
                OR question_number = ?
              )
        """, (template_type, cleaned_text, normalized_question_number, normalized_question_number))
        conn.commit()


def rename_clinic(old_name, new_name):
    initialize_database()

    old_name = (old_name or "").strip()
    new_name = (new_name or "").strip()

    if not old_name or not new_name or new_name == old_name:
        return 0

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE assessments
        SET clinic_name = ?
        WHERE clinic_name = ?
        """, (new_name, old_name))
        conn.commit()
        return cursor.rowcount


def get_assessments_for_clinic(clinic_name):
    initialize_database()

    clinic_name = (clinic_name or "").strip()
    if not clinic_name:
        return []

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, assessment_date
        FROM assessments
        WHERE clinic_name = ?
        ORDER BY assessment_date DESC, id DESC
        """, (clinic_name,))
        rows = cursor.fetchall()

    return rows


def update_assessment_specialty(assessment_id, new_specialty):
    initialize_database()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE assessments
        SET specialty = ?
        WHERE id = ?
        """, (new_specialty, assessment_id))
        conn.commit()
        return cursor.rowcount


def update_assessment_date(assessment_id, new_date):
    initialize_database()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE assessments
        SET assessment_date = ?
        WHERE id = ?
        """, (new_date, assessment_id))
        conn.commit()
        return cursor.rowcount


def update_assessment_region(assessment_id, new_region):
    initialize_database()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE assessments
        SET region = ?
        WHERE id = ?
        """, (new_region, assessment_id))
        conn.commit()
        return cursor.rowcount


def delete_assessment(assessment_id):
    initialize_database()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        DELETE FROM assessments
        WHERE id = ?
        """, (assessment_id,))
        conn.commit()
        return cursor.rowcount


def get_latest_assessment_for_clinic(clinic_name):
    initialize_database()

    clinic_name = (clinic_name or "").strip()
    if not clinic_name:
        return None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, clinic_name, assessment_date
        FROM assessments
        WHERE clinic_name = ?
        ORDER BY assessment_date DESC, id DESC
        LIMIT 1
        """, (clinic_name,))
        row = cursor.fetchone()

    return row


def get_assessment_detail(assessment_id):
    initialize_database()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT *
        FROM assessments
        WHERE id = ?
        """, (assessment_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))


def update_assessment_content(assessment_id, tests_performed, notes, answers_and_comments):
    initialize_database()

    sql = """
    UPDATE assessments
    SET q1_answer = ?, q1_comment = ?, q1_template_comment = ?, q1_manual_comment = ?, q1_custom_comment = ?,
        q2_answer = ?, q2_comment = ?, q2_template_comment = ?, q2_manual_comment = ?, q2_custom_comment = ?,
        q3_answer = ?, q3_comment = ?, q3_template_comment = ?, q3_manual_comment = ?, q3_custom_comment = ?,
        q4_answer = ?, q4_comment = ?, q4_template_comment = ?, q4_manual_comment = ?, q4_custom_comment = ?,
        q5_answer = ?, q5_comment = ?, q5_template_comment = ?, q5_manual_comment = ?, q5_custom_comment = ?,
        q6_answer = ?, q6_comment = ?, q6_template_comment = ?, q6_manual_comment = ?, q6_custom_comment = ?,
        q7_answer = ?, q7_comment = ?, q7_template_comment = ?, q7_manual_comment = ?, q7_custom_comment = ?,
        q8_answer = ?, q8_comment = ?, q8_template_comment = ?, q8_manual_comment = ?, q8_custom_comment = ?,
        q9_answer = ?, q9_comment = ?, q9_template_comment = ?, q9_manual_comment = ?, q9_custom_comment = ?,
        q10_answer = ?, q10_comment = ?, q10_template_comment = ?, q10_manual_comment = ?, q10_custom_comment = ?,
        q11_answer = ?, q11_comment = ?, q11_template_comment = ?, q11_manual_comment = ?, q11_custom_comment = ?,
        q12_answer = ?, q12_comment = ?, q12_template_comment = ?, q12_manual_comment = ?, q12_custom_comment = ?,
        q13_answer = ?, q13_comment = ?, q13_template_comment = ?, q13_manual_comment = ?, q13_custom_comment = ?,
        q14_answer = ?, q14_comment = ?, q14_template_comment = ?, q14_manual_comment = ?, q14_custom_comment = ?,
        q15_answer = ?, q15_comment = ?, q15_template_comment = ?, q15_manual_comment = ?, q15_custom_comment = ?,
        notes = ?,
        tests_performed = ?
    WHERE id = ?
    """

    values = []
    for item in answers_and_comments:
        answer = item.get("answer")
        combined_comment = item.get("combined_comment")
        template_comment = item.get("template_comment")
        manual_comment = item.get("manual_comment")
        custom_comment = item.get("custom_comment")
        values.extend([answer, combined_comment, template_comment, manual_comment, custom_comment])

    values.extend([notes, tests_performed, assessment_id])

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, values)
        conn.commit()
        return cursor.rowcount


def create_assessment(clinic_name, assessment_date, region, specialty, tests_performed, notes, answers_and_comments):
    initialize_database()

    columns = ["clinic_name", "assessment_date", "region", "specialty", "tests_performed", "notes"]
    values = [clinic_name, assessment_date, region, specialty, tests_performed, notes]

    for index, item in enumerate(answers_and_comments, start=1):
        columns.extend([
            f"q{index}_answer",
            f"q{index}_comment",
            f"q{index}_template_comment",
            f"q{index}_manual_comment",
            f"q{index}_custom_comment",
        ])
        values.extend([
            item.get("answer"),
            item.get("combined_comment"),
            item.get("template_comment"),
            item.get("manual_comment"),
            item.get("custom_comment"),
        ])

    placeholders = ", ".join("?" for _ in values)
    sql = f"INSERT INTO assessments ({', '.join(columns)}) VALUES ({placeholders})"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, values)
        conn.commit()
        return cursor.lastrowid


initialize_database()
