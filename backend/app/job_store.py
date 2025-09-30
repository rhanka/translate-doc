from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict

from .models import Job, JobStatus


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def create(self, job: Job) -> Job:
        async with self._lock:
            self._jobs[job.id] = job
        return job

    async def get(self, job_id: str) -> Job | None:
        async with self._lock:
            job = self._jobs.get(job_id)
        return job

    async def update(self, job_id: str, **changes) -> Job:
        async with self._lock:
            job = self._jobs[job_id]
            new_job = replace(
                job,
                **changes,
                updated_at=datetime.now(timezone.utc),
            )
            self._jobs[job_id] = new_job
        return new_job

    async def list(self) -> list[Job]:
        async with self._lock:
            return list(self._jobs.values())


job_store = JobStore()
