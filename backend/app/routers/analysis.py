from __future__ import annotations

import logging
from time import monotonic

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal, get_db
from app.schemas import AnalysisJobOut, AnalysisLatestOut, AnalysisRunOut
from app.services.analysis_service import (
    AnalysisPostNotFoundError,
    AnalysisReportNotFoundError,
    AnalysisJobState,
    get_analysis_job_status_for_post,
    get_latest_analysis_for_post,
    mark_analysis_job_failed,
    run_analysis_for_post,
    start_analysis_job_for_post,
)

router = APIRouter(prefix="/posts/{post_id}/analysis")
logger = logging.getLogger(__name__)
_active_analysis_jobs: dict[int, float] = {}


@router.post("", response_model=AnalysisRunOut, response_model_by_alias=True)
async def run_analysis(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await run_analysis_for_post(db, post_id)
    except AnalysisPostNotFoundError:
        raise HTTPException(status_code=404, detail="post not found")

    return AnalysisRunOut(
        status=result.status,
        report_id=result.report_id,
        report=result.report,
        error=result.error,
    )


@router.post("/jobs", response_model=AnalysisJobOut, response_model_by_alias=True, status_code=202)
async def start_analysis_job(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        state = await start_analysis_job_for_post(db, post_id)
    except AnalysisPostNotFoundError:
        raise HTTPException(status_code=404, detail="post not found")

    if _analysis_job_is_active(post_id):
        return _job_out(state, "AI analysis job already running")

    _active_analysis_jobs[post_id] = monotonic()
    background_tasks.add_task(_run_analysis_job, post_id)
    return _job_out(state, "AI analysis job started")


@router.get("/status", response_model=AnalysisJobOut, response_model_by_alias=True)
async def get_analysis_status(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        state = await get_analysis_job_status_for_post(db, post_id)
    except AnalysisPostNotFoundError:
        raise HTTPException(status_code=404, detail="post not found")

    if state.status == "running" and _analysis_job_is_stale(post_id):
        _active_analysis_jobs.pop(post_id, None)
        await mark_analysis_job_failed(
            db,
            post_id,
            "이전 AI 분석 작업이 제한 시간을 넘어 중단되었습니다. 다시 실행할 수 있습니다.",
        )
        state = await get_analysis_job_status_for_post(db, post_id)

    return _job_out(state)


@router.get("/latest", response_model=AnalysisLatestOut, response_model_by_alias=True)
async def get_latest_analysis(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await get_latest_analysis_for_post(db, post_id)
    except AnalysisPostNotFoundError:
        raise HTTPException(status_code=404, detail="post not found")
    except AnalysisReportNotFoundError:
        raise HTTPException(status_code=404, detail="analysis report not found")

    return AnalysisLatestOut(
        status=result.status,
        report_id=result.report_id,
        report=result.report,
        error=result.error,
        created_at=result.created_at,
        model=result.model,
        reasoning_effort=result.reasoning_effort,
        response_id=result.response_id,
        trace_id=result.trace_id,
        usage=result.usage,
    )


async def _run_analysis_job(post_id: int) -> None:
    async with SessionLocal() as db:
        try:
            await run_analysis_for_post(db, post_id)
        except AnalysisPostNotFoundError:
            logger.warning("analysis job post not found: post_id=%s", post_id)
        except Exception:
            logger.exception("analysis job failed unexpectedly: post_id=%s", post_id)
            await db.rollback()
            try:
                await mark_analysis_job_failed(
                    db,
                    post_id,
                    "AI 분석 작업 중 예외가 발생해 리포트를 완성하지 못했습니다.",
                    exc=exc,
                )
            except AnalysisPostNotFoundError:
                logger.warning("analysis job failed after post was removed: post_id=%s", post_id)
        finally:
            _active_analysis_jobs.pop(post_id, None)


def _job_out(state: AnalysisJobState, message: str | None = None) -> AnalysisJobOut:
    return AnalysisJobOut(
        post_id=state.post_id,
        status=state.status,  # type: ignore[arg-type]
        latest_report_id=state.latest_report_id,
        latest_report_status=state.latest_report_status,  # type: ignore[arg-type]
        message=message,
    )


def _analysis_job_is_active(post_id: int) -> bool:
    started_at = _active_analysis_jobs.get(post_id)
    return started_at is not None and monotonic() - started_at <= _analysis_job_timeout_seconds()


def _analysis_job_is_stale(post_id: int) -> bool:
    started_at = _active_analysis_jobs.get(post_id)
    if started_at is None:
        return False
    return monotonic() - started_at > _analysis_job_timeout_seconds()


def _analysis_job_timeout_seconds() -> float:
    return max(settings.analysis_model_timeout_seconds + 30.0, 30.0)
