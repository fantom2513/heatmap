"""Валидация изображений для ML Processor."""
import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, UnidentifiedImageError
import io

from src.constants import (
    MAX_IMAGE_DIMENSION,
    ALLOWED_IMAGE_MIME_TYPES,
    ALLOWED_IMAGE_EXTENSIONS,
    ENVIRONMENT,
)

logger = logging.getLogger(__name__)


class ImageValidationError(Exception):
    """Базовое исключение для ошибок валидации изображения."""
    pass


class InvalidImageFormatError(ImageValidationError):
    """Ошибка: недопустимый формат изображения."""
    pass


class ImageDimensionExceededError(ImageValidationError):
    """Ошибка: превышено максимальное разрешение изображения."""
    pass


def validate_image_format(
    content: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None
) -> None:
    """
    Валидирует формат изображения по MIME-type (быстрая проверка).
    
    Это легковесная проверка для раннего отклонения невалидных файлов.
    Финальная проверка через PIL выполняется в validate_and_open_image.
    
    Расширение файла не проверяется как блокирующее, так как оно может быть
    переименовано. Реальная проверка формата выполняется через PIL.
    
    Args:
        content: Байты файла (не используется, но оставлен для совместимости API)
        filename: Имя файла (опционально, используется только для логирования)
        content_type: MIME-type файла (опционально)
        
    Raises:
        InvalidImageFormatError: Если формат не поддерживается
    """
    # Проверка MIME-type если указан (быстрая проверка)
    if content_type:
        content_type_lower = content_type.lower()
        if content_type_lower not in ALLOWED_IMAGE_MIME_TYPES:
            error_msg = (
                f"Недопустимый MIME-type: {content_type}. "
                f"Разрешенные форматы: {', '.join(sorted(ALLOWED_IMAGE_MIME_TYPES))}"
            )
            logger.warning("Image format validation failed (MIME-type)", extra={
                "content_type": content_type,
                "file_name": filename
            })
            raise InvalidImageFormatError(
                error_msg if ENVIRONMENT == "development" else "Недопустимый формат изображения"
            )
    
    # Проверка расширения файла - только для логирования (не блокирующая)
    # Расширение может быть переименовано, поэтому реальную проверку делает PIL
    if filename:
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            logger.debug("File extension mismatch (non-blocking)", extra={
                "extension": file_ext,
                "file_name": filename,
                "allowed_extensions": sorted(ALLOWED_IMAGE_EXTENSIONS)
            })
    
    # Примечание: Финальная проверка через PIL выполняется в validate_and_open_image
    # чтобы избежать двойного открытия файла


def validate_image_dimensions(image: Image.Image) -> Tuple[int, int]:
    """
    Валидирует размеры изображения.
    
    Args:
        image: Объект PIL.Image
        
    Returns:
        Tuple[int, int]: (width, height) изображения
        
    Raises:
        ImageDimensionExceededError: Если размеры превышают MAX_IMAGE_DIMENSION
    """
    width, height = image.size
    max_dimension = max(width, height)
    
    if max_dimension > MAX_IMAGE_DIMENSION:
        error_msg = (
            f"Разрешение изображения превышает максимум: {width}x{height}. "
            f"Максимальное разрешение: {MAX_IMAGE_DIMENSION}px"
        )
        logger.warning("Image dimension validation failed", extra={
            "width": width,
            "height": height,
            "max_dimension": max_dimension,
            "max_allowed": MAX_IMAGE_DIMENSION
        })
        raise ImageDimensionExceededError(
            error_msg if ENVIRONMENT == "development" else f"Изображение слишком большое (максимум {MAX_IMAGE_DIMENSION}px)"
        )
    
    return width, height


def validate_and_open_image(
    content: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None
) -> Image.Image:
    """
    Валидирует и открывает изображение (комплексная проверка).
    
    Выполняет:
    1. Быструю валидацию формата (MIME-type, расширение) - для раннего отклонения
    2. Открытие и проверку через PIL - финальная проверка формата
    3. Валидацию размеров
    
    Args:
        content: Байты файла
        filename: Имя файла (опционально)
        content_type: MIME-type файла (опционально)
        
    Returns:
        Image.Image: Валидное изображение в формате RGB
        
    Raises:
        InvalidImageFormatError: Если формат не поддерживается
        ImageDimensionExceededError: Если размеры превышают максимум
    """
    # Шаг 1: Быстрая валидация формата (MIME-type, расширение)
    # Это позволяет быстро отклонить невалидные файлы без открытия через PIL
    validate_image_format(content, filename, content_type)
    
    # Шаг 2: Открытие изображения через PIL (финальная проверка формата)
    # Это единственное место, где мы открываем файл
    try:
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except UnidentifiedImageError as e:
        error_msg = f"Ошибка открытия изображения: {str(e)}"
        logger.error("Failed to open image", exc_info=True, extra={
            "file_name": filename,
            "content_type": content_type
        })
        raise InvalidImageFormatError(
            error_msg if ENVIRONMENT == "development" else "Недопустимый формат изображения"
        )
    
    # Шаг 3: Валидация размеров
    validate_image_dimensions(image)
    
    logger.debug("Image validation successful", extra={
        "file_name": filename,
        "size": image.size,
        "format": image.format
    })
    
    return image
