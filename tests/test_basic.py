import unittest

from app import create_app
from app.services.attendance_service import _build_connection_string


class AppTests(unittest.TestCase):
    def test_app_creation(self) -> None:
        app = create_app()
        self.assertIsNotNone(app)

    def test_build_connection_string_escapes_special_characters(self) -> None:
        conn_str = _build_connection_string(
            {
                "DB_DRIVER": "ODBC Driver 18 for SQL Server",
                "DB_SERVER": "113.176.95.32,8089",
                "DB_DATABASE": "CJ_AGRI_ATT_2022",
                "DB_UID": "livestock",
                "DB_PWD": "pa;ss}word",
                "DB_ENCRYPT": "yes",
                "DB_TRUST_CERT": "yes",
                "DB_TIMEOUT": 10,
            }
        )

        self.assertIn("PWD={pa;ss}}word};", conn_str)
