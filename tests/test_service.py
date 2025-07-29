import os
import tempfile
from unittest.mock import MagicMock, call, patch

import pytest
import yaml

from src.renderer import ResumeRenderer, ResumeTemplate
from src.service import ResumeService

SAMPLE_RENDERED_RESUME = "<html>Rendered Resume</html>"
SAMPLE_PDF_BYTES = b"PDF_CONTENT"


@pytest.fixture
def mock_renderer():
    renderer = MagicMock(spec=ResumeRenderer)
    renderer.render_resume.return_value = SAMPLE_RENDERED_RESUME
    renderer.generate_pdf.return_value = SAMPLE_PDF_BYTES
    return renderer


class FileChangeSimulator:
    def __init__(self, file_content_list):
        self._file_content_list = file_content_list

    async def fake_awatch(self, file_path):
        for content in self._file_content_list:
            with open(file_path, "w") as f:
                f.write(content)
            yield "modified", file_path


@pytest.fixture
def resume_service(mock_renderer):
    return ResumeService(renderer=mock_renderer)


class PreviewRecorder:
    def __init__(self):
        self.previews = []

    async def on_preview_updated(self, preview: str):
        self.previews.append(preview)


class TestResumeService:
    def test_generate_pdf(self, resume_service, mock_renderer):
        test_data = {"v": 1}

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as yaml_file:
            yaml.dump(test_data, yaml_file)
            yaml_file_path = yaml_file.name

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            pdf_file_path = pdf_file.name

        try:
            resume_service.generate_pdf(
                csv_data_path=yaml_file_path, output_path=pdf_file_path, template=ResumeTemplate.DEFAULT
            )

            mock_renderer.render_resume.assert_called_once_with(test_data, ResumeTemplate.DEFAULT)
            mock_renderer.generate_pdf.assert_called_once_with(SAMPLE_RENDERED_RESUME)

            with open(pdf_file_path, "rb") as f:
                assert f.read() == SAMPLE_PDF_BYTES

        finally:
            os.unlink(yaml_file_path)
            os.unlink(pdf_file_path)

    @pytest.mark.asyncio
    async def test_watch_file(self, resume_service, mock_renderer):
        initial_data = {"v": 1}
        first_change_data = {"v": 2}
        second_change_data = {"v": 3}
        preview_recorder = PreviewRecorder()

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml") as yaml_file:
            yaml.dump(initial_data, yaml_file)

            file_change_simulator = FileChangeSimulator(
                file_content_list=[
                    yaml.dump(first_change_data),
                    yaml.dump(second_change_data),
                ]
            )

            with patch("src.service.awatch", file_change_simulator.fake_awatch):
                await resume_service.watch_file(
                    file_path=yaml_file.name,
                    on_preview_updated=preview_recorder.on_preview_updated,
                    template=ResumeTemplate.DEFAULT,
                )

            assert preview_recorder.previews == [SAMPLE_RENDERED_RESUME] * 3, "The preview should be updated 3 times."

            mock_renderer.render_resume.assert_has_calls(
                [
                    call(initial_data, ResumeTemplate.DEFAULT),
                    call(first_change_data, ResumeTemplate.DEFAULT),
                    call(second_change_data, ResumeTemplate.DEFAULT),
                ]
            )
