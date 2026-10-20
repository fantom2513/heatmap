"""Общие middleware для FastAPI сервисов."""
import uuid
import logging
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Module-level ContextVar — one instance, never re-created per request.
# Defined here so logging_config.py can import it to inject request_id
# into LogRecord via the record factory.
_request_id_var: ContextVar[str] = ContextVar('request_id', default='-')


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления Request ID к каждому запросу."""

    async def dispatch(self, request: Request, call_next):
        # Генерируем или получаем request_id из заголовка
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Set the ContextVar for the duration of this coroutine.
        # Save the token so we can reset after the request (prevents bleed in
        # task-pool / asyncio scenarios where the same task handles multiple reqs).
        token = _request_id_var.set(request_id)

        # Выполняем запрос
        try:
            response: Response = await call_next(request)
        finally:
            _request_id_var.reset(token)

        response.headers["X-Request-ID"] = request_id
        return response


# ---------------------------------------------------------------------------
# Single module-level LogRecordFactory installation.
# Reads _request_id_var; called ONCE here, NOT per request.
# ---------------------------------------------------------------------------

def _make_request_id_factory(original_factory):
    def factory(*args, **kwargs):
        record = original_factory(*args, **kwargs)
        if not hasattr(record, 'request_id'):
            record.request_id = _request_id_var.get()
        # Import here to avoid circular imports at module level; reads the
        # module-level variable set by setup_logging().
        from src.logging_config import _service_name  # noqa: PLC0415
        if not hasattr(record, 'service'):
            record.service = _service_name
        return record
    return factory


logging.setLogRecordFactory(_make_request_id_factory(logging.getLogRecordFactory()))
