"""Константы для ML Processor сервиса."""
import os

# Максимальный размер загружаемого файла (в байтах)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB по умолчанию

# Максимальное разрешение изображения (ширина или высота в пикселях)
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", str(4096)))  # 4096px по умолчанию

# Разрешенные форматы изображений (MIME types)
ALLOWED_IMAGE_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}

# Разрешенные расширения файлов (для дополнительной проверки)
ALLOWED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

# Окружение (development/production)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

# TTL для кэша health check (в секундах)
HEALTH_CHECK_CACHE_TTL = int(os.getenv("HEALTH_CHECK_CACHE_TTL", "60"))  # 60 сек по умолчанию
