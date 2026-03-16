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
        # Важно: токен передаётся как есть (без Bearer) согласно документации
        self.session.headers.update({
            'Authorization': self.token,
            'Content-Type': 'application/json'
        })
        self._me = None
        self.dispatcher = None
        logger.info(f"✅ MAXAdapter инициализирован с токеном: {token[:10]}...")

    async def send_message(self, chat_id: int, text: str, **kwargs) -> Dict:
        """Отправка сообщения через API MAX"""
        try:
            logger.info(f"📤 MAX: Попытка отправки сообщения в чат {chat_id}")
            logger.info(f"📤 Текст: {text[:100]}...")
            
            # Формируем payload согласно документации MAX API
            payload = {
                "recipient": {
                    "chat_id": chat_id
                },
                "message": {
                    "body": {
                        "text": text
                    }
                }
            }
            
            logger.info(f"📤 URL: {self.api_url}/messages")
            logger.info(f"📤 Headers: Authorization: {self.token[:10]}...")
            logger.info(f"📤 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            # Отправляем POST-запрос
            response = self.session.post(
                f"{self.api_url}/messages",
                json=payload,
                timeout=10
            )
            
            logger.info(f"📥 Статус ответа: {response.status_code}")
            logger.info(f"📥 Тело ответа: {response.text[:500]}")
            
            if response.status_code in [200, 201, 202]:
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

    async def get_me(self) -> Dict:
        """Получение информации о боте"""
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

    async def edit_message_text(self, text: str, chat_id: int = None, 
                               message_id: int = None, **kwargs) -> Dict:
        """Редактирование сообщения (заглушка)"""
        logger.info(f"✏️ MAX: Редактирование сообщения {message_id} (пока не реализовано)")
        return {"ok": True}

    async def answer_callback(self, callback_id: str, text: str = None, 
                             show_alert: bool = False) -> Dict:
        """Ответ на callback (заглушка)"""
        logger.info(f"🔄 MAX: Ответ на callback {callback_id} (пока не реализовано)")
        return {"ok": True}

    async def set_webhook(self, url: str) -> bool:
        """Установка вебхука (заглушка)"""
        logger.info(f"🔗 MAX: Установка вебхука {url} (пока не реализовано)")
        return True