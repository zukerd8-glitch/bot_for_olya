import asyncio
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from database.models import get_db
from services.context_manager import context_manager
from services.ai_generator import ai_generator
from keyboards.inline import get_main_menu_keyboard, get_compliment_type_keyboard

router = Router()

@router.message()
async def handle_message(message: Message):
    """
    Обработчик всех текстовых сообщений
    Генерирует комплимент на основе полученного текста
    """
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
            
            # Генерируем комплимент
            compliment = await ai_generator.generate_compliment(
                message_text=message.text,
                history=history,
                compliment_type=None  # Автоматический выбор типа
            )
            
            # Отправляем комплимент
            await message.answer(compliment, reply_markup=get_main_menu_keyboard())
            
            # Сохраняем ответ бота
            context_manager.save_message(
                telegram_user_id=message.from_user.id,
                message_text=compliment,
                is_bot=True,
                compliment_type=None,  # Можно добавить определение типа
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

@router.callback_query(F.data.startswith("compliment_"))
async def process_compliment_type(callback: CallbackQuery):
    """
    Обработчик выбора типа комплимента
    """
    compliment_type = callback.data.replace("compliment_", "")
    
    # Маппинг типов
    type_mapping = {
        "appearance": "💄 Внешность",
        "character": "🌟 Характер", 
        "achievements": "🏆 Достижения",
        "random": "🎲 Случайный"
    }
    
    selected_type = type_mapping.get(compliment_type, "случайный")
    
    # Отправляем подтверждение
    await callback.message.answer(
        f"Отлично! Генерирую комплимент про *{selected_type}* для Оли...\n\n"
        f"Можешь отправить дополнительный контекст или просто написать любое сообщение 💫",
        parse_mode="Markdown"
    )
    
    # Сохраняем выбор типа в состоянии или базе
    with get_db() as db:
        context_manager.save_message(
            telegram_user_id=callback.from_user.id,
            message_text=f"Выбран тип комплимента: {selected_type}",
            is_bot=False,
            db=db
        )
    
    await callback.answer(f"Выбран тип: {selected_type}")
