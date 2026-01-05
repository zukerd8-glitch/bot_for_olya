from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger

from database.models import Message, User, get_db

class ContextManager:
    """Управление контекстом диалога"""
    
    def __init__(self):
        self.max_history_size = 10
    
    def get_dialog_history(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        Получает историю диалога для пользователя
        
        Args:
            user_id: ID пользователя в базе данных
            db: сессия базы данных
        
        Returns:
            Список сообщений в формате словарей
        """
        try:
            messages = db.query(Message)\
                .filter(Message.user_id == user_id)\
                .order_by(Message.created_at.desc())\
                .limit(self.max_history_size)\
                .all()
            
            # Преобразуем в нужный формат (от старых к новым)
            history = []
            for msg in reversed(messages):
                history.append({
                    "text": msg.text,
                    "is_bot": msg.is_bot,
                    "compliment_type": msg.compliment_type,
                    "created_at": msg.created_at
                })
            
            logger.debug(f"Загружено {len(history)} сообщений из истории пользователя {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории диалога: {e}")
            return []
    
    def save_message(self, 
                    telegram_user_id: int,
                    message_text: str,
                    is_bot: bool = False,
                    compliment_type: Optional[str] = None,
                    db: Session = None) -> None:
        """
        Сохраняет сообщение в базу данных
        
        Args:
            telegram_user_id: ID пользователя в Telegram
            message_text: текст сообщения
            is_bot: флаг, является ли отправитель ботом
            compliment_type: тип комплимента (если есть)
            db: сессия базы данных (если None, создаст новую)
        """
        try:
            if db is None:
                with get_db() as db_session:
                    self._save_message_internal(
                        telegram_user_id, message_text, is_bot, compliment_type, db_session
                    )
            else:
                self._save_message_internal(
                    telegram_user_id, message_text, is_bot, compliment_type, db
                )
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения: {e}")
    
    def _save_message_internal(self,
                              telegram_user_id: int,
                              message_text: str,
                              is_bot: bool,
                              compliment_type: Optional[str],
                              db: Session) -> None:
        """Внутренний метод сохранения сообщения"""
        # Находим или создаем пользователя
        user = db.query(User).filter(User.telegram_id == telegram_user_id).first()
        if not user:
            user = User(telegram_id=telegram_user_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Сохраняем сообщение
        message = Message(
            user_id=user.id,
            text=message_text,
            is_bot=is_bot,
            compliment_type=compliment_type
        )
        db.add(message)
        db.commit()
        
        logger.debug(f"Сохранено сообщение от {'бота' if is_bot else 'пользователя'} для user_id={telegram_user_id}")
    
    def cleanup_old_messages(self, db: Session, days_to_keep: int = 30):
        """
        Очищает старые сообщения из базы данных
        
        Args:
            db: сессия базы данных
            days_to_keep: сколько дней хранить сообщения
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Удаляем старые сообщения
            deleted_count = db.query(Message)\
                .filter(Message.created_at < cutoff_date)\
                .delete()
            
            db.commit()
            logger.info(f"Удалено {deleted_count} старых сообщений (старше {days_to_keep} дней)")
            
        except Exception as e:
            logger.error(f"Ошибка при очистке старых сообщений: {e}")
            db.rollback()

# Глобальный экземпляр менеджера контекста
context_manager = ContextManager()
