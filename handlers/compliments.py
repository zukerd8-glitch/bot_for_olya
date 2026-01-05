from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from database.models import get_db
from services.context_manager import context_manager
from services.ai_generator import ai_generator
from keyboards.inline import get_main_menu_keyboard

router = Router()

@router.message()
async def handle_message(message: Message):
    """Обработчик всех текстовых сообщений"""
    logger.info(f"Получено сообщение от {message.from_user.id}: {message.text[:50]}...")
    
    # Показываем индикатор набора
    typing_message = await message.answer("Думаю над комплиментом... ✨")
    
    try:
        with get_db() as db:
            # Сохраняем сообщение пользователя
            context_manager.save_message(
                telegram_user_id=message.from_user.id,
                message_text=message.text,
                is_bot=False,
                db=db
            )
            
            # Получаем историю диалога
            history = context_manager.get_dialog_history(message.from_user.id, db)
            
            # Генерируем комплимент через универсальный генератор
            compliment = await ai_generator.generate_compliment(
                message_text=message.text,
                history=history,
                compliment_type=None  # Автоматический выбор
            )
            
            # Отправляем комплимент
            await message.answer(compliment, reply_markup=get_main_menu_keyboard())
            
            # Сохраняем ответ бота
            context_manager.save_message(
                telegram_user_id=message.from_user.id,
                message_text=compliment,
                is_bot=True,
                compliment_type=None,
                db=db
            )
            
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await message.answer(
            "Произошла ошибка при генерации комплимента. Попробуй ещё раз! 💫",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        # Удаляем индикатор набора
        await typing_message.delete()
