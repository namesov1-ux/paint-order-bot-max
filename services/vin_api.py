# services/vin_api.py
import requests
import logging
from typing import Dict, Optional, Any
from config.settings import settings

logger = logging.getLogger(__name__)

class VINAPIService:
    """Сервис для работы с Auto.dev API"""
    
    def __init__(self):
        self.api_key = settings.AUTO_DEV_API_KEY
        self.base_url = "https://api.auto.dev/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def decode_vin(self, vin: str) -> Optional[Dict[str, Any]]:
        """
        Декодирование VIN-номера через Auto.dev API
        """
        try:
            logger.info(f"🔍 Запрос к Auto.dev API для VIN: {vin}")
            
            response = self.session.get(
                f"{self.base_url}/decode/{vin}",
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Ошибка API: {response.status_code}")
                return None
            
            data = response.json()
            logger.info(f"✅ Получен ответ от API")
            
            # Извлекаем нужные данные
            result = {
                'vin': data.get('vin'),
                'brand': data.get('make', {}).get('name'),
                'model': data.get('model', {}).get('name'),
                'year': data.get('years', [{}])[0].get('year') if data.get('years') else None,
                'engine': data.get('engine', {}).get('name'),
                'paint_code': self._extract_paint_code(data),
                'raw_data': data
            }
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут при запросе к API")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к API: {e}")
            return None
    
    def _extract_paint_code(self, data: Dict) -> Optional[str]:
        """Извлекает код краски из ответа API"""
        # В Auto.dev код краски может быть в разных местах
        
        # Вариант 1: в основных данных
        if data.get('paint'):
            return data['paint'].get('code')
        
        # Вариант 2: в опциях
        for option in data.get('options', []):
            if 'paint' in option.get('name', '').lower():
                return option.get('code')
        
        # Вариант 3: в спецификациях
        if data.get('specification'):
            for spec in data['specification']:
                if 'color' in spec.get('name', '').lower():
                    return spec.get('value')
        
        return None
    
    def format_vehicle_info(self, vin_data: Dict) -> str:
        """Форматирует информацию об авто для показа пользователю"""
        lines = []
        
        if vin_data.get('brand'):
            lines.append(f"🚗 Марка: {vin_data['brand']}")
        if vin_data.get('model'):
            lines.append(f"📋 Модель: {vin_data['model']}")
        if vin_data.get('year'):
            lines.append(f"📅 Год: {vin_data['year']}")
        if vin_data.get('engine'):
            lines.append(f"🔧 Двигатель: {vin_data['engine']}")
        if vin_data.get('paint_code'):
            lines.append(f"🎨 Код краски: {vin_data['paint_code']}")
        
        return "\n".join(lines)
    
    def extract_paint_code(self, vin_data: Dict) -> Optional[str]:
        return vin_data.get('paint_code')
