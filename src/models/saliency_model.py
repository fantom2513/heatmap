import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import numpy as np
import cv2
from PIL import Image

import os
from typing import Tuple, Optional, Union


class WebSaliencyUNet(nn.Module):
    def __init__(self, in_channels=5, pretrained_path: Optional[str] = ""):
        super().__init__()
        resnet = models.resnet34(pretrained=False)
        # Грузим веса, если указаны
        if pretrained_path:
            if not os.path.exists(pretrained_path):
                raise FileNotFoundError(
                    f"Файл весов не найден: {pretrained_path}")
            try:
                state_dict = torch.load(pretrained_path, map_location='cpu')
                resnet.load_state_dict(state_dict)
            except Exception as e:
                raise RuntimeError(f"Ошибка загрузки весов resnet34: {e}")
        self.firstconv = nn.Conv2d(
            in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        with torch.no_grad():
            self.firstconv.weight[:, :3] = resnet.conv1.weight
            if in_channels > 3:
                mean = resnet.conv1.weight.mean(dim=1, keepdim=True)
                self.firstconv.weight[:, 3:in_channels] = mean.repeat(
                    1, in_channels - 3, 1, 1)
        self.encoder1 = nn.Sequential(
            self.firstconv, resnet.bn1, resnet.relu, resnet.maxpool)
        self.encoder2 = resnet.layer1
        self.encoder3 = resnet.layer2
        self.encoder4 = resnet.layer3
        self.encoder5 = resnet.layer4
        self.up4 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.conv4 = nn.Sequential(
            nn.Conv2d(512, 256, 3, padding=1), nn.ReLU())
        self.up3 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.conv3 = nn.Sequential(
            nn.Conv2d(256, 128, 3, padding=1), nn.ReLU())
        self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.conv2 = nn.Sequential(nn.Conv2d(128, 64, 3, padding=1), nn.ReLU())
        self.up1 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.conv1 = nn.Sequential(nn.Conv2d(32, 32, 3, padding=1), nn.ReLU())
        self.final = nn.Conv2d(32, 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.encoder1(x)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)
        e4 = self.encoder4(e3)
        e5 = self.encoder5(e4)

        d4 = self.up4(e5)
        d4 = self.conv4(torch.cat([d4, e4], dim=1))
        d3 = self.up3(d4)
        d3 = self.conv3(torch.cat([d3, e3], dim=1))
        d2 = self.up2(d3)
        d2 = self.conv2(torch.cat([d2, e2], dim=1))
        d1 = self.up1(d2)
        d1 = self.conv1(d1)

        out = F.interpolate(d1, scale_factor=2,
                            mode='bilinear', align_corners=False)
        return self.final(out)


class SaliencyPredictor:
    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device(
            'cuda' if torch.cuda.is_available() else 'cpu')
        try:
            self.model = WebSaliencyUNet(in_channels=5)
        except Exception as e:
            raise RuntimeError(
                f"Ошибка инициализации архитектуры WebSaliencyUNet: {e}")

        if model_path:
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"Файл весов модели не найден: {model_path}")
            try:
                self.model.load_state_dict(torch.load(
                    model_path, map_location=self.device))
            except Exception as e:
                raise RuntimeError(
                    f"Ошибка загрузки весов в SaliencyPredictor: {e}")
        else:
            raise ValueError(
                "Не указан путь к файлу весов модели (model_path).")

        try:
            self.model = self.model.to(self.device).eval()
        except Exception as e:
            raise RuntimeError(
                f"Ошибка переноса модели на устройство {self.device}: {e}")

    def normalize_map(self, x: np.ndarray) -> np.ndarray:
        """Нормализует карту в диапазон [0, 1]."""
        x = x - x.min()
        return x / (x.max() + 1e-8)

    def get_contrast_mask(
        self,
        img_rgb: np.ndarray,
        color_thresh: float = 0.8,
        ignore_bottom: float = 0.12,
        min_area: int = 300
    ) -> np.ndarray:
        try:
            mean_color = img_rgb.mean(axis=(0, 1), keepdims=True)
            color_dist = np.linalg.norm(img_rgb - mean_color, axis=2)
            color_dist = (color_dist - color_dist.min()) / \
                (color_dist.max() - color_dist.min() + 1e-8)
            mask = (color_dist > color_thresh).astype(np.uint8)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
            mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
                mask_clean, connectivity=8)
            H = mask_clean.shape[0]
            filtered_mask = np.zeros_like(mask_clean)
            for i in range(1, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]
                y = stats[i, cv2.CC_STAT_TOP]
                if area > min_area and y < int((1 - ignore_bottom) * H):
                    filtered_mask[labels == i] = 1
            return filtered_mask
        except Exception as e:
            raise RuntimeError(f"Ошибка генерации contrast mask: {e}")

    def preprocess_image(
        self,
        image: Union[Image.Image, np.ndarray],
        size: int = 512
    ) -> Tuple[torch.Tensor, np.ndarray, np.ndarray]:
        try:
            if isinstance(image, Image.Image):
                image = np.array(image.convert('RGB'))
            img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            img_resized = cv2.resize(img_bgr, (size, size))
            img = img_resized.transpose(2, 0, 1) / 255.0
            return torch.tensor(img, dtype=torch.float32), image, img_bgr
        except Exception as e:
            raise RuntimeError(f"Ошибка препроцессинга изображения: {e}")

    def predict_saliency(
        self,
        image: Union[Image.Image, np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        try:
            img_tensor, _, img_bgr = self.preprocess_image(image)
        except Exception as e:
            raise RuntimeError(f"Ошибка на этапе препроцессинга: {e}")
        device = self.device
        text_mask = torch.zeros((1, 512, 512), device=device)
        face_mask = torch.zeros((1, 512, 512), device=device)
        try:
            x = torch.cat(
                [img_tensor.to(device), text_mask, face_mask]).unsqueeze(0)
            with torch.no_grad():
                pred = self.model(x)[0, 0].cpu().numpy()
            pred = np.clip(pred, 0, 1)
            contrast_mask = self.get_contrast_mask(img_bgr)
            pred_map_resized = cv2.resize(
                pred, (img_bgr.shape[1], img_bgr.shape[0]))
            return pred_map_resized, img_bgr, contrast_mask
        except Exception as e:
            raise RuntimeError(f"Ошибка на этапе инференса модели: {e}")

    def create_heatmap_overlay(
        self,
        saliency_map: np.ndarray,
        original_image: np.ndarray,
        contrast_mask: np.ndarray,
        alpha: float = 0.6
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        try:
            saliency_norm = self.normalize_map(saliency_map)
            contrast_norm = self.normalize_map(
                contrast_mask.astype(np.float32))
            final_map = 0.5 * saliency_norm + 0.5 * contrast_norm
            final_map = self.normalize_map(final_map)
            heatmap = cv2.applyColorMap(
                (final_map * 255).astype(np.uint8), cv2.COLORMAP_JET)
            heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
            blended = cv2.addWeighted(
                original_image, 1 - alpha, heatmap, alpha, 0)
            return blended, heatmap, final_map, contrast_norm
        except Exception as e:
            raise RuntimeError(
                f"Ошибка при создании оверлея тепловой карты: {e}")

