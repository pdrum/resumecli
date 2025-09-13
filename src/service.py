import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

import yaml
from typing_extensions import TypeAlias
from watchfiles import awatch

from src.constants import PROJECT_ROOT
from src.renderer import ResumeDataValidationError, ResumeRenderer, ResumeTemplate

PreviewUpdatedCallback: TypeAlias = Callable[[str], Awaitable[None]]


@dataclass
class NewResumeResult:
    """Results from creating a new resume."""

    resume_path: Path
    schema_path: Path


class ResumeService:
    def __init__(self, renderer: ResumeRenderer):
        self._renderer = renderer

    async def generate_pdf(
        self,
        cv_data_path: str,
        output_path: str,
        template: ResumeTemplate,
    ) -> None:
        async def write_to_pdf_file(preview_content: str) -> None:
            with open(output_path, "wb") as f:
                f.write(self._renderer.generate_pdf(preview_content))

        await self._update_preview(cv_data_path, write_to_pdf_file, template)

    async def show_previews(
        self,
        file_path: str,
        on_preview_updated: PreviewUpdatedCallback,
        template: ResumeTemplate,
    ) -> None:
        await self._update_preview(file_path, on_preview_updated, template)
        async for _ in awatch(file_path):
            await self._update_preview(file_path, on_preview_updated, template)

    @staticmethod
    def create_new_resume(output_path: str) -> NewResumeResult:
        output_path = Path(output_path)
        output_dir = output_path.parent

        sample_path = PROJECT_ROOT / "cv.sample.yaml"
        schema_path = PROJECT_ROOT / "cv.schema.json"

        schema_dest = output_dir / "cv.schema.json"

        shutil.copy(sample_path, output_path)
        shutil.copy(schema_path, schema_dest)

        return NewResumeResult(resume_path=output_path, schema_path=schema_dest)

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
