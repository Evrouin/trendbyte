"""Reports endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["reports"])

REPORTS_DIR = Path(__file__).parent.parent.parent / "output" / "reports"


@router.get("/reports/latest")
def get_latest_report():
    """Get the latest pipeline run report."""
    if not REPORTS_DIR.exists():
        return {"error": "No reports found"}

    reports = sorted(REPORTS_DIR.glob("report_*.md"), reverse=True)
    if not reports:
        return {"error": "No reports found"}

    content = reports[0].read_text()
    return {
        "filename": reports[0].name,
        "content": content,
    }
