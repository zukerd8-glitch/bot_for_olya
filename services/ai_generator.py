import asyncio
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from config.settings import settings
from utils.fallback_generator import fallback_generator

# Импорты провайдеров (с обработкой ошибок импорта)
try:
    from services.openai_provider import openai_provider
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI провайдер не доступен")

try:
    from services.openrouter_provider import openrouter_provider
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False
    logger.warning("OpenRouter провайдер не доступен")

try:
    from services.together_provider import together_provider
    TOGETHER_AVAILABLE = True
except ImportError:
    TOGETHER_AVAILABLE = False
    logger.warning("Together AI провайдер не доступен")


class AIGenerator:
    """Универсальный генератор с поддержкой всех провайдеров"""
    
    def __init__(self):
        self.providers: List[Tuple[str, Any]] = []
        self._init_providers()
        logger.info(f"Инициализированы провайдеры: {[p[0] for p in self.providers]}")
    
    def _init_providers(self):
        """Инициализирует провайдеры в порядке приоритета"""
        
        # Определяем порядок приоритета из настроек
        priority_order = getattr(settings, 'AI_PROVIDER_PRIORITY', 
                               ['openrouter', 'openai', 'together', 'fallback'])
        
        # Словарь доступных провайдеров
        available_providers = {}
        
        # OpenRouter
        if (OPENROUTER_AVAILABLE and 
            settings.OPENROUTER_API_KEY and 
            openrouter_provider.is_available()):
            available_providers['openrouter'] = openrouter_provider
        
        # OpenAI
        if (OPENAI_AVAILABLE and 
            settings.OPENAI_API_KEY and 
            openai_provider.is_available()):
            available_providers['openai'] = openai_provider
        
        # Together AI
        if (TOGETHER_AVAILABLE and 
            settings.TOGETHER_API_KEY and 
            settings.USE_TOGETHER_AI and 
            together_provider.is_available()):
            available_providers['together'] = together_provider
        
        # Fallback (всегда доступен)
        available_providers['fallback'] = fallback_generator
        
        # Сортируем провайдеры по приоритету
        for provider_name in priority_order:
            if provider_name in available_providers:
                self.providers.append((provider_name, available_providers[provider_name]))
                logger.info(f"Добавлен провайдер: {provider_name}")
        
        # Если нет провайдеров, добавляем только fallback
        if len(self.providers) == 0:
            self.providers.append(('fallback', fallback_generator))
            logger.warning("Нет доступных AI провайдеров, использую только fallback")
    
    async def generate_compliment(self,
                                 message_text: str,
                                 history: List[Dict[str, Any]],
                                 compliment_type: Optional[str] = None) -> str:
        """
        Генерирует комплимент, пробуя провайдеров по очереди
        
        Args:
            message_text: текущее сообщение пользователя
            history: история диалога
            compliment_type: тип комплимента
            
        Returns:
            Сгенерированный комплимент
        """
        
        # Статистика использования
        stats = {"attempts": 0, "success": False}
        
        for provider_name, provider in self.providers:
            stats["attempts"] += 1
            
            try:
                logger.debug(f"Пробую генерацию через {provider_name}")
                
                if provider_name == 'fallback':
                    # Fallback генератор синхронный
                    compliment = provider.generate_compliment(
                        compliment_type=compliment_type,
                        context=[msg["text"] for msg in history[-5:]]
                    )
                else:
                    # AI провайдеры асинхронные
                    compliment = await provider.generate_compliment(
                        message_text=message_text,
                        history=history,
                        compliment_type=compliment_type
                    )
                
                logger.info(f"✅ Успешная генерация через {provider_name}")
                stats["success"] = True
                stats["provider"] = provider_name
                
                # Сохраняем статистику
                self._log_statistics(stats, provider_name, compliment)
                
                return compliment
                
            except Exception as e:
                logger.warning(f"❌ Провайдер {provider_name} не сработал: {str(e)[:100]}")
                
                # Если это не последний провайдер, пробуем следующий
                if provider_name != self.providers[-1][0]:
                    logger.info(f"Пробую следующий провайдер...")
                    continue
                else:
                    # Если это последний провайдер (fallback), то он не должен падать
                    if provider_name == 'fallback':
                        logger.error("Даже fallback генератор не сработал!")
                        raise
        
        # Если дошли сюда, что-то пошло не так
        logger.error("Все провайдеры провалились")
        return "Оля, ты сегодня прекрасна! 💖"
    
    def _log_statistics(self, stats: Dict, provider_name: str, compliment: str):
        """Логирует статистику использования"""
        logger.info(
            f"📊 Статистика генерации | "
            f"Попыток: {stats['attempts']} | "
            f"Провайдер: {provider_name} | "
            f"Длина: {len(compliment)} chars"
        )
    
    def get_available_providers(self) -> List[str]:
        """Возвращает список доступных провайдеров"""
        return [name for name, _ in self.providers]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Возвращает информацию о всех провайдерах"""
        info = {}
        
        for name, provider in self.providers:
            if name == 'fallback':
                info[name] = {
                    'type': 'local',
                    'status': 'available',
                    'description': 'Локальный шаблонный генератор'
                }
            elif hasattr(provider, 'get_info'):
                info[name] = provider.get_info()
            else:
                info[name] = {
                    'type': 'api',
                    'status': 'available',
                    'description': f'{name.capitalize()} API провайдер'
                }
        
        return info


# Глобальный экземпляр
ai_generator = AIGenerator()
