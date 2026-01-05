from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session
from loguru import logger

from database.models import get_db
from services.context_manager import context_manager
from keyboards.inline import get_main_menu_keyboard, get_compliment_type_keyboard

router = Router()

class ComplimentStates(StatesGroup):
    """Состояния для генерации комплиментов"""
    waiting_for_context = State()
    choosing_type = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    
    welcome_text = (
        "✨ Привет! Я бот, который создает персонализированные комплименты для прекрасной Оли! ✨\n\n"
        "Я учитываю контекст нашего разговора, чтобы каждый комплимент был уникальным и уместным.\n\n"
        "Выбери тип комплимента или просто напиши мне что-нибудь, "
        "и я создам что-то особенное для Оли! 💖"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )
    
    # Сохраняем факт запуска бота
    with get_db() as db:
        context_manager.save_message(
            telegram_user_id=message.from_user.id,
            message_text="/start",
            is_bot=False,
            db=db
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 *Как пользоваться ботом:*\n\n"
        "1. Напиши мне любое сообщение - я создам комплимент для Оли с учётом контекста\n"
        "2. Или выбери тип комплимента из меню:\n"
        "   • 💄 *Внешность* - комплименты о внешности\n"
        "   • 🌟 *Характер* - комплименты о личных качествах\n"
        "   • 🏆 *Достижения* - комплименты об успехах\n"
        "   • 🎲 *Случайный* - комплимент любого типа\n\n"
        "3. Я запоминаю последние 10 сообщений для создания персонализированных комплиментов\n\n"
        "4. Доступные команды:\n"
        "   /start - перезапустить бота\n"
        "   /help - это сообщение\n"
        "   /history - показать историю комплиментов\n"
        "   /clear - очистить историю диалога\n\n"
        "💡 *Совет:* Чем больше контекста ты предоставишь, тем персонализированнее будет комплимент!"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("history"))
async def cmd_history(message: Message):
    """Показывает историю комплиментов"""
    with get_db() as db:
        # Получаем историю сообщений
        history = context_manager.get_dialog_history(message.from_user.id, db)
        
        if not history:
            await message.answer("История диалога пуста. Начни общение с ботом!")
            return
        
        # Фильтруем только комплименты от бота
        compliments = [msg for msg in history if msg["is_bot"]]
        
        if not compliments:
            await message.answer("Ещё не было сгенерировано ни одного комплимента!")
            return
        
        # Формируем сообщение с историей
        history_text = "📖 *История твоих комплиментов для Оли:*\n\n"
        
        for i, comp in enumerate(reversed(compliments[-10:]), 1):
            date_str = comp["created_at"].strftime("%d.%m %H:%M")
            comp_type = comp.get("compliment_type", "случайный")
            type_emoji = {
                "appearance": "💄",
                "character": "🌟",
                "achievements": "🏆",
                "random": "🎲"
            }.get(comp_type, "✨")
            
            # Обрезаем длинный текст
            comp_text = comp["text"]
            if len(comp_text) > 100:
                comp_text = comp_text[:97] + "..."
            
            history_text += f"{i}. {type_emoji} *{date_str}*:\n`{comp_text}`\n\n"
        
        await message.answer(history_text, parse_mode="Markdown")

@router.message(Command("clear"))
async def cmd_clear(message: Message):
    """Очищает историю диалога"""
    with get_db() as db:
        # Находим пользователя
        from database.models import User, Message
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        
        if user:
            # Удаляем все сообщения пользователя
            deleted_count = db.query(Message)\
                .filter(Message.user_id == user.id)\
                .delete()
            db.commit()
            
            logger.info(f"Пользователь {message.from_user.id} очистил историю ({deleted_count} сообщений)")
            await message.answer(f"✅ История диалога очищена! Удалено {deleted_count} сообщений.")
        else:
            await message.answer("У тебя ещё нет истории диалога!")

@router.callback_query(F.data == "generate_compliment")
async def process_generate_compliment(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки генерации комплимента"""
    await callback.message.answer(
        "Выбери тип комплимента для Оли:",
        reply_markup=get_compliment_type_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "show_history")
async def process_show_history(callback: CallbackQuery):
    """Обработчик кнопки показа истории"""
    await cmd_history(callback.message)
    await callback.answer()

@router.callback_query(F.data == "clear_history")
async def process_clear_history(callback: CallbackQuery):
    """Обработчик кнопки очистки истории"""
    await cmd_clear(callback.message)
    await callback.answer()
