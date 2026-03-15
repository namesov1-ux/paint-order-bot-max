# core/adapters/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

@dataclass
class User:
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None

@dataclass
class Chat:
    id: int
    type: str = "private"

@dataclass
class Message:
    message_id: int
    from_user: User
    chat: Chat
    date: int
    text: Optional[str] = None
    bot: Any = None
    
    @property
    def from_(self):
        return self.from_user
    
    async def answer(self, text: str, **kwargs):
        if self.bot:
            return await self.bot.send_message(self.chat.id, text, **kwargs)
    
    async def reply(self, text: str, **kwargs):
        return await self.answer(text, **kwargs)

@dataclass
class CallbackQuery:
    id: str
    from_user: User
    message: Message
    data: str
    
    @property
    def from_(self):
        return self.from_user

class BaseAdapter(ABC):
    @abstractmethod
    async def send_message(self, chat_id: int, text: str, **kwargs) -> Dict:
        pass
    
    @abstractmethod
    async def edit_message_text(self, text: str, chat_id: int = None, 
                               message_id: int = None, **kwargs) -> Dict:
        pass
    
    @abstractmethod
    async def answer_callback(self, callback_id: str, text: str = None, 
                             show_alert: bool = False) -> Dict:
        pass
    
    @abstractmethod
    async def get_me(self) -> Dict:
        pass
