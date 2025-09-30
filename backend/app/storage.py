from __future__ import annotations

from pathlib import Path
from typing import Tuple

from .config import get_settings


class StorageManager:
    def __init__(self, base_path: Path | None = None) -> None:
        settings = get_settings()
        self._base_path = (base_path or settings.storage_path).resolve()
        self._base_path.mkdir(parents=True, exist_ok=True)

    def job_directory(self, job_id: str) -> Path:
        path = self._base_path / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def input_path(self, job_id: str, filename: str) -> Path:
        job_dir = self.job_directory(job_id)
        return job_dir / filename

    def output_path(self, job_id: str, source_filename: str, suffix: str | None = None) -> Path:
        job_dir = self.job_directory(job_id)
        path = Path(source_filename)
        stem = path.stem
        ext = path.suffix
        if suffix:
            stem = f"{stem}{suffix}"
        return job_dir / f"{stem}{ext}"


storage = StorageManager()
