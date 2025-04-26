from queue import PriorityQueue

import cv2
import numpy as np
from PIL import Image
from widgets.base import BaseWidget
import customtkinter as ctk
from PIL import ImageDraw

class Blur(BaseWidget):

    subscriptions = {
        "use_zone_changed": "on_use_zone_changed",
        "blur_changed": "on_blur_changed",
    }

    use_zones = ["editor"]

    def __init__(self, _event_bus, _is_last=False, **kwargs):
        BaseWidget.__init__(self, _event_bus=_event_bus)
        self.renderer = None
        self.base_img = None  # оригинал
        self.radius = 0
        if _is_last:
            self.init_subscribes()


    def on_use_zone_changed(self, _use_zone):
        if _use_zone:
            self.renderer = _use_zone

    # def on_file_opened(self, _img):
    #     if not _img:
    #         return
    #     print(f"opened: {_img}")
    #     self.base_img = _img  # сохраняем оригинал при открытии

    def on_blur_changed(self, _radius):
        if not _radius:
            return
        self.radius = _radius
        self.apply_blur()

    def apply_blur(self):
        if not self.renderer or not self.renderer.img:
            return

        img_np = np.array(self.renderer.img.convert("RGB"))
        if self.radius > 0:
            ksize = self._ensure_odd(self.radius * 2 + 1)
            blurred_np = cv2.GaussianBlur(img_np, (ksize, ksize), 0)
        else:
            blurred_np = img_np

        blurred_pil = Image.fromarray(blurred_np).convert("RGBA")

        # обновляем текущее изображение
        self.renderer.img = blurred_pil
        self.renderer.draw = ImageDraw.Draw(self.renderer.img)

        # сохраняем как базовое, если нужно
        self.renderer.base_img = self.renderer.img.copy()

        self.renderer.render()

    def _ensure_odd(self, k):
        return k if k % 2 == 1 else k + 1