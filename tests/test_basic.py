from app import create_app


def test_app_creation() -> None:
    app = create_app()
    assert app is not None
