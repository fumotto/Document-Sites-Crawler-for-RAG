import json

from src.app.gui import settings_store


def test_save_then_load_round_trips_values(tmp_path, monkeypatch):
    # TestID: SS-001
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(settings_store, "get_settings_path", lambda: settings_path)

    settings_store.save_settings({"urls_text": "https://a.com", "mode": "full"})
    loaded = settings_store.load_settings()

    assert loaded["urls_text"] == "https://a.com"
    assert loaded["mode"] == "full"


def test_missing_settings_file_returns_defaults(tmp_path, monkeypatch):
    # TestID: SS-002
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(settings_store, "get_settings_path", lambda: settings_path)

    loaded = settings_store.load_settings()

    assert loaded == settings_store.DEFAULT_SETTINGS


def test_corrupt_json_falls_back_to_defaults(tmp_path, monkeypatch):
    # TestID: SS-003
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(settings_store, "get_settings_path", lambda: settings_path)

    loaded = settings_store.load_settings()

    assert loaded == settings_store.DEFAULT_SETTINGS


def test_partial_settings_are_merged_with_defaults(tmp_path, monkeypatch):
    # TestID: SS-004
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps({"urls_text": "https://only-this.com"}), encoding="utf-8")
    monkeypatch.setattr(settings_store, "get_settings_path", lambda: settings_path)

    loaded = settings_store.load_settings()

    assert loaded["urls_text"] == "https://only-this.com"
    for key in settings_store.DEFAULT_SETTINGS:
        assert key in loaded
