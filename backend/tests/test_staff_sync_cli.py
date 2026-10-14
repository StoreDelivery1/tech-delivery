import io
import sys
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from app.staff_sync_cli import main


class TestStaffSyncCli(unittest.TestCase):
    def test_cli_failure_output_omits_exception_message(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["staff_sync_cli", "--apply"]):
            with patch(
                "app.staff_sync_cli.GoogleSheetsService.read_staff_rows",
                side_effect=RuntimeError("sensitive employee row and identifier"),
            ):
                with redirect_stderr(output):
                    result = main()

        self.assertEqual(result, 1)
        self.assertIn("RuntimeError", output.getvalue())
        self.assertNotIn("sensitive employee row", output.getvalue())
        self.assertNotIn("identifier", output.getvalue())


if __name__ == "__main__":
    unittest.main()
