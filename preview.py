from abc import ABC, abstractmethod
import json

import typer
from watchfiles import awatch

from renderer import ResumeRenderer, Template

class ResumeUpdatedNotifier(ABC):
    @abstractmethod
    def notify(self, content: str) -> None:
        pass


class PreviewService:
    def __init__(self, renderer: ResumeRenderer, notifier: ResumeUpdatedNotifier):
        self._renderer = renderer
        self._notifier = notifier

    async def watch_file(self, file_path: str, template: Template = Template.DEFAULT_RESUME) -> None:
        async for _ in awatch(file_path):
            try:
                with open(file_path, 'r') as f:
                    resume_data = json.load(f)

                rendered_content = self._renderer.render(resume_data, template)

                self._notifier.notify(rendered_content)
                typer.echo("File changed. Preview updated.")
            except Exception as e:
                typer.echo(f"Error processing file change: {str(e)}", err=True)
