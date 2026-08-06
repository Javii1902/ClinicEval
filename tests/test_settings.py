def test_default_compliance_threshold_is_100(isolated_settings):
    assert isolated_settings.get_compliance_threshold() == 100


def test_set_and_get_compliance_threshold(isolated_settings):
    isolated_settings.set_compliance_threshold(90)
    assert isolated_settings.get_compliance_threshold() == 90


def test_settings_persist_across_reloads(isolated_settings):
    isolated_settings.set_compliance_threshold(85)
    reloaded = isolated_settings.load_settings()
    assert reloaded["compliance_threshold"] == 85


def test_corrupt_settings_file_falls_back_to_default(isolated_settings):
    isolated_settings.SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    isolated_settings.SETTINGS_PATH.write_text("{not valid json", encoding="utf-8")
    assert isolated_settings.get_compliance_threshold() == 100


def test_missing_settings_file_returns_defaults(isolated_settings):
    assert not isolated_settings.SETTINGS_PATH.exists()
    settings_dict = isolated_settings.load_settings()
    assert settings_dict == {"compliance_threshold": 100}
