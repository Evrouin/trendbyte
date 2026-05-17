"""Generate a local text report for each pipeline run."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.logger import Logger
from src.models import Trend

logger = Logger.get(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "output" / "reports"


def generate_report(trends: list[Trend], mentions_count: int, image_path: str | None) -> str:
    """Generate and save a markdown report. Returns the file path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.utcnow()
    filename = f"report_{now.strftime('%Y-%m-%d_%H%M')}.md"
    filepath = REPORTS_DIR / filename

    top = trends[:10]
    lines = [
        f"# TrendByte Report — {now.strftime('%B %d, %Y %H:%M UTC')}",
        "",
        "## Summary",
        "",
        f"- **Mentions collected:** {mentions_count}",
        f"- **Trends identified:** {len(trends)}",
        f"- **Image:** {image_path or 'N/A'}",
        "",
        "## Top Trending",
        "",
        "| # | Name | Score | Growth | Sources |",
        "|---|------|-------|--------|---------|",
    ]

    for i, t in enumerate(top, 1):
        sources = ", ".join(t.sources)
        lines.append(f"| {i} | {t.name} | {t.score:.0f} | {t.growth_pct}% | {sources} |")

    lines.extend(
        [
            "",
            "## Tweet Preview",
            "",
            "```",
            "⚡ Today's Trending Tech",
            "",
        ]
    )

    for i, t in enumerate(trends[:3], 1):
        lines.append(f"{i}. {t.name} — ↑{t.growth_pct}% | {t.mentions} mentions")

    lines.extend(
        [
            "",
            "#TrendByte #TechTrends",
            "```",
            "",
            "---",
            f"*Generated at {now.isoformat()}*",
        ]
    )

    filepath.write_text("\n".join(lines))
    logger.info("Report saved: %s", filepath)
    return str(filepath)
