import yaml
from typing import Callable, Awaitable

import typer
from watchfiles import awatch

from renderer import ResumeRenderer, Template, ResumeDataValidationError


class PreviewService:
    def __init__(self, renderer: ResumeRenderer):
        self._renderer = renderer

    async def watch_file(
            self,
            file_path: str,
            on_preview_updated: Callable[[str], Awaitable[None]],
            template: Template = Template.DEFAULT_RESUME,
    ) -> None:
        await self.update_preview(file_path, on_preview_updated, template)
        async for _ in awatch(file_path):
            await self.update_preview(file_path, on_preview_updated, template)

    async def update_preview(self, file_path, on_preview_updated, template):
        try:
            with open(file_path, 'r') as f:
                resume_data = yaml.safe_load(f)

            rendered_content = self._renderer.render_resume(resume_data, template)

            await on_preview_updated(rendered_content)
        except Exception as e:
            error_page = self._renderer.render_error(str(e))
            await on_preview_updated(error_page)
