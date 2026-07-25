import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.dispatcher import dp
from app.core.config import settings


async def main():
    print("🚀 Bot is starting...")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    print("✅ Bot created")
    print("▶️ Start polling...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())