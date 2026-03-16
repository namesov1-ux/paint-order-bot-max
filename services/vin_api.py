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
        self.base_url = "https://api.auto.dev"
        self.session = requests.Session()
        # Устанавливаем заголовок авторизации для всех запросов сессии [citation:1][citation:2]
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })

    def decode_vin(self, vin: str) -> Optional[Dict[str, Any]]:
        """
        Декодирование VIN-номера и получение спецификаций (включая код краски).
        """
        try:
            logger.info(f"🔍 Запрос к Auto.dev API для VIN: {vin}")

            # 1. Базовый запрос к VIN Decode endpoint [citation:2]
            vin_response = self.session.get(
                f"{self.base_url}/vin/{vin}",
                timeout=10
            )

            if vin_response.status_code != 200:
                logger.error(f"❌ Ошибка VIN Decode API: {vin_response.status_code}")
                return None

            vin_data = vin_response.json()
            logger.info(f"✅ Получен базовый ответ от API")

            # Формируем базовый результат
            vehicle = vin_data.get('vehicle', {})
            result = {
                'vin': vin_data.get('vin'),
                'brand': vehicle.get('make'),
                'model': vehicle.get('model'),
                'year': vehicle.get('year'),
                'manufacturer': vehicle.get('manufacturer'),
                'type': vehicle.get('type'),
                'paint_code': None,  # Пока не знаем
                'raw_data': vin_data
            }

            # 2. Запрос к Specifications endpoint для получения кода краски [citation:1]
            specs_url = vin_data.get('discover', {}).get('📋 Specifications')
            if specs_url:
                logger.info(f"🔍 Запрос к Specifications endpoint: {specs_url}")
                try:
                    specs_response = self.session.get(specs_url, timeout=10)
                    if specs_response.status_code == 200:
                        specs_data = specs_response.json()
                        result['paint_code'] = self._extract_paint_code_from_specs(specs_data)
                        result['specs_data'] = specs_data  # Сохраним на всякий случай
                    else:
                        logger.warning(f"⚠️ Не удалось получить спецификации (статус: {specs_response.status_code})")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при запросе спецификаций: {e}")
            else:
                logger.info("ℹ️ URL для спецификаций не найден в ответе.")

            if result['paint_code']:
                 logger.info(f"✅ Найден код краски: {result['paint_code']}")
            else:
                 logger.info("ℹ️ Код краски не найден в спецификациях.")

            return result

        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут при запросе к API")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Непредвиденная ошибка: {e}", exc_info=True)
            return None

    def _extract_paint_code_from_specs(self, specs_data: Dict) -> Optional[str]:
        """
        Извлекает код краски из данных, полученных от /specs endpoint.
        """
        # Auto.dev может возвращать цвета в разных полях. Проверим основные.
        # 1. Прямое поле для внешнего цвета [citation:1]
        exterior_color = specs_data.get('exteriorColor')
        if exterior_color and isinstance(exterior_color, dict):
            return exterior_color.get('code')

        # 2. В списке спецификаций (бывает и так)
        for spec in specs_data.get('specifications', []):
            if spec.get('category') == 'Exterior' and 'color' in spec.get('name', '').lower():
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
        if vin_data.get('manufacturer'):
            lines.append(f"🏭 Производитель: {vin_data['manufacturer']}")
        if vin_data.get('paint_code'):
            lines.append(f"🎨 Код краски: {vin_data['paint_code']}")
        else:
            lines.append("❓ Код краски не найден в базе.")
        return "\n".join(lines)

    def extract_paint_code(self, vin_data: Dict) -> Optional[str]:
        """Просто возвращает код краски из словаря с данными."""
        return vin_data.get('paint_code')