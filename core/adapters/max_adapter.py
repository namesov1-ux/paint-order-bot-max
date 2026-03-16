# core/adapters/max_adapter.py
import logging
import requests
import json
from typing import Dict, Any, Optional, Callable
from .base import BaseAdapter, User, Chat, Message, CallbackQuery

logger = logging.getLogger(__name__)

class MAXAdapter(BaseAdapter):
    def __init__(self, token: str, api_url: str = "https://api.max.ru/v1"):
        self.token = token
        self.api_url = api_url
        self.session = requests.Session()
        self._me = None
        self.dispatcher = None
        logger.info(f"✅ MAXAdapter инициализирован с токеном: {token[:10]}...")

    async def send_message(self, chat_id: int, text: str, **kwargs) -> Dict:
        """Реальная отправка сообщения через API MAX"""
        try:
            logger.info(f"📤 MAX: Попытка отправки сообщения {chat_id}")
            logger.info(f"📤 Текст: {text[:100]}...")
            
            # Формируем запрос к API MAX
            url = f"{self.api_url}/messages/send"
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            payload = {
                'recipient': {
                    'chat_id': chat_id
                },
                'message': {
                    'body': {
                        'text': text
                    }
                }
            }
            
            # Добавляем клавиатуру, если есть
            if 'reply_markup' in kwargs:
                payload['message']['reply_markup'] = kwargs['reply_markup']
            
            logger.info(f"📤 URL: {url}")
            logger.info(f"📤 Headers: {headers}")
            logger.info(f"📤 Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # Отправляем запрос
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            logger.info(f"📥 Ответ статус: {response.status_code}")
            logger.info(f"📥 Ответ тело: {response.text[:200]}")
            
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
        """Редактирование сообщения"""
        try:
            logger.info(f"✏️ MAX: Редактирование {message_id} в чате {chat_id}")
            # TODO: реализовать редактирование через API MAX
            return {"ok": True}
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования: {e}")
            return {"ok": False, "error": str(e)}
    
    async def answer_callback(self, callback_id: str, text: str = None, 
                             show_alert: bool = False) -> Dict:
        """Ответ на callback"""
        try:
            logger.info(f"🔄 MAX: Ответ на callback {callback_id}")
            # TODO: реализовать ответ на callback через API MAX
            return {"ok": True}
        except Exception as e:
            logger.error(f"❌ Ошибка ответа на callback: {e}")
            return {"ok": False, "error": str(e)}
    
    async def get_me(self) -> Dict:
        """Получение информации о боте"""
        try:
            if not self._me:
                logger.info("📡 Запрос информации о боте")
                url = f"{self.api_url}/bots/me"
                headers = {'Authorization': f'Bearer {self.token}'}
                
                response = self.session.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    self._me = response.json()
                    logger.info(f"✅ Информация о боте получена: {self._me}")
                else:
                    logger.error(f"❌ Ошибка получения информации: {response.status_code}")
                    self._me = {"id": 0, "username": "paint_bot"}
            
            return self._me
        except Exception as e:
            logger.error(f"❌ Ошибка в get_me: {e}")
            return {"id": 0, "username": "paint_bot"}
    
    async def set_webhook(self, url: str) -> bool:
        """Установка вебхука"""
        try:
            logger.info(f"🔗 MAX: Установка вебхука {url}")
            # TODO: реализовать установку вебхука через API MAX
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка установки вебхука: {e}")
            return False