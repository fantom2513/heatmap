"""
Конфигурация pytest для ML Processor тестов.
"""
import sys
from pathlib import Path
import pytest

# Настройка PYTHONPATH для корректной работы импортов
service_root = Path(__file__).parent.parent
sys.path.insert(0, str(service_root))

# Фикстура для TestClient
try:
    from fastapi.testclient import TestClient
    
    @pytest.fixture
    def client():
        """Фикстура для создания тестового клиента"""
        from src.api import app
        return TestClient(app)
except ImportError:
    # Fallback для старых версий FastAPI
    import httpx
    
    @pytest.fixture
    def client():
        """Фикстура для создания тестового клиента"""
        from src.api import app
        transport = httpx.ASGITransport(app=app)
        return httpx.Client(transport=transport, base_url="http://testserver")
