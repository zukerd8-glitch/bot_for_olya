from aiogram import Router
from aiogram.types import ErrorEvent
from loguru import logger

router = Router()

@router.error()
async def error_handler(event: ErrorEvent):
    """
    Глобальный обработчик ошибок
    """
    logger.error(
        f"Ошибка в обработчике: {event.exception.__class__.__name__}: {event.exception}"
    )
    
    # Можно отправить сообщение пользователю
    try:
        await event.update.message.answer(
            "Произошла непредвиденная ошибка. Пожалуйста, попробуйте ещё раз позже. 🛠️"
        )
    except:
        pass  # Если нельзя отправить сообщение, просто игнорируем
