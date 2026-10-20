"""Доменные исключения для ML Processor сервиса."""


class MLProcessorError(Exception):
    """Базовое исключение для всех ошибок ML Processor."""
    pass


class ModelLoadError(MLProcessorError):
    """Ошибка загрузки модели."""
    pass


class ImageProcessingError(MLProcessorError):
    """Ошибка обработки изображения."""
    pass


class HeatmapGenerationError(MLProcessorError):
    """Ошибка генерации heatmap."""
    pass
