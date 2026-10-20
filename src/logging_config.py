"""Единая конфигурация логирования для всех сервисов."""
import logging
import json
import sys
from pathlib import Path
from typing import Optional
import os

# Module-level service name — set once by setup_logging(), read by middleware factory.
_service_name: str = "unknown"

# Guard: install the default record factory only once, no matter how many times
# setup_logging() is called (e.g. multiple tests each calling setup_logging()).
_factory_installed: bool = False


class JsonFormatter(logging.Formatter):
    """JSON форматтер для структурированного логирования."""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Добавляем request_id если есть
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Добавляем exception если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["stack_trace"] = self.formatStack(
                record.stack_info) if record.stack_info else None

        # Добавляем дополнительные поля из extra
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename',
                           'funcName', 'levelname', 'levelno', 'lineno',
                           'module', 'msecs', 'message', 'pathname', 'process',
                           'processName', 'relativeCreated', 'thread', 'threadName',
                           'exc_info', 'exc_text', 'stack_info', 'request_id']:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    service_name: str,
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    json_format: Optional[bool] = None,
    force: bool = False
) -> None:
    """
    Единая настройка логирования для всех сервисов.

    Использует гибридный подход:
    - Значения по умолчанию в коде (INFO, false)
    - Можно переопределить через .env (LOG_LEVEL, LOG_JSON_FORMAT)
    - Можно переопределить через параметры функции

    Args:
        service_name: Имя сервиса (api-gateway, data-processor, etc.)
        log_level: Уровень логирования (переопределяет .env и дефолт)
        log_file: Путь к файлу логов (опционально)
        json_format: Использовать JSON формат (переопределяет .env и дефолт)
        force: Принудительно переинициализировать логирование
    """
    # Store service name at module level so the single middleware factory can read it.
    global _service_name
    _service_name = service_name

    # Получаем уровень из параметра, .env или используем дефолт
    env_level = os.getenv("LOG_LEVEL", "INFO").upper()  # Дефолт: INFO
    level_str = log_level or env_level
    level = getattr(logging, level_str, logging.INFO)

    root_logger = logging.getLogger()

    # Если логирование уже настроено и force=False, только обновляем уровень
    if root_logger.handlers and not force:
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)
        return

    # Очищаем существующие хендлеры
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    # Определяем формат: параметр > .env > дефолт (false)
    if json_format is not None:
        use_json = json_format
    else:
        use_json = os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"

    if use_json:
        formatter = JsonFormatter(service_name)
    else:
        # Кастомный форматтер с яркими маркерами состояния
        class MarkedFormatter(logging.Formatter):
            """Форматтер с яркими маркерами состояния [ERROR], [WARNING], [INFO], [SUCCESS]."""

            # Маркеры состояния для разных уровней
            LEVEL_MARKERS = {
                'DEBUG': '[DEBUG]',
                'INFO': '[INFO]',
                'WARNING': '[WARNING]',
                'ERROR': '[ERROR]',
                'CRITICAL': '[CRITICAL]',
            }

            def format(self, record):
                # Заменяем levelname на маркер
                original_levelname = record.levelname
                marker = self.LEVEL_MARKERS.get(
                    original_levelname, f'[{original_levelname}]')
                record.levelname = marker

                # Форматируем сообщение
                formatted = super().format(record)

                # Восстанавливаем оригинальный levelname (на случай повторного использования)
                record.levelname = original_levelname

                return formatted

        formatter = MarkedFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(service)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Добавляем service в record. Guarded install: only wraps the factory once,
    # no matter how many times setup_logging() is called (e.g. force=True, tests).
    # If middleware.py has already installed its factory (sets 'service' itself),
    # the hasattr check here is a no-op — no double-wrapping.
    global _factory_installed
    if not _factory_installed:
        _old_factory = logging.getLogRecordFactory()

        def _default_record_factory(*args, **kwargs):
            record = _old_factory(*args, **kwargs)
            if not hasattr(record, 'service'):
                record.service = _service_name
            return record

        logging.setLogRecordFactory(_default_record_factory)
        _factory_installed = True

    # Консольный хендлер
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Файловый хендлер (если указан)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        # В файл пишем все (DEBUG), в консоль - по уровню
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Настраиваем уровни для сторонних библиотек
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
