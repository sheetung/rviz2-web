from app.main import app


def test_interactive_api_docs_are_disabled():
    assert app.docs_url is None
    assert app.redoc_url is None
