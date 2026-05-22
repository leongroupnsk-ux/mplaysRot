"""
Хранилище моделей: сохранение/загрузка артефактов на диск (models/).
В продакшне заменяется на MinIO/S3.
"""
import os
import joblib
from pathlib import Path
from typing import Any

import onnx

_MODELS_DIR = Path(os.getenv("MODELS_DIR", "/app/models"))
_MODELS_DIR.mkdir(parents=True, exist_ok=True)


def save_joblib(name: str, obj: Any) -> Path:
    path = _MODELS_DIR / f"{name}.pkl"
    joblib.dump(obj, path)
    return path


def load_joblib(name: str) -> Any:
    path = _MODELS_DIR / f"{name}.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}")
    return joblib.load(path)


def save_onnx(name: str, model: onnx.ModelProto) -> Path:
    path = _MODELS_DIR / f"{name}.onnx"
    onnx.save(model, str(path))
    return path


def load_onnx_path(name: str) -> str:
    path = _MODELS_DIR / f"{name}.onnx"
    if not path.exists():
        raise FileNotFoundError(f"ONNX model not found: {path}")
    return str(path)


def model_exists(name: str, ext: str = "pkl") -> bool:
    return (_MODELS_DIR / f"{name}.{ext}").exists()
