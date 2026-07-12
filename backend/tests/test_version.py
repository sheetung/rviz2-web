from app.core.version import API_VERSION, APP_VERSION, CONFIG_VERSION, VERSION_FILE


def test_release_version_is_synchronized():
    assert VERSION_FILE.read_text(encoding="utf-8").strip() == "1.0.0"
    assert APP_VERSION == "1.0.0"
    assert API_VERSION == "v1"
    assert CONFIG_VERSION == 1
