import asyncio
import logging

from app.bot.bot import bot
from app.bot.dispatcher import dp
from app.services.staff_sync_scheduler import start_staff_sync_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Bot starting...")
    scheduler = start_staff_sync_scheduler()
    try:
        await dp.start_polling(bot)
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)
            logger.info("Staff sync scheduler stopped.")
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())