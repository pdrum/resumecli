import yaml
from typing import Callable, Awaitable

import typer
from watchfiles import awatch

from renderer import ResumeRenderer, Template


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

            rendered_content = self._renderer.render(resume_data, template)

            await on_preview_updated(rendered_content)
            typer.echo("File changed. Preview updated.")
        except Exception as e:
            typer.echo(type(e).__name__ + ": " + str(e), err=True)
            typer.echo(f"Error processing file change: {str(e)}", err=True)
