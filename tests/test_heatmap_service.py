"""
Тесты для HeatmapService
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

# Моки уже настроены в conftest.py
from src.services.heatmap_service import HeatmapService
from src.exceptions import ModelLoadError


@patch('src.services.heatmap_service.SaliencyPredictor')
@patch('pathlib.Path.exists')
def test_heatmap_service_init(mock_exists, mock_predictor):
    """Тест инициализации HeatmapService"""
    mock_exists.return_value = True
    mock_predictor_instance = MagicMock()
    mock_predictor.return_value = mock_predictor_instance
    
    service = HeatmapService(model_path="/test/path/model.pth")
    
    assert service.predictor is not None
    mock_predictor.assert_called_once()


@patch('src.services.heatmap_service.SaliencyPredictor')
@patch('pathlib.Path.exists')
def test_heatmap_service_init_file_not_found(mock_exists, mock_predictor):
    """Тест инициализации HeatmapService когда файл не найден"""
    mock_exists.return_value = False
    
    with pytest.raises(ModelLoadError):
        HeatmapService(model_path="/test/path/model.pth")


@patch('src.services.heatmap_service.SaliencyPredictor')
@patch('pathlib.Path.exists')
def test_generate_heatmap_success(mock_exists, mock_predictor):
    """Тест успешной генерации heatmap"""
    try:
        import numpy as np
    except ImportError:
        # Если numpy не установлен, используем мок
        np = MagicMock()
        np.array = MagicMock(return_value=MagicMock())
    
    mock_exists.return_value = True
    mock_predictor_instance = MagicMock()
    
    # Создаем мок saliency_map (не None, чтобы пройти проверку)
    if hasattr(np, 'array') and callable(np.array):
        try:
            mock_saliency_map = np.array([[0.5, 0.6], [0.7, 0.8]])
            mock_original_image = np.array([[[255, 0, 0]]], dtype=np.uint8)
            mock_contrast_mask = np.array([[0, 1], [1, 0]])
            mock_blended = np.array([[[128, 64, 0]]], dtype=np.uint8)
            mock_heatmap = np.array([[[0, 255, 0]]], dtype=np.uint8)
        except (TypeError, AttributeError):
            # Если numpy не работает, используем простые значения
            mock_saliency_map = MagicMock()
            mock_original_image = MagicMock()
            mock_contrast_mask = MagicMock()
            mock_blended = MagicMock()
            mock_heatmap = MagicMock()
    else:
        mock_saliency_map = MagicMock()
        mock_original_image = MagicMock()
        mock_contrast_mask = MagicMock()
        mock_blended = MagicMock()
        mock_heatmap = MagicMock()
    
    mock_predictor_instance.predict_saliency.return_value = (
        mock_saliency_map,  # saliency_map (не None!)
        mock_original_image,  # original_image
        mock_contrast_mask   # contrast_mask
    )
    
    mock_predictor_instance.create_heatmap_overlay.return_value = (
        mock_blended,  # blended
        mock_heatmap,  # heatmap
        MagicMock(),  # final_map
        MagicMock()   # contrast_norm
    )
    mock_predictor.return_value = mock_predictor_instance
    
    # Мокируем Image.fromarray чтобы избежать проблем с numpy
    with patch('PIL.Image.fromarray') as mock_fromarray:
        mock_fromarray.return_value = Image.new('RGB', (100, 100), color='blue')
        
        service = HeatmapService(model_path="/test/path/model.pth")
        test_image = Image.new('RGB', (100, 100), color='red')
        
        result = service.generate_heatmap(test_image)
        
        assert "blended_image" in result
        assert "heatmap" in result
        mock_predictor_instance.predict_saliency.assert_called_once()


@patch('src.services.heatmap_service.SaliencyPredictor')
@patch('pathlib.Path.exists')
def test_generate_heatmap_invalid_image_type(mock_exists, mock_predictor):
    """Тест генерации heatmap с невалидным типом изображения"""
    mock_exists.return_value = True
    mock_predictor_instance = MagicMock()
    mock_predictor.return_value = mock_predictor_instance
    
    service = HeatmapService(model_path="/test/path/model.pth")
    
    with pytest.raises(TypeError):
        service.generate_heatmap("not an image")

