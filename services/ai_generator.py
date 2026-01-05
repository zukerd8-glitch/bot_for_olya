import json
from typing import List, Optional, Dict, Any
from openai import OpenAI, APIConnectionError, APIError, RateLimitError
from loguru import logger

from config.settings import settings
from utils.fallback_generator import fallback_generator

class AIGenerator:
    """Класс для генерации комплиментов с использованием OpenAI API"""
    
    def __init__(self):
        self.client = None
        self.use_openai = bool(settings.OPENAI_API_KEY)
        
        if self.use_openai:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI клиент инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации OpenAI: {e}")
                self.use_openai = False
        
        self.compliment_types = {
            "appearance": "комплимент о внешности",
            "character": "комплимент о характере и личных качествах",
            "achievements": "комплимент о достижениях и успехах"
        }
    
    async def generate_compliment(self,
                                 message_text: str,
                                 history: List[Dict[str, Any]],
                                 compliment_type: Optional[str] = None) -> str:
        """
        Генерирует персонализированный комплимент для Оли
        
        Args:
            message_text: текущее сообщение пользователя
            history: история диалога
            compliment_type: желаемый тип комплимента
        
        Returns:
            Сгенерированный комплимент
        """
        # Используем OpenAI если доступно
        if self.use_openai and self.client:
            try:
                return await self._generate_with_openai(message_text, history, compliment_type)
            except (APIConnectionError, APIError, RateLimitError) as e:
                logger.error(f"Ошибка OpenAI API: {e}")
                logger.info("Использую fallback генератор")
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")
        
        # Fallback на локальный генератор
        return self._generate_fallback(message_text, history, compliment_type)
    
    async def _generate_with_openai(self,
                                   message_text: str,
                                   history: List[Dict[str, Any]],
                                   compliment_type: Optional[str] = None) -> str:
        """Генерация комплимента с использованием OpenAI"""
        
        # Формируем системный промпт
        system_prompt = """Ты - друг, который умеет делать красивые, искренние и персонализированные комплименты 
        девушке по имени Оля. Твои комплименты должны быть:
        1. Персонализированными с учетом контекста разговора
        2. Искренними и естественными
        3. Теплыми и доброжелательными
        4. Не слишком длинными (1-3 предложения)
        
        Всегда обращайся к Оле по имени и используй местоимение "ты".
        Избегай шаблонных фраз, делай комплименты уникальными."""
        
        # Добавляем информацию о типе комплимента
        if compliment_type and compliment_type in self.compliment_types:
            system_prompt += f"\n\nПользователь хочет получить {self.compliment_types[compliment_type]}."
        
        # Формируем историю диалога для контекста
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем историю диалога (последние N сообщений)
        for msg in history[-settings.CONTEXT_MEMORY_SIZE:]:
            role = "assistant" if msg["is_bot"] else "user"
            messages.append({"role": role, "content": msg["text"]})
        
        # Добавляем текущее сообщение
        messages.append({"role": "user", "content": message_text})
        
        # Делаем запрос к OpenAI
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=150,
                n=1
            )
            
            compliment = response.choices[0].message.content.strip()
            
            # Убедимся, что обращаемся к Оле
            if not any(name in compliment.lower() for name in ["оля", "оленька", "олечка"]):
                compliment = f"Оля, {compliment.lower()}"
            
            logger.debug(f"Сгенерирован комплимент через OpenAI: {compliment[:50]}...")
            return compliment
            
        except Exception as e:
            logger.error(f"Ошибка при запросе к OpenAI: {e}")
            raise
    
    def _generate_fallback(self,
                          message_text: str,
                          history: List[Dict[str, Any]],
                          compliment_type: Optional[str] = None) -> str:
        """Генерация комплимента через fallback систему"""
        
        # Извлекаем текст последних сообщений для контекста
        context_texts = [msg["text"] for msg in history[-5:]]
        
        # Генерируем комплимент через fallback генератор
        compliment = fallback_generator.generate_compliment(
            compliment_type=compliment_type,
            context=context_texts
        )
        
        logger.debug(f"Сгенерирован fallback комплимент: {compliment[:50]}...")
        return compliment

# Создаем глобальный экземпляр генератора
ai_generator = AIGenerator()
