"""Render HTML templates to PNG images for Twitter posts."""

from __future__ import annotations

import asyncio
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


class ImageRenderer:
    """Renders Jinja2 HTML templates to PNG images via Playwright."""

    def __init__(self) -> None:
        self._env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        OUTPUT_DIR.mkdir(exist_ok=True)

    def render_trending_card(self, trends: list[dict], date: str) -> str:
        """Render daily trending card. Returns path to generated PNG."""
        return asyncio.run(self._render("trending_card.html", {"trends": trends, "date": date}, "trending_card.png"))

    def render_weekly_comparison(self, trends: list[dict], week: str) -> str:
        """Render weekly comparison chart. Returns path to generated PNG."""
        return asyncio.run(self._render("weekly_comparison.html", {"trends": trends, "week": week}, "weekly_comparison.png"))

    async def _render(self, template_name: str, data: dict, output_name: str) -> str:
        """Render template to PNG."""
        template = self._env.get_template(template_name)
        html = template.render(**data)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1200, "height": 675}, device_scale_factor=2)
            await page.set_content(html, wait_until="networkidle")
            filepath = str(OUTPUT_DIR / output_name)
            await page.screenshot(path=filepath)
            await browser.close()

        return filepath
