import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config.settings import settings
from database.models import init_db
from handlers import commands, compliments, errors
from utils.logger import logger as app_logger

async def main():
    """Основная функция запуска бота"""
    
    # Инициализация базы данных
    init_db()
    logger.info("База данных инициализирована")
    
    # Инициализация бота
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(commands.router)
    dp.include_router(compliments.router)
    dp.include_router(errors.router)
    
    # Логирование запуска
    logger.info("Бот запущен и готов к работе!")
    
    if settings.BOT_ADMIN_ID:
        try:
            await bot.send_message(
                settings.BOT_ADMIN_ID,
                "🤖 Бот с комплиментами для Оли запущен и готов к работе!"
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение админу: {e}")
    
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
