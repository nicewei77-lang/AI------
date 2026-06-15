from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

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
                await mark_analysis_job_failed(db, post_id, "AI 분석 실패")
            except AnalysisPostNotFoundError:
                logger.warning("analysis job failed after post was removed: post_id=%s", post_id)


def _job_out(state: AnalysisJobState, message: str | None = None) -> AnalysisJobOut:
    return AnalysisJobOut(
        post_id=state.post_id,
        status=state.status,  # type: ignore[arg-type]
        latest_report_id=state.latest_report_id,
        latest_report_status=state.latest_report_status,  # type: ignore[arg-type]
        message=message,
    )
