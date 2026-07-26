from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.bot.bot import bot


class NotificationService:

    @staticmethod
    async def send_message(
        telegram_id: int,
        text: str,
        **kwargs,
    ) -> bool:
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                **kwargs,
            )
            return True

        except TelegramBadRequest:
            return False

        except Exception as e:
            print(
                f"Notification error: {e}"
            )
            return False

    @staticmethod
    async def edit_message(
        chat_id: int,
        message_id: int,
        text: str,
        **kwargs,
    ) -> bool:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                **kwargs,
            )
            return True

        except TelegramBadRequest:
            return False

        except Exception as e:
            print(
                f"Edit message error: {e}"
            )
            return False

    @staticmethod
    async def delete_message(
        chat_id: int,
        message_id: int,
    ) -> bool:
        try:
            await bot.delete_message(
                chat_id=chat_id,
                message_id=message_id,
            )
            return True

        except TelegramBadRequest:
            return False

        except Exception as e:
            print(
                f"Delete message error: {e}"
            )
            return False