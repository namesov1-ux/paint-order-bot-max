import logging
import requests
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

    async def send_message(self, chat_id: int, text: str, **kwargs) -> Dict:
        try:
            logger.info(f"📤 MAX: Отправка сообщения {chat_id}")
            return {"ok": True, "result": {"message_id": 123}}
        except Exception as e:
            logger.error(f"❌ MAX send_message error: {e}")
            return {"ok": False, "error": str(e)}
    
    async def edit_message_text(self, text: str, chat_id: int = None, 
                               message_id: int = None, **kwargs) -> Dict:
        logger.info(f"✏️ MAX: Редактирование {message_id}")
        return {"ok": True}
    
    async def answer_callback(self, callback_id: str, text: str = None, 
                             show_alert: bool = False) -> Dict:
        logger.info(f"🔄 MAX: Ответ на callback")
        return {"ok": True}
    
    async def get_me(self) -> Dict:
        if not self._me:
            self._me = {"id": 0, "username": "paint_bot"}
        return self._me
    
    async def set_webhook(self, url: str) -> bool:
        logger.info(f"🔗 MAX: Установка вебхука {url}")
        return True
    
    def get_update_handler(self) -> Callable:
        async def handle_update(data: Dict):
            if not self.dispatcher:
                return False
            return await self.dispatcher.process_update(data)
        return handle_update
