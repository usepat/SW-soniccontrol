from __future__ import annotations

from importlib.resources import as_file
from threading import Lock
from typing import ClassVar

import ttkbootstrap as ttk

from soniccontrol_gui.resources import resources


class SingletonMeta(type):
    _instances: ClassVar[dict[SingletonMeta, object]] = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class ImageLoader(metaclass=SingletonMeta):
    images: ClassVar[dict[str, ttk.ImageTk.PhotoImage]] = {}

    @staticmethod
    def _normalize_sizing(sizing: tuple[int, int]) -> tuple[int, int]:
        width, height = sizing
        return max(1, int(width)), max(1, int(height))

    @classmethod
    def generate_image_key(
        cls, image_name: str, sizing: tuple[int, int]
    ) -> str:
        normalized_sizing = cls._normalize_sizing(sizing)
        return f"{image_name}{normalized_sizing}"

    @classmethod
    def _load_image_resource(
        cls, image_name: str, sizing: tuple[int, int]
    ) -> ttk.ImageTk.PhotoImage:
        normalized_sizing = cls._normalize_sizing(sizing)
        with as_file(resources.PICTURES.joinpath(image_name)) as image:
            tk_image = ttk.Image.open(image, "r").resize(normalized_sizing)
            return ttk.ImageTk.PhotoImage(image=tk_image)

    @classmethod
    def load_image_resource(
        cls, image_name: str, sizing: tuple[int, int]
    ) -> ttk.ImageTk.PhotoImage:
        key: str = cls.generate_image_key(image_name, sizing)
        if key not in cls.images:
            cls.images[key] = cls._load_image_resource(image_name, sizing)
        return cls.images[key]
    
    @classmethod 
    def clear_resources(cls):
        cls.images.clear()
    
