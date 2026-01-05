import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger

from config.settings import settings

class OpenRouterGenerator:
    """Генератор комплиментов с использованием OpenRouter API"""
    
    def __init__(self):
        self.client = None
        self.use_openrouter = bool(settings.OPENROUTER_API_KEY)
        
        if self.use_openrouter:
            try:
                # OpenRouter совместим с OpenAI SDK, но требует особых заголовков
                self.client = OpenAI(
                    base_url=settings.OPENROUTER_BASE_URL,
                    api_key=settings.OPENROUTER_API_KEY,
                    default_headers={
                        "HTTP-Referer": "https://github.com/your-repo",  # Ваш сайт/репозиторий
                        "X-Title": "Olya Compliments Bot",  # Название вашего приложения
                    }
                )
                logger.info("OpenRouter клиент инициализирован")
                
                # Проверяем доступность модели
                self.available_models = self._get_available_models()
                
            except Exception as e:
                logger.error(f"Ошибка инициализации OpenRouter: {e}")
                self.use_openrouter = False
    
    def _get_available_models(self) -> List[str]:
        """Получает список доступных моделей"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.warning(f"Не удалось получить список моделей: {e}")
            # Возвращаем популярные модели по умолчанию
            return [
                "openai/gpt-3.5-turbo",
                "openai/gpt-4",
                "anthropic/claude-3-haiku",
                "meta-llama/llama-3-70b-instruct"
            ]
    
    def _select_best_model(self) -> str:
        """Выбирает лучшую доступную модель"""
        preferred_models = [
            settings.OPENROUTER_MODEL,
            "openai/gpt-3.5-turbo",  # Недорогая и быстрая
            "anthropic/claude-3-haiku",  # Дешевая модель от Anthropic
            "google/gemini-pro",  # Альтернатива от Google
            "meta-llama/llama-3-8b-instruct"  # Бесплатная опция
        ]
        
        for model in preferred_models:
            if model in self.available_models:
                return model
        
        # Если ничего не найдено, возвращаем первую доступную
        return self.available_models[0] if self.available_models else settings.OPENROUTER_MODEL
    
    async def generate_compliment(self,
                                 message_text: str,
                                 history: List[Dict[str, Any]],
                                 compliment_type: Optional[str] = None) -> str:
        """Генерирует комплимент через OpenRouter"""
        if not self.use_openrouter or not self.client:
            raise RuntimeError("OpenRouter не доступен")
        
        try:
            # Выбираем модель
            model = self._select_best_model()
            
            # Строим промпт
            messages = self._build_messages(message_text, history, compliment_type)
            
            # Делаем запрос
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            compliment = response.choices[0].message.content.strip()
            compliment = self._post_process_compliment(compliment)
            
            logger.debug(f"Сгенерирован комплимент через {model}: {compliment[:50]}...")
            
            # Логируем использование (для мониторинга стоимости)
            self._log_usage(response.usage, model)
            
            return compliment
            
        except Exception as e:
            logger.error(f"Ошибка OpenRouter API: {e}")
            raise
    
    def _build_messages(self,
                       message_text: str,
                       history: List[Dict[str, Any]],
                       compliment_type: Optional[str] = None) -> List[Dict[str, str]]:
        """Строит список сообщений для запроса"""
        
        # Системный промпт
        system_prompt = self._create_system_prompt(compliment_type)
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем историю
        for msg in history[-min(8, len(history)):]:  # Максимум 8 сообщений истории
            role = "assistant" if msg["is_bot"] else "user"
            messages.append({"role": role, "content": msg["text"]})
        
        # Добавляем текущее сообщение
        messages.append({"role": "user", "content": message_text})
        
        return messages
    
    def _create_system_prompt(self, compliment_type: Optional[str] = None) -> str:
        """Создает системный промпт"""
        
        prompt = """Ты - бот, который делает искренние, персонализированные комплименты девушке по имени Оля.

Твоя задача:
1. Создавать уникальные комплименты, учитывая контекст разговора
2. Быть искренним, теплым и дружелюбным
3. Делать комплименты конкретными, избегая общих фраз
4. Использовать имя "Оля" в каждом комплименте
5. Делать комплименты не слишком длинными (1-3 предложения)

Примеры хороших комплиментов:
- "Оля, сегодня твоя улыбка особенно лучезарна! Заметил, как она поднимает настроение всем вокруг."
- "Мне очень нравится, как ты поддерживаешь друзей, Оля. Твоя эмпатия - редкое качество!"
- "Оля, твои успехи в работе впечатляют! Видно, как много усилий ты вкладываешь."

Примеры ПЛОХИХ комплиментов (не делай так):
- "Ты красивая." (слишком общее)
- "У тебя хороший характер." (не конкретно)
- Комплимент без упоминания имени Оля."""

        # Добавляем специфику типа комплимента
        if compliment_type == "appearance":
            prompt += "\n\nСейчас сделай комплимент о внешности Оли. Обрати внимание на детали, но будь тактичным."
        elif compliment_type == "character":
            prompt += "\n\nСейчас сделай комплимент о характере Оли. Отметь её внутренние качества."
        elif compliment_type == "achievements":
            prompt += "\n\nСейчас сделай комплимент о достижениях Оли. Подчеркни её успехи и усилия."
        
        return prompt
    
    def _post_process_compliment(self, compliment: str) -> str:
        """Пост-обработка сгенерированного комплимента"""
        
        # Удаляем лишние кавычки и форматирование
        compliment = compliment.strip('"\' ')
        
        # Убеждаемся, что обращаемся к Оле
        if not any(name in compliment.lower() for name in ["оля", "оленька", "олечка"]):
            # Добавляем обращение в начало
            sentences = compliment.split('. ')
            if sentences:
                sentences[0] = f"Оля, {sentences[0].lower()}"
                compliment = '. '.join(sentences)
        
        # Добавляем эмодзи для эмоциональности
        emojis = ["💖", "✨", "🌟", "🌸", "💫", "💕"]
        import random
        if random.random() > 0.5:  # 50% шанс добавить эмодзи
            compliment += f" {random.choice(emojis)}"
        
        return compliment
    
    def _log_usage(self, usage, model: str):
        """Логирует использование токенов для мониторинга стоимости"""
        if usage:
            logger.info(
                f"OpenRouter использование | Модель: {model} | "
                f"Токены: {usage.total_tokens} (вход: {usage.prompt_tokens}, выход: {usage.completion_tokens})"
            )

# Глобальный экземпляр
openrouter_generator = OpenRouterGenerator()
