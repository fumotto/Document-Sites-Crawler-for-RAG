import importlib

from src.app.gui import user_paths


def test_get_app_data_root_creates_expected_directory(tmp_path, monkeypatch):
    # TestID: UP-001
    monkeypatch.setattr(user_paths.Path, "home", classmethod(lambda cls: tmp_path))

    root = user_paths.get_app_data_root()

    assert root == tmp_path / "DocumentSitesCrawlerForRAG"
    assert root.exists()


def test_get_settings_path_is_under_app_data_root(tmp_path, monkeypatch):
    # TestID: UP-002
    monkeypatch.setattr(user_paths.Path, "home", classmethod(lambda cls: tmp_path))

    settings_path = user_paths.get_settings_path()

    assert settings_path == user_paths.get_app_data_root() / "settings.json"


def test_get_cache_output_archives_logs_roots_are_created(tmp_path, monkeypatch):
    # TestID: UP-003
    monkeypatch.setattr(user_paths.Path, "home", classmethod(lambda cls: tmp_path))

    cache_root = user_paths.get_cache_root()
    output_root = user_paths.get_output_root()
    archives_root = user_paths.get_archives_root()
    logs_root = user_paths.get_logs_root()

    app_root = user_paths.get_app_data_root()
    assert cache_root == app_root / "cache"
    assert output_root == app_root / "output"
    assert archives_root == app_root / "archives"
    assert logs_root == app_root / "logs"
    for path in (cache_root, output_root, archives_root, logs_root):
        assert path.exists()


def test_get_log_file_path_is_under_logs_root(tmp_path, monkeypatch):
    # TestID: UP-004
    monkeypatch.setattr(user_paths.Path, "home", classmethod(lambda cls: tmp_path))

    log_file_path = user_paths.get_log_file_path()

    assert log_file_path == user_paths.get_logs_root() / "crawler.log"
