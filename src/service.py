from typing import Awaitable, Callable

import yaml  # type: ignore[import]
from typing_extensions import TypeAlias
from watchfiles import awatch

from src.renderer import ResumeRenderer, ResumeTemplate

PreviewUpdatedCallback: TypeAlias = Callable[[str], Awaitable[None]]


class ResumeService:
    def __init__(self, renderer: ResumeRenderer):
        self._renderer = renderer

    def generate_pdf(
        self,
        csv_data_path: str,
        output_path: str,
        template: ResumeTemplate = ResumeTemplate.DEFAULT,
    ) -> None:
        with open(csv_data_path, "r") as f:
            resume_data = yaml.safe_load(f)

        rendered_content = self._renderer.render_resume(resume_data, template)
        pdf = self._renderer.generate_pdf(rendered_content)
        with open(output_path, "wb") as f:
            f.write(pdf)

    async def watch_file(
        self,
        file_path: str,
        on_preview_updated: PreviewUpdatedCallback,
        template: ResumeTemplate = ResumeTemplate.DEFAULT,
    ) -> None:
        await self._update_preview(file_path, on_preview_updated, template)
        async for _ in awatch(file_path):
            await self._update_preview(file_path, on_preview_updated, template)

    async def _update_preview(
        self,
        file_path: str,
        on_preview_updated: PreviewUpdatedCallback,
        template: ResumeTemplate,
    ) -> None:
        try:
            with open(file_path, "r") as f:
                resume_data = yaml.safe_load(f)

            rendered_content = self._renderer.render_resume(resume_data, template)

            await on_preview_updated(rendered_content)
        except Exception as e:
            error_page = self._renderer.render_error(str(e))
            await on_preview_updated(error_page)
