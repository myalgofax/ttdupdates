from __future__ import annotations

from datetime import datetime
from pathlib import Path


def timestamp_filename(prefix: str, ext: str = "png") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
