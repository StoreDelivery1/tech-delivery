import json
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    @classmethod
    def read_staff_rows(cls) -> list[list[str]]:
        if not settings.GOOGLE_SPREADSHEET_ID:
            raise ValueError("GOOGLE_SPREADSHEET_ID is not configured")
        if not settings.GOOGLE_SHEET_NAME:
            raise ValueError("GOOGLE_SHEET_NAME is not configured")
        if not settings.GOOGLE_APPLICATION_CREDENTIALS:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is not configured")

        credentials_path = Path(settings.GOOGLE_APPLICATION_CREDENTIALS).expanduser()
        credentials_exists = credentials_path.is_file()
        credentials_size = credentials_path.stat().st_size if credentials_exists else None
        logger.info(
            "Service Account file diagnostics: exists=%s size_bytes=%s empty=%s",
            credentials_exists,
            credentials_size,
            credentials_size == 0 if credentials_size is not None else None,
        )

        if not credentials_exists:
            raise ValueError(
                "Service Account JSON was not found. Check GOOGLE_APPLICATION_CREDENTIALS."
            )

        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        try:
            credentials = Credentials.from_service_account_file(
                str(credentials_path),
                scopes=cls.SCOPES,
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Service Account JSON is invalid "
                f"(line={exc.lineno}, column={exc.colno}, reason={exc.msg})"
            ) from exc
        except Exception as exc:
            logger.error(
                "Service Account credential load failed (%s)",
                type(exc).__name__,
            )
            raise RuntimeError("Service Account credentials could not be loaded") from None
        worksheet = settings.GOOGLE_SHEET_NAME.replace("'", "''")
        requested_range = f"'{worksheet}'!A:G"

        try:
            sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
            response = (
                sheets.spreadsheets()
                .values()
                .get(
                    spreadsheetId=settings.GOOGLE_SPREADSHEET_ID,
                    range=requested_range,
                    valueRenderOption="UNFORMATTED_VALUE",
                )
                .execute()
            )
        except Exception as exc:
            logger.error("Google Sheets read failed (%s)", type(exc).__name__)
            raise RuntimeError("Google Sheets read failed") from None

        return response.get("values", [])