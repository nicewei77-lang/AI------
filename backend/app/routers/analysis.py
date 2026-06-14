from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import AnalysisLatestOut, AnalysisRunOut
from app.services.analysis_service import (
    AnalysisPostNotFoundError,
    AnalysisReportNotFoundError,
    get_latest_analysis_for_post,
    run_analysis_for_post,
)

router = APIRouter(prefix="/posts/{post_id}/analysis")


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
