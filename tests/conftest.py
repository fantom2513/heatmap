"""
Конфигурация pytest для ML Processor тестов.
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock
from PIL import Image

# Настройка PYTHONPATH для корректной работы импортов
service_root = Path(__file__).parent.parent
sys.path.insert(0, str(service_root))

@pytest.fixture
def heatmap_service():
    """Isolate API contract tests from model weights and inference."""
    service = MagicMock()
    service.predictor.predict_saliency.return_value = (object(), None, None)
    service.generate_heatmap.return_value = {
        "blended_image": Image.new("RGB", (100, 100), color="blue")
    }
    return service


@pytest.fixture
def client(heatmap_service):
    from fastapi.testclient import TestClient
    from src.api import app
    from src.config.dependencies import get_heatmap_service
    from src.utils import health_checker

    original_overrides = app.dependency_overrides.copy()
    health_checker._health_check_cache = None
    app.dependency_overrides[get_heatmap_service] = lambda: heatmap_service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        health_checker._health_check_cache = None
