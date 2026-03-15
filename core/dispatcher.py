# core/dispatcher.py
import logging
import json
import traceback
from typing import Dict, Any, List, Optional, Callable
from .adapters.base import BaseAdapter, User, Chat, Message, CallbackQuery

logger = logging.getLogger(__name__)

class Handler:
    def __init__(self, callback: Callable, filters: List):
        self.callback = callback
        self.filters = filters

class Router:
    def __init__(self, name: str = None):
        self.name = name
        self.message_handlers = []
        self.callback_handlers = []
    
    def message(self, *filters):
        def decorator(func):
            self.message_handlers.append(Handler(func, filters))
            return func
        return decorator
    
    def callback(self, *filters):
        def decorator(func):
            self.callback_handlers.append(Handler(func, filters))
            return func
        return decorator

class Dispatcher:
    def __init__(self, adapter: BaseAdapter):
        self.adapter = adapter
        self.message_handlers = []
        self.callback_handlers = []
        self._routers = []
    
    def include_router(self, router: Router):
        self._routers.append(router)
        self.message_handlers.extend(router.message_handlers)
        self.callback_handlers.extend(router.callback_handlers)
        logger.info(f"📦 Подключен роутер: {router.name}")
    
    async def process_update(self, update_data: Dict) -> bool:
        """Обработка входящего обновления от MAX"""
        try:
            request_id = update_data.get('request_id', 'unknown')
            logger.info("=" * 80)
            logger.info(f"🔍 [{request_id}] ПОЛУЧЕНЫ ДАННЫЕ ОТ MAX (process_update):")
            logger.info(json.dumps(update_data, indent=2, ensure_ascii=False))
            logger.info("=" * 80)
            
            # Подробный анализ структуры
            logger.info(f"📊 [{request_id}] Анализ ключей верхнего уровня: {list(update_data.keys())}")
            
            # Проверяем наличие ключа 'from' на разных уровнях
            if 'from' in update_data:
                logger.info(f"✅ [{request_id}] Ключ 'from' найден на верхнем уровне")
                logger.info(f"📝 [{request_id}] from = {json.dumps(update_data['from'], ensure_ascii=False)}")
            
            # Проверяем вложенные структуры
            if 'message' in update_data:
                logger.info(f"✅ [{request_id}] Ключ 'message' найден")
                if isinstance(update_data['message'], dict):
                    if 'from' in update_data['message']:
                        logger.info(f"✅✅ [{request_id}] Ключ 'from' найден внутри message")
                        logger.info(f"📝 [{request_id}] message.from = {json.dumps(update_data['message']['from'], ensure_ascii=False)}")
            
            if 'callback_query' in update_data:
                logger.info(f"✅ [{request_id}] Ключ 'callback_query' найден")
                if isinstance(update_data['callback_query'], dict):
                    if 'from' in update_data['callback_query']:
                        logger.info(f"✅✅ [{request_id}] Ключ 'from' найден внутри callback_query")
                        logger.info(f"📝 [{request_id}] callback_query.from = {json.dumps(update_data['callback_query']['from'], ensure_ascii=False)}")
            
            if 'bot_started' in update_data:
                logger.info(f"✅ [{request_id}] Ключ 'bot_started' найден")
            
            # Определяем тип события
            if 'message' in update_data:
                logger.info(f"📩 [{request_id}] Обнаружен тип: message")
                return await self._process_message(update_data, request_id)
            elif 'callback_query' in update_data:
                logger.info(f"🔄 [{request_id}] Обнаружен тип: callback_query")
                return await self._process_callback(update_data, request_id)
            elif 'bot_started' in update_data:
                logger.info(f"🚀 [{request_id}] Обнаружен тип: bot_started")
                return await self._process_bot_started(update_data, request_id)
            else:
                logger.warning(f"⚠️ [{request_id}] Неизвестный тип update: {list(update_data.keys())}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки update: {e}", exc_info=True)
            logger.error(f"🔍 Данные, вызвавшие ошибку: {json.dumps(update_data, ensure_ascii=False)}")
            return False
    
    async def _process_message(self, data: Dict, request_id: str = 'unknown') -> bool:
        """Обработка входящего сообщения с подробной отладкой"""
        try:
            logger.info(f"📩 [{request_id}] _process_message начал работу")
            logger.info(f"📩 [{request_id}] Входные данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Пробуем разные пути для извлечения данных
            message_data = data.get('message', {})
            logger.info(f"📩 [{request_id}] message_data = {json.dumps(message_data, ensure_ascii=False)}")
            
            # Извлекаем данные пользователя из разных возможных мест
            user_data = None
            
            # Вариант 1: из верхнего уровня
            if 'from' in data:
                user_data = data['from']
                logger.info(f"✅ [{request_id}] Данные пользователя найдены в data['from']")
            
            # Вариант 2: из message
            elif 'from' in message_data:
                user_data = message_data['from']
                logger.info(f"✅ [{request_id}] Данные пользователя найдены в message['from']")
            
            # Вариант 3: из user
            elif 'user' in data:
                user_data = data['user']
                logger.info(f"✅ [{request_id}] Данные пользователя найдены в data['user']")
            
            # Вариант 4: из sender
            elif 'sender' in data:
                user_data = data['sender']
                logger.info(f"✅ [{request_id}] Данные пользователя найдены в data['sender']")
            
            # Вариант 5: если есть user_id
            elif 'user_id' in data:
                user_data = {'id': data['user_id']}
                logger.info(f"✅ [{request_id}] Данные пользователя восстановлены из user_id")
            
            if not user_data:
                logger.error(f"❌ [{request_id}] НЕ НАЙДЕНЫ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ!")
                logger.error(f"❌ [{request_id}] Доступные ключи в data: {list(data.keys())}")
                logger.error(f"❌ [{request_id}] Доступные ключи в message_data: {list(message_data.keys()) if message_data else 'нет'}")
                return False
            
            logger.info(f"👤 [{request_id}] user_data = {json.dumps(user_data, ensure_ascii=False)}")
            
            # Извлекаем данные чата
            chat_data = {}
            if 'chat' in data:
                chat_data = data['chat']
                logger.info(f"✅ [{request_id}] Данные чата найдены в data['chat']")
            elif 'chat' in message_data:
                chat_data = message_data['chat']
                logger.info(f"✅ [{request_id}] Данные чата найдены в message['chat']")
            elif 'peer' in data:
                chat_data = data['peer']
                logger.info(f"✅ [{request_id}] Данные чата найдены в data['peer']")
            else:
                chat_data = {'id': user_data.get('id', 0)}
                logger.info(f"⚠️ [{request_id}] Данные чата не найдены, используем ID пользователя")
            
            logger.info(f"💬 [{request_id}] chat_data = {json.dumps(chat_data, ensure_ascii=False)}")
            
            # Извлекаем текст сообщения
            text = ''
            if 'text' in message_data:
                text = message_data['text']
                logger.info(f"✅ [{request_id}] Текст найден в message['text']: {text}")
            elif 'text' in data:
                text = data['text']
                logger.info(f"✅ [{request_id}] Текст найден в data['text']: {text}")
            elif 'body' in message_data and 'text' in message_data['body']:
                text = message_data['body']['text']
                logger.info(f"✅ [{request_id}] Текст найден в message['body']['text']: {text}")
            else:
                logger.warning(f"⚠️ [{request_id}] Текст сообщения не найден")
            
            # Создаем объекты
            try:
                user = User(
                    id=int(user_data.get('id', 0)),
                    first_name=user_data.get('first_name', user_data.get('name', '')),
                    last_name=user_data.get('last_name'),
                    username=user_data.get('username')
                )
                logger.info(f"✅ [{request_id}] User создан: id={user.id}, name={user.first_name}")
            except Exception as e:
                logger.error(f"❌ [{request_id}] Ошибка создания User: {e}")
                return False
            
            try:
                chat = Chat(
                    id=int(chat_data.get('id', user.id)),
                    type=chat_data.get('type', 'private')
                )
                logger.info(f"✅ [{request_id}] Chat создан: id={chat.id}")
            except Exception as e:
                logger.error(f"❌ [{request_id}] Ошибка создания Chat: {e}")
                chat = Chat(id=user.id, type='private')
            
            message_id = message_data.get('id', data.get('message_id', 0))
            if isinstance(message_id, str) and message_id.isdigit():
                message_id = int(message_id)
            
            timestamp = message_data.get('date', data.get('timestamp', data.get('date', 0)))
            
            message = Message(
                message_id=message_id,
                from_user=user,
                chat=chat,
                date=timestamp,
                text=text,
                bot=self.adapter
            )
            
            # Добавляем метод answer для обратной совместимости
            message.reply = message.answer
            
            logger.info(f"✅ [{request_id}] Message создан: id={message.message_id}, text='{message.text}'")
            logger.info(f"👤 [{request_id}] Пользователь {user.id}: {message.text}")
            
            # Ищем подходящий handler
            for i, handler in enumerate(self.message_handlers):
                logger.info(f"🔍 [{request_id}] Проверка handler {i}: {handler.callback.__name__}")
                filters_passed = True
                
                for j, filter_func in enumerate(handler.filters):
                    if callable(filter_func):
                        try:
                            logger.info(f"  🔍 [{request_id}]   Проверка фильтра {j}: {filter_func}")
                            
                            # Проверяем команды
                            if hasattr(filter_func, 'commands'):
                                logger.info(f"  🔍 [{request_id}]     Command filter: {filter_func.commands}")
                                cmd_match = False
                                for cmd in filter_func.commands:
                                    if message.text and message.text.startswith(f'/{cmd}'):
                                        cmd_match = True
                                        logger.info(f"  ✅ [{request_id}]       Команда /{cmd} совпала")
                                        break
                                if not cmd_match:
                                    logger.info(f"  ❌ [{request_id}]     Ни одна команда не совпала")
                                    filters_passed = False
                                    break
                            elif not filter_func(message):
                                logger.info(f"  ❌ [{request_id}]     Фильтр не пройден")
                                filters_passed = False
                                break
                            else:
                                logger.info(f"  ✅ [{request_id}]     Фильтр пройден")
                                
                        except Exception as e:
                            logger.error(f"❌ [{request_id}] Ошибка в фильтре {j}: {e}")
                            filters_passed = False
                            break
                
                if filters_passed:
                    logger.info(f"✅ [{request_id}] Handler {i} ПОДХОДИТ! Вызываем {handler.callback.__name__}")
                    try:
                        await handler.callback(message)
                        logger.info(f"✅ [{request_id}] Handler успешно выполнен")
                    except Exception as e:
                        logger.error(f"❌ [{request_id}] Ошибка при выполнении handler: {e}", exc_info=True)
                    return True
                else:
                    logger.info(f"❌ [{request_id}] Handler {i} НЕ подходит")
            
            logger.info(f"⚠️ [{request_id}] Нет подходящего handler для сообщения")
            return False
            
        except Exception as e:
            logger.error(f"❌ [{request_id}] Критическая ошибка в _process_message: {e}", exc_info=True)
            logger.error(traceback.format_exc())
            return False
    
    async def _process_callback(self, data: Dict, request_id: str = 'unknown') -> bool:
        """Обработка callback query с подробной отладкой"""
        try:
            logger.info(f"🔄 [{request_id}] _process_callback начал работу")
            logger.info(f"🔄 [{request_id}] Входные данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # TODO: аналогичная отладка для callback
            return False
            
        except Exception as e:
            logger.error(f"❌ [{request_id}] Ошибка в _process_callback: {e}", exc_info=True)
            return False
    
    async def _process_bot_started(self, data: Dict, request_id: str = 'unknown') -> bool:
        """Обработка события запуска бота с подробной отладкой"""
        try:
            logger.info(f"🚀 [{request_id}] _process_bot_started начал работу")
            logger.info(f"🚀 [{request_id}] Входные данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # TODO: аналогичная отладка для bot_started
            return False
            
        except Exception as e:
            logger.error(f"❌ [{request_id}] Ошибка в _process_bot_started: {e}", exc_info=True)
            return False