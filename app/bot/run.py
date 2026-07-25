import asyncio

from app.bot.bot import bot
from app.bot.dispatcher import dp


async def main():
    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())