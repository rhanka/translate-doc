from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class Job:
    id: str
    filename: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    result_path: Optional[Path] = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result_url": f"/api/jobs/{self.id}/result" if self.result_path else None,
        }
