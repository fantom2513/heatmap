"""
Тесты для валидации изображений - только критичные проверки.
"""
import pytest
from PIL import Image
import io

from src.utils.image_validator import (
    validate_and_open_image,
    InvalidImageFormatError,
    ImageDimensionExceededError,
)


def test_validate_and_open_image_success():
    """Тест успешной валидации - основной flow"""
    test_image = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    result_image = validate_and_open_image(
        content=img_bytes.getvalue(),
        filename="test.png",
        content_type="image/png"
    )
    
    assert isinstance(result_image, Image.Image)
    assert result_image.size == (100, 100)
    assert result_image.mode == "RGB"


def test_validate_and_open_image_invalid_format():
    """Тест отклонения невалидного формата - критичная проверка безопасности"""
    invalid_content = b"not an image"
    
    with pytest.raises(InvalidImageFormatError):
        validate_and_open_image(
            content=invalid_content,
            filename="test.txt",
            content_type="text/plain"
        )


def test_validate_and_open_image_exceeded_dimensions():
    """Тест отклонения превышенных размеров - критичная проверка"""
    test_image = Image.new('RGB', (5000, 5000), color='red')
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    with pytest.raises(ImageDimensionExceededError):
        validate_and_open_image(
            content=img_bytes.getvalue(),
            filename="large.png",
            content_type="image/png"
        )
