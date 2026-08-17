import asyncio
import logging

from app.bot.bot import bot
from app.bot.dispatcher import dp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Bot starting...")
    await dp.start_polling(bot)
    logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())