"""
Тесты для API ML Processor - только критичные сценарии.
"""
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io


@patch('src.config.dependencies.get_heatmap_service')
def test_health_check(mock_get_service, client):
    """Тест health check эндпоинта"""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ml-processor"
    assert data["model"] == "ok"


@patch('src.config.dependencies.get_heatmap_service')
def test_generate_heatmap_success(mock_get_service, client):
    """Тест успешной генерации heatmap - основной flow"""
    test_image = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    mock_service = MagicMock()
    mock_result_image = Image.new('RGB', (100, 100), color='blue')
    mock_service.generate_heatmap.return_value = {
        "blended_image": mock_result_image,
        "heatmap": mock_result_image,
        "final_map": None,
        "contrast_norm": None
    }
    mock_get_service.return_value = mock_service
    
    response = client.post(
        "/api/heatmap",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    
    assert response.status_code == 200
    assert "blended_png_base64" in response.json()


def test_generate_heatmap_invalid_format(client):
    """Тест валидации формата - критичная проверка безопасности"""
    response = client.post(
        "/api/heatmap",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "формат" in detail or "format" in detail


def test_generate_heatmap_large_dimensions(client):
    """Тест валидации размера изображения - критичная проверка"""
    test_image = Image.new('RGB', (5000, 5000), color='red')
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    response = client.post(
        "/api/heatmap",
        files={"file": ("large.png", img_bytes.getvalue(), "image/png")}
    )
    
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "размер" in detail or "dimension" in detail or "большое" in detail or "превышает" in detail


@patch('src.config.dependencies.get_heatmap_service')
def test_generate_heatmap_service_error(mock_get_service, client):
    """Тест обработки ошибки сервиса - критичная проверка"""
    from src.exceptions import HeatmapGenerationError
    
    test_image = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    mock_service = MagicMock()
    mock_service.generate_heatmap.side_effect = HeatmapGenerationError("Service error")
    mock_get_service.return_value = mock_service
    
    response = client.post(
        "/api/heatmap",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    
    assert response.status_code == 500
