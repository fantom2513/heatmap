"""Настройка логирования для ML Processor сервиса."""
import logging
import os


class MarkedFormatter(logging.Formatter):
    """Форматтер логов с маркерами уровней."""
    
    LEVEL_MARKERS = {
        'DEBUG': '[DEBUG]',
        'INFO': '[INFO]',
        'WARNING': '[WARNING]',
        'ERROR': '[ERROR]',
        'CRITICAL': '[CRITICAL]',
    }

    def format(self, record):
        """Форматирует запись лога с маркером уровня."""
        original = record.levelname
        record.levelname = self.LEVEL_MARKERS.get(
            original, f'[{original}]'
        )
        formatted = super().format(record)
        record.levelname = original
        return formatted


def setup_logging_fallback(service_name: str) -> None:
    """
    Настройка fallback логирования, если общий модуль недоступен.
    
    Args:
        service_name: Имя сервиса для логирования
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Очищаем существующие хендлеры, чтобы избежать дублирования
    if root_logger.handlers:
        return
    
    handler = logging.StreamHandler()
    handler.setFormatter(MarkedFormatter(
        f'%(asctime)s - %(name)s - %(levelname)s - [{service_name}] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(handler)


def setup_service_logging(service_name: str) -> None:
    from src.logging_config import setup_logging
    setup_logging(
        service_name=service_name,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        json_format=os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
    )
