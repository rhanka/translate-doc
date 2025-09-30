from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import get_settings
from .job_store import job_store
from .llm import EchoClient, LLMClientError, get_llm_client
from .models import Job, JobStatus
from .storage import storage
from .translation.pipeline import UnsupportedFileTypeError, translate_job

settings = get_settings()

app = FastAPI(title="translate-doc", version="0.1.0")

if settings.frontend_origin:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

try:
    llm_client = get_llm_client()
except LLMClientError:
    llm_client = EchoClient()


async def _save_upload(job_id: str, upload: UploadFile) -> Path:
    filename = Path(upload.filename or "document").name
    destination = storage.input_path(job_id, filename)
    async with aiofiles.open(destination, "wb") as buffer:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            await buffer.write(chunk)
    await upload.close()
    return destination


async def _run_job(job_id: str, filename: str) -> None:
    await job_store.update(job_id, status=JobStatus.PROCESSING, progress=0.05, message="Starting translation")

    def report_progress(fraction: float, message: str) -> None:
        async def _update() -> None:
            await job_store.update(job_id, progress=min(max(fraction, 0.0), 1.0), message=message)

        asyncio.create_task(_update())

    try:
        result_path = await translate_job(job_id, filename, llm_client, progress_callback=report_progress)
    except UnsupportedFileTypeError as exc:
        await job_store.update(job_id, status=JobStatus.FAILED, progress=1.0, message=str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive
        await job_store.update(job_id, status=JobStatus.FAILED, progress=1.0, message=str(exc))
        return

    await job_store.update(job_id, status=JobStatus.COMPLETED, progress=1.0, message="Completed", result_path=result_path)


@app.post("/api/jobs")
async def create_job(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = Path(file.filename or "document").name
    job_id = uuid4().hex
    job = Job(id=job_id, filename=filename)
    await job_store.create(job)
    await _save_upload(job_id, file)
    asyncio.create_task(_run_job(job_id, filename))
    return job.to_dict()


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@app.get("/api/jobs")
async def list_jobs() -> list[dict[str, Any]]:
    jobs = await job_store.list()
    return [job.to_dict() for job in sorted(jobs, key=lambda j: j.created_at, reverse=True)]


@app.get("/api/jobs/{job_id}/result")
async def download_result(job_id: str) -> FileResponse:
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED or not job.result_path:
        raise HTTPException(status_code=400, detail="Job not completed")
    return FileResponse(job.result_path, filename=Path(job.result_path).name)


@app.get("/health" )
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
