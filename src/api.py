from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import io
import base64
import logging

from src.constants import MAX_FILE_SIZE, ENVIRONMENT
from src.config.logging_setup import setup_service_logging
from src.config.dependencies import get_heatmap_service
from src.services.heatmap_service import HeatmapService
from src.exceptions import ModelLoadError, HeatmapGenerationError
from src.utils.image_validator import (
    validate_and_open_image,
    InvalidImageFormatError,
    ImageDimensionExceededError,
)
from src.utils.health_checker import check_model_health

from src.middleware import RequestIDMiddleware

# Настройка логирования
setup_service_logging("ml-processor")

logger = logging.getLogger(__name__)

app = FastAPI(title="ML Processor Service")

app.add_middleware(RequestIDMiddleware)

# Pydantic модели


class HeatmapResponse(BaseModel):
    blended_png_base64: str


@app.get("/health")
async def health_check(heatmap_service: HeatmapService = Depends(get_heatmap_service)):
    """
    Health check endpoint с проверкой доступности модели.
    
    Использует DI для получения HeatmapService и проверяет реальную работоспособность
    модели через легковесный тест (с кэшированием результата).
    """
    status = {"status": "ok", "service": "ml-processor"}

    # Проверка доступности модели через DI
    try:
        # Проверяем реальную работоспособность модели
        health_result = check_model_health(heatmap_service)
        if health_result["status"] == "ok":
            status["model"] = "ok"
        else:
            status["model"] = "unavailable"
            status["error"] = health_result.get("error", "Model check failed")
            logger.error("Model health check failed", extra={"error": status["error"]})
            from fastapi import Response
            return Response(content=str(status), status_code=503, media_type="application/json")
    except ModelLoadError as e:
        status["model"] = "unavailable"
        status["error"] = str(e) if ENVIRONMENT == "development" else "Model unavailable"
        logger.error("Model load error", exc_info=True, extra={"error": str(e)})
        from fastapi import Response
        return Response(content=str(status), status_code=503, media_type="application/json")
    except Exception as e:
        status["model"] = "unavailable"
        status["error"] = str(e) if ENVIRONMENT == "development" else "Model unavailable"
        logger.error("Model unavailable", exc_info=True)
        from fastapi import Response
        return Response(content=str(status), status_code=503, media_type="application/json")

    return status


@app.post("/api/heatmap", response_model=HeatmapResponse)
async def generate_heatmap(
    file: UploadFile = File(...),
    heatmap_service: HeatmapService = Depends(get_heatmap_service)
):
    """
    Генерирует heatmap для загруженного изображения.
    
    Валидирует:
    - Размер файла (MAX_FILE_SIZE)
    - Формат изображения (PNG, JPEG, WEBP)
    - Разрешение изображения (MAX_IMAGE_DIMENSION)
    
    Args:
        file: Загруженный файл изображения
        heatmap_service: Сервис для генерации heatmap (внедряется через DI)
    """
    try:
        content = await file.read()
        file_size = len(content)
        
        logger.info("Heatmap generation request", extra={
            "file_name": file.filename,
            "file_size": file_size,
            "content_type": file.content_type
        })

        # Валидация размера файла
        if file_size > MAX_FILE_SIZE:
            error_msg = f"File too large: {file_size} bytes. Max size: {MAX_FILE_SIZE} bytes"
            logger.warning("File size validation failed", extra={
                "file_size": file_size,
                "max_size": MAX_FILE_SIZE
            })
            raise HTTPException(
                status_code=400,
                detail=error_msg if ENVIRONMENT == "development" else "Файл слишком большой"
            )

        # Валидация формата и размеров изображения
        try:
            image = validate_and_open_image(
                content=content,
                filename=file.filename,
                content_type=file.content_type
            )
        except InvalidImageFormatError as e:
            logger.warning("Image format validation failed", extra={
                "file_name": file.filename,
                "content_type": file.content_type
            })
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except ImageDimensionExceededError as e:
            logger.warning("Image dimension validation failed", extra={
                "file_name": file.filename
            })
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

        logger.debug("Image validated and opened", extra={"size": image.size})

        logger.info("Generating heatmap")
        try:
            result = heatmap_service.generate_heatmap(image)
        except HeatmapGenerationError as e:
            error_detail = str(e) if ENVIRONMENT == "development" else "Ошибка генерации heatmap"
            logger.error("Heatmap generation error", exc_info=True, extra={"error": str(e)})
            raise HTTPException(status_code=500, detail=error_detail)
        
        blended_image = result["blended_image"]

        logger.debug("Converting image to base64")
        buf = io.BytesIO()
        blended_image.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        logger.info("Heatmap generation successful", extra={
            "base64_length": len(img_b64)
        })
        return HeatmapResponse(blended_png_base64=img_b64)

    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(
            e) if ENVIRONMENT == "development" else "Внутренняя ошибка сервера"
        logger.error("Error in heatmap generation", exc_info=True)
        raise HTTPException(status_code=500, detail=error_detail)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8002, reload=True)
