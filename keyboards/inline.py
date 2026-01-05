from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_compliment_type_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора типа комплимента
    
    Returns:
        InlineKeyboardMarkup объект
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="💄 Внешность",
            callback_data="compliment_appearance"
        ),
        InlineKeyboardButton(
            text="🌟 Характер",
            callback_data="compliment_character"
        ),
        InlineKeyboardButton(
            text="🏆 Достижения",
            callback_data="compliment_achievements"
        ),
        InlineKeyboardButton(
            text="🎲 Случайный",
            callback_data="compliment_random"
        )
    )
    
    builder.adjust(2, 2)
    return builder.as_markup()

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создает основное меню бота
    
    Returns:
        InlineKeyboardMarkup объект
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="✨ Сделать комплимент",
            callback_data="generate_compliment"
        ),
        InlineKeyboardButton(
            text="📖 История комплиментов",
            callback_data="show_history"
        ),
        InlineKeyboardButton(
            text="🔄 Очистить историю",
            callback_data="clear_history"
        )
    )
    
    builder.adjust(1, 2)
    return builder.as_markup()
