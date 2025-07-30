from typing import Awaitable, Callable

import yaml
from typing_extensions import TypeAlias
from watchfiles import awatch

from src.renderer import ResumeDataValidationError, ResumeRenderer, ResumeTemplate

PreviewUpdatedCallback: TypeAlias = Callable[[str], Awaitable[None]]


class ResumeService:
    def __init__(self, renderer: ResumeRenderer):
        self._renderer = renderer

    async def generate_pdf(
        self,
        cv_data_path: str,
        output_path: str,
        template: ResumeTemplate = ResumeTemplate.DEFAULT,
    ) -> None:
        async def write_to_pdf_file(preview_content: str) -> None:
            with open(output_path, "wb") as f:
                f.write(self._renderer.generate_pdf(preview_content))

        await self._update_preview(cv_data_path, write_to_pdf_file, template)

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
        except Exception:
            await on_preview_updated(self._renderer.render_error(f"Could not open file: {file_path}"))
            return

        try:
            rendered_content = self._renderer.render_resume(resume_data, template)

            await on_preview_updated(rendered_content)
        except ResumeDataValidationError as e:
            error_page = self._renderer.render_error(str(e))
            await on_preview_updated(error_page)
