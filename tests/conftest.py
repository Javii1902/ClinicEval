import sys
from pathlib import Path

# Make sure `clinic_eval` is importable regardless of how pytest is invoked
# (bare `pytest`, `python -m pytest`, or the venv's own pytest.exe).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import clinic_eval.db as db
import clinic_eval.settings as settings


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    # Every test gets its own throwaway SQLite file under pytest's tmp_path -
    # never touches the real Data/clinic_eval.db.
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "clinic_eval.db")
    monkeypatch.setattr(db, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(db, "_database_initialized", False)
    db.initialize_database()
    yield db


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    yield settings


@pytest.fixture
def dashboard_app(isolated_db, isolated_settings):
    # A real (hidden) Tk app instance - the dashboard's dataset-building
    # logic reads live UI state (selected filters, etc.), so it's only
    # meaningfully testable through the actual widget, not a mock of it.
    from clinic_eval.app import ClinicEvalApp

    app = ClinicEvalApp()
    app.withdraw()

    # ClinicEvalApp.build_ui() schedules an after(100, ...) to open the Home
    # tab and refresh it. A plain update() only drains events already due -
    # it doesn't wait out that 100ms timer, so without this the callback
    # could fire in the middle of a test's own actions instead of before it,
    # producing flaky, run-order-dependent failures. Running the real event
    # loop for a bit (then quitting it) lets that timer actually fire first.
    app.after(200, app.quit)
    app.mainloop()
    app.update()

    yield app
    app.destroy()
