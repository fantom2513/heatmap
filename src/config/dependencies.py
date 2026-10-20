"""Dependency Injection для ML Processor сервиса."""
from functools import lru_cache
from typing import Annotated
from fastapi import Depends

from src.services.heatmap_service import HeatmapService


@lru_cache(maxsize=1)
def get_heatmap_service() -> HeatmapService:
    """
    Получить экземпляр HeatmapService (singleton с lazy loading).
    
    Модель загружается только при первом вызове и кэшируется.
    Это позволяет:
    - Загружать модель один раз при первом запросе
    - Переиспользовать модель для всех последующих запросов
    - Улучшить производительность и снизить нагрузку на память
    
    Returns:
        HeatmapService: Экземпляр сервиса с загруженной моделью
    """
    return HeatmapService()


# Type alias для удобства использования в эндпоинтах
HeatmapServiceDep = Annotated[HeatmapService, Depends(get_heatmap_service)]
