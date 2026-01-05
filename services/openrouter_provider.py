import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger

from config.settings import settings


class OpenRouterProvider:
    """Провайдер для OpenRouter API"""
    
    def __init__(self):
        self.client = None
        self.available = False
        self.model = settings.OPENROUTER_MODEL
        
        if settings.OPENROUTER_API_KEY:
            self._initialize_client()
        else:
            logger.warning("OpenRouter API ключ не указан")
    
    def _initialize_client(self):
        """Инициализирует клиент OpenRouter"""
        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
                default_headers={
                    "HTTP-Referer": "https://github.com/your-username/olya-bot",
                    "X-Title": "Olya Compliments Bot",
                },
            )
            
            # Тестовый запрос для проверки подключения
            models = self.client.models.list()
            logger.info(f"✅ OpenRouter подключен. Доступно моделей: {len(models.data)}")
            
            # Проверяем доступность выбранной модели
            available_models = [m.id for m in models.data]
            if self.model not in available_models:
                logger.warning(f"Модель {self.model} недоступна. Доступные: {available_models[:3]}...")
                # Выбираем доступную модель
                for preferred in ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku", "google/gemini-pro"]:
                    if preferred in available_models:
                        self.model = preferred
                        break
            
            self.available = True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации OpenRouter: {e}")
            self.available = False
    
    def is_available(self) -> bool:
        """Проверяет доступность провайдера"""
        return self.available
    
    async def generate_compliment(self,
                                 message_text: str,
                                 history: List[Dict[str, Any]],
                                 compliment_type: Optional[str] = None) -> str:
        """
        Генерирует комплимент через OpenRouter
        
        Args:
            message_text: текущее сообщение пользователя
            history: история диалога
            compliment_type: тип комплимента
            
        Returns:
            Сгенерированный комплимент
        """
        if not self.available or not self.client:
            raise RuntimeError("OpenRouter провайдер не доступен")
        
        try:
            # Формируем промпт
            messages = self._build_messages(message_text, history, compliment_type)
            
            # Делаем запрос
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150,
                top_p=0.9
            )
            
            compliment = response.choices[0].message.content.strip()
            
            # Пост-обработка
            compliment = self._post_process_compliment(compliment)
            
            # Логируем использование
            if hasattr(response, 'usage'):
                self._log_usage(response.usage)
            
            logger.debug(f"OpenRouter сгенерировал: {compliment[:50]}...")
            return compliment
            
        except Exception as e:
            logger.error(f"Ошибка OpenRouter: {e}")
            raise
    
    def _build_messages(self,
                       message_text: str,
                       history: List[Dict[str, Any]],
                       compliment_type: Optional[str] = None) -> List[Dict[str, str]]:
        """Строит список сообщений для промпта"""
        
        system_prompt = """Ты делаешь искренние, персонализированные комплименты девушке по имени Оля.
        
        Правила:
        1. Всегда обращайся к "Оля" или "Олечка"
        2. Будь конкретным, избегай общих фраз
        3. Учитывай контекст разговора
        4. Будь теплым и дружелюбным
        5. 1-3 предложения, не больше
        
        Пример хорошего комплимента: "Оля, сегодня твоя улыбка особенно лучезарна! Заметил, как она поднимает настроение всем вокруг.""""
        
        if compliment_type == "appearance":
            system_prompt += "\nСделай комплимент о внешности Оли."
        elif compliment_type == "character":
            system_prompt += "\nСделай комплимент о характере Оли."
        elif compliment_type == "achievements":
            system_prompt += "\nСделай комплимент о достижениях Оли."
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем историю (последние 5 сообщений)
        for msg in history[-5:]:
            role = "assistant" if msg["is_bot"] else "user"
            messages.append({"role": role, "content": msg["text"]})
        
        # Добавляем текущее сообщение
        messages.append({"role": "user", "content": message_text})
        
        return messages
    
    def _post_process_compliment(self, compliment: str) -> str:
        """Пост-обработка сгенерированного текста"""
        # Удаляем лишние кавычки
        compliment = compliment.strip('"\'')
        
        # Убеждаемся, что обращаемся к Оле
        if not any(name in compliment.lower() for name in ["оля", "оленька", "олечка"]):
            # Добавляем обращение
            sentences = compliment.split('. ')
            if sentences and sentences[0]:
                sentences[0] = f"Оля, {sentences[0].lower()}"
                compliment = '. '.join(sentences)
        
        return compliment
    
    def _log_usage(self, usage):
        """Логирует использование токенов"""
        if usage:
            logger.info(
                f"OpenRouter использование | "
                f"Токены: {usage.total_tokens} (вход: {usage.prompt_tokens}, выход: {usage.completion_tokens})"
            )
    
    def get_info(self) -> Dict[str, Any]:
        """Возвращает информацию о провайдере"""
        return {
            'type': 'api',
            'status': 'available' if self.available else 'unavailable',
            'model': self.model,
            'description': 'OpenRouter API с доступом к множеству моделей'
        }


# Глобальный экземпляр
openrouter_provider = OpenRouterProvider()
