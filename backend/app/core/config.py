import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "",
    )

    ALGORITHM: str = os.getenv(
        "ALGORITHM",
        "HS256",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "60",
        )
    )

    BOT_TOKEN: str = os.getenv(
        "BOT_TOKEN",
        "",
    )


    GOOGLE_SPREADSHEET_ID: str = (
        os.getenv("GOOGLE_SPREADSHEET_ID")
        or os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    )

    GOOGLE_SHEET_NAME: str = (
        os.getenv("GOOGLE_SHEET_NAME")
        or os.getenv("GOOGLE_SHEETS_WORKSHEET", "")
    )

    GOOGLE_SHEETS_SPREADSHEET_ID: str = GOOGLE_SPREADSHEET_ID
    GOOGLE_SHEETS_WORKSHEET: str = GOOGLE_SHEET_NAME

    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        "credentials/google-sheets-service-account.json",
    )

    STAFF_SYNC_HOUR: int = int(os.getenv("STAFF_SYNC_HOUR", "3"))
    STAFF_SYNC_MINUTE: int = int(os.getenv("STAFF_SYNC_MINUTE", "15"))
    STAFF_SYNC_TIMEZONE: str = os.getenv("STAFF_SYNC_TIMEZONE", "Europe/Kyiv")

settings = Settings()