import tempfile
import unittest
from unittest.mock import patch

from app.core.config import settings
from app.services.google_sheets_service import GoogleSheetsService


class TestGoogleSheetsService(unittest.TestCase):
    def test_credential_load_error_hides_path_and_exception_text(self):
        with tempfile.NamedTemporaryFile() as credentials_file:
            with (
                patch.object(settings, "GOOGLE_SPREADSHEET_ID", "test-sheet"),
                patch.object(settings, "GOOGLE_SHEET_NAME", "Staff"),
                patch.object(settings, "GOOGLE_APPLICATION_CREDENTIALS", credentials_file.name),
                patch(
                    "google.oauth2.service_account.Credentials.from_service_account_file",
                    side_effect=RuntimeError("private credential details"),
                ),
                self.assertLogs("app.services.google_sheets_service", level="INFO") as logs,
            ):
                with self.assertRaisesRegex(RuntimeError, "credentials could not be loaded") as raised:
                    GoogleSheetsService.read_staff_rows()

        self.assertNotIn("private credential details", str(raised.exception))
        self.assertNotIn(credentials_file.name, " ".join(logs.output))
        self.assertNotIn("private credential details", " ".join(logs.output))

    def test_api_error_is_not_exposed_in_logs_or_exception(self):
        with tempfile.NamedTemporaryFile() as credentials_file:
            with (
                patch.object(settings, "GOOGLE_SPREADSHEET_ID", "test-sheet"),
                patch.object(settings, "GOOGLE_SHEET_NAME", "Staff"),
                patch.object(settings, "GOOGLE_APPLICATION_CREDENTIALS", credentials_file.name),
                patch(
                    "google.oauth2.service_account.Credentials.from_service_account_file",
                    return_value=object(),
                ),
                patch(
                    "googleapiclient.discovery.build",
                    side_effect=RuntimeError("private spreadsheet response"),
                ),
                self.assertLogs("app.services.google_sheets_service", level="INFO") as logs,
            ):
                with self.assertRaisesRegex(RuntimeError, "Google Sheets read failed") as raised:
                    GoogleSheetsService.read_staff_rows()

        self.assertNotIn("private spreadsheet response", str(raised.exception))
        self.assertNotIn(credentials_file.name, " ".join(logs.output))
        self.assertNotIn("private spreadsheet response", " ".join(logs.output))


if __name__ == "__main__":
    unittest.main()
