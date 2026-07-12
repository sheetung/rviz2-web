from app.core.version import APP_VERSION, VERSION_FILE


def test_release_version_is_synchronized():
    assert VERSION_FILE.read_text(encoding="utf-8").strip() == "1.0.0"
    assert APP_VERSION == "1.0.0"
