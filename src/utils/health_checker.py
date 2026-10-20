"""Утилита для проверки работоспособности модели."""
from functools import lru_cache
from time import time
from typing import Optional, Dict, Any
from PIL import Image

from src.constants import HEALTH_CHECK_CACHE_TTL
from src.exceptions import HeatmapGenerationError

# Кэш для результата проверки
_health_check_cache: Optional[Dict[str, Any]] = None


def check_model_health(heatmap_service) -> Dict[str, Any]:
    """
    Проверяет реальную работоспособность модели через легковесный тест.
    
    Создает тестовое изображение 10x10px и проверяет, что модель может
    выполнить предсказание. Результат кэшируется на HEALTH_CHECK_CACHE_TTL секунд.
    
    Args:
        heatmap_service: Экземпляр HeatmapService
        
    Returns:
        Dict с результатом проверки: {"status": "ok"/"error", "error": ...}
    """
    global _health_check_cache
    
    # Проверяем кэш
    if _health_check_cache:
        cache_time, cache_result = _health_check_cache["time"], _health_check_cache["result"]
        if time() - cache_time < HEALTH_CHECK_CACHE_TTL:
            return cache_result
    
    # Выполняем проверку
    try:
        # Создаем минимальное тестовое изображение (10x10px)
        test_image = Image.new('RGB', (10, 10), color='white')
        
        # Пытаемся выполнить предсказание (только predict_saliency, без overlay)
        # Это легковесная проверка, которая не создает полный heatmap
        saliency_map, _, _ = heatmap_service.predictor.predict_saliency(test_image)
        
        if saliency_map is None:
            result = {"status": "error", "error": "Model returned None"}
        else:
            result = {"status": "ok"}
            
    except Exception as e:
        result = {"status": "error", "error": str(e)}
    
    # Кэшируем результат
    _health_check_cache = {
        "time": time(),
        "result": result
    }
    
    return result
