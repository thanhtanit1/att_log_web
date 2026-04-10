import unittest
from datetime import datetime
from unittest.mock import patch

from app import create_app
from app.services.attendance_service import _build_connection_string


class AppTests(unittest.TestCase):
    def test_app_creation(self) -> None:
        app = create_app()
        self.assertIsNotNone(app)

    def test_index_defaults_filter_dates_to_today(self) -> None:
        app = create_app()
        today = datetime.now().strftime("%Y-%m-%d")

        with app.test_client() as client:
            with patch(
                "app.routes.main.get_dashboard_data",
                return_value=([], [], [], 0, False, None),
            ) as mocked_get_dashboard_data:
                response = client.get("/")

        self.assertEqual(response.status_code, 200)
        mocked_get_dashboard_data.assert_called_once_with(
            page=1,
            page_size=app.config["PAGE_SIZE"],
            devname="all",
            start_date=today,
            end_date=today,
        )
        page_html = response.get_data(as_text=True)
        self.assertIn(f'value="{today}"', page_html)
        self.assertIn("Today", page_html)
        self.assertIn("Xóa lọc", page_html)

    def test_index_keeps_user_selected_filter_dates(self) -> None:
        app = create_app()

        with app.test_client() as client:
            with patch(
                "app.routes.main.get_dashboard_data",
                return_value=([], [], [], 0, False, None),
            ) as mocked_get_dashboard_data:
                response = client.get("/?start_date=2026-04-01&end_date=2026-04-09")

        self.assertEqual(response.status_code, 200)
        mocked_get_dashboard_data.assert_called_once_with(
            page=1,
            page_size=app.config["PAGE_SIZE"],
            devname="all",
            start_date="2026-04-01",
            end_date="2026-04-09",
        )

    def test_index_renders_error_message_when_dashboard_fails(self) -> None:
        app = create_app()

        with app.test_client() as client:
            with patch(
                "app.routes.main.get_dashboard_data",
                return_value=([], [], [], 0, False, "DB connection failed"),
            ):
                response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("DB connection failed", response.get_data(as_text=True))

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
