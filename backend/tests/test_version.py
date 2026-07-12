from app.core.version import APP_VERSION, VERSION_FILE


def test_release_version_is_synchronized():
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    assert version
    assert APP_VERSION == version
