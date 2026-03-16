# core/adapters/max_adapter.py
import logging
import requests
import json
from typing import Dict, Any, Optional, Callable
from .base import BaseAdapter, User, Chat, Message, CallbackQuery

logger = logging.getLogger(__name__)

class MAXAdapter(BaseAdapter):
    def __init__(self, token: str, api_url: str = "https://platform-api.max.ru"):
        self.token = token
        self.api_url = api_url
        self.session = requests.Session()
        # Устанавливаем заголовок авторизации для всех запросов [citation:8]
        self.session.headers.update({
            'Authorization': f'{self.token}',  # Токен без Bearer, просто как есть [citation:9]
            'Content-Type': 'application/json'
        })
        self._me = None
        self.dispatcher = None
        logger.info(f"✅ MAXAdapter инициализирован с токеном: {token[:10]}...")

    async def send_message(self, chat_id: int, text: str, **kwargs) -> Dict:
        """
        Отправка сообщения через официальный API MAX [citation:9]
        POST https://platform-api.max.ru/messages
        """
        try:
            logger.info(f"📤 MAX: Отправка сообщения в чат {chat_id}")
            
            # Формируем payload согласно документации [citation:9]
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            
            # Добавляем форматирование, если указано
            if 'format' in kwargs:
                payload['format'] = kwargs['format']
            
            # Добавляем клавиатуру, если есть [citation:8]
            if 'reply_markup' in kwargs:
                payload['attachments'] = [{
                    'type': 'inline_keyboard',
                    'payload': kwargs['reply_markup']
                }]
            
            logger.info(f"📤 URL: {self.api_url}/messages")
            logger.info(f"📤 Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # Отправляем POST-запрос к API MAX [citation:9]
            response = self.session.post(
                f"{self.api_url}/messages",
                json=payload,
                timeout=10
            )
            
            logger.info(f"📥 Статус ответа: {response.status_code}")
            logger.info(f"📥 Тело ответа: {response.text[:200]}")
            
            if response.status_code == 200:
                logger.info(f"✅ Сообщение успешно отправлено в чат {chat_id}")
                return response.json()
            else:
                logger.error(f"❌ Ошибка отправки: {response.status_code} - {response.text}")
                return {"ok": False, "error": response.text}
                
        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут при отправке сообщения")
            return {"ok": False, "error": "timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return {"ok": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Непредвиденная ошибка: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}
    
    async def edit_message_text(self, text: str, chat_id: int = None, 
                               message_id: int = None, **kwargs) -> Dict:
        """Редактирование сообщения через API MAX [citation:10]"""
        try:
            logger.info(f"✏️ MAX: Редактирование сообщения {message_id} в чате {chat_id}")
            
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text
            }
            
            response = self.session.put(
                f"{self.api_url}/messages",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Сообщение отредактировано")
                return response.json()
            else:
                logger.error(f"❌ Ошибка редактирования: {response.status_code}")
                return {"ok": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования: {e}")
            return {"ok": False, "error": str(e)}
    
    async def answer_callback(self, callback_id: str, text: str = None, 
                             show_alert: bool = False) -> Dict:
        """Ответ на callback-запрос [citation:10]"""
        try:
            logger.info(f"🔄 MAX: Ответ на callback {callback_id}")
            
            payload = {
                "callback_id": callback_id,
                "text": text,
                "show_alert": show_alert
            }
            
            response = self.session.post(
                f"{self.api_url}/answers",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Callback обработан")
                return response.json()
            else:
                logger.error(f"❌ Ошибка callback: {response.status_code}")
                return {"ok": False}
                
        except Exception as e:
            logger.error(f"❌ Ошибка ответа на callback: {e}")
            return {"ok": False}
    
    async def get_me(self) -> Dict:
        """Получение информации о боте [citation:8]"""
        try:
            if not self._me:
                logger.info("📡 Запрос информации о боте")
                
                response = self.session.get(
                    f"{self.api_url}/me",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self._me = response.json()
                    logger.info(f"✅ Информация о боте получена: {self._me.get('username')}")
                else:
                    logger.error(f"❌ Ошибка получения информации: {response.status_code}")
                    self._me = {"id": 0, "username": "paint_bot"}
            
            return self._me
            
        except Exception as e:
            logger.error(f"❌ Ошибка в get_me: {e}")
            return {"id": 0, "username": "paint_bot"}
    
    async def set_webhook(self, url: str) -> bool:
        """Установка вебхука через API MAX [citation:3][citation:10]"""
        try:
            logger.info(f"🔗 MAX: Установка вебхука {url}")
            
            payload = {
                "url": url,
                "update_types": ["message_created", "bot_started", "callback_query"]
            }
            
            response = self.session.post(
                f"{self.api_url}/subscriptions",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Вебхук успешно установлен")
                return True
            else:
                logger.error(f"❌ Ошибка установки вебхука: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка установки вебхука: {e}")
            return False