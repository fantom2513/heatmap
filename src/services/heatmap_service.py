from pathlib import Path
from typing import Any, Dict, Optional
from PIL import Image, UnidentifiedImageError

from src.models.saliency_model import SaliencyPredictor
from src.exceptions import ModelLoadError, HeatmapGenerationError

class HeatmapService:
    def __init__(self, model_path: Optional[str] = None):
        # Строим абсолютный путь до модели по умолчанию
        if model_path is None:
            # Путь относительно корня проекта (services/ml-processor/)
            model_path = Path(__file__).parent.parent.parent / "models" / "websaliency_model.pth"
        if not Path(model_path).exists():
            raise ModelLoadError(f"Файл модели не найден по пути: {model_path}")
        try:
            self.predictor = SaliencyPredictor(model_path=str(model_path))
        except ModelLoadError:
            raise
        except Exception as e:
            raise ModelLoadError(f"Ошибка инициализации SaliencyPredictor: {e}") from e

    def generate_heatmap(self, image: Image.Image) -> Dict[str, Any]:
        # Проверяем тип изображения
        if not isinstance(image, Image.Image):
            raise TypeError(f"Ожидался объект PIL.Image.Image, получено: {type(image)}")
        try:
            saliency_map, original_image, contrast_mask = self.predictor.predict_saliency(image)
        except Exception as e:
            raise HeatmapGenerationError(f"Ошибка при предсказании тепловой карты: {e}") from e
        if saliency_map is None:
            raise HeatmapGenerationError("Сгенерированная тепловая карта (saliency_map) оказалась None.")
        try:
            blended_image, heatmap, final_map, contrast_norm = self.predictor.create_heatmap_overlay(
                saliency_map, original_image, contrast_mask, alpha=0.6
            )
        except Exception as e:
            raise HeatmapGenerationError(f"Ошибка при наложении тепловой карты: {e}") from e
        return {
            "blended_image": Image.fromarray(blended_image),
            "heatmap": Image.fromarray(heatmap),
            "final_map": final_map,
            "contrast_norm": contrast_norm
        }

