import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import jsonschema.exceptions
import pytest
import yaml

from src.constants import PROJECT_ROOT
from src.renderer import ResumeDataValidationError, ResumeRenderer, ResumeTemplate
from src.service import NewResumeResult, ResumeService

SAMPLE_RENDERED_RESUME = "<html>Rendered Resume</html>"
SAMPLE_RENDERED_ERROR = "<html>Error Page</html>"
SAMPLE_PDF_BYTES = b"PDF_CONTENT"


@pytest.fixture
def mock_renderer():
    renderer = MagicMock(spec=ResumeRenderer)
    renderer.render_resume.return_value = SAMPLE_RENDERED_RESUME
    renderer.render_error.return_value = SAMPLE_RENDERED_ERROR
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
    @pytest.mark.asyncio
    async def test_generate_pdf(self, resume_service, mock_renderer):
        test_data = {"v": 1}

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as yaml_file:
            yaml.dump(test_data, yaml_file)
            yaml_file_path = yaml_file.name

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            pdf_file_path = pdf_file.name

        try:
            await resume_service.generate_pdf(
                cv_data_path=yaml_file_path, output_path=pdf_file_path, template=ResumeTemplate.MINIMAL_BLUE
            )

            mock_renderer.render_resume.assert_called_once_with(test_data, ResumeTemplate.MINIMAL_BLUE)
            mock_renderer.generate_pdf.assert_called_once_with(SAMPLE_RENDERED_RESUME)

            with open(pdf_file_path, "rb") as f:
                assert f.read() == SAMPLE_PDF_BYTES

        finally:
            os.unlink(yaml_file_path)
            os.unlink(pdf_file_path)

    @pytest.mark.asyncio
    async def test_generate_pdf_file_not_found(self, resume_service, mock_renderer):
        non_existent_file = "/path/that/does/not/exist.yaml"

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            pdf_file_path = pdf_file.name

        try:
            await resume_service.generate_pdf(
                cv_data_path=non_existent_file,
                output_path=pdf_file_path,
                template=ResumeTemplate.MINIMAL_BLUE,
            )

            mock_renderer.render_error.assert_called_with(f"Could not open file: {non_existent_file}")
            mock_renderer.render_resume.assert_not_called()
            mock_renderer.generate_pdf.assert_called_with(SAMPLE_RENDERED_ERROR)

            with open(pdf_file_path, "rb") as f:
                assert f.read() == SAMPLE_PDF_BYTES

        finally:
            os.unlink(pdf_file_path)

    @pytest.mark.asyncio
    async def test_generate_pdf_validation_error(self, resume_service, mock_renderer):
        invalid_data = {"invalid": "data"}
        library_error_message = "missing field 'name"

        mock_renderer.render_resume.side_effect = ResumeDataValidationError(
            jsonschema.exceptions.ValidationError(library_error_message)
        )

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as yaml_file:
            yaml.dump(invalid_data, yaml_file)
            yaml_file_path = yaml_file.name

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            pdf_file_path = pdf_file.name

        try:
            await resume_service.generate_pdf(
                cv_data_path=yaml_file_path,
                output_path=pdf_file_path,
                template=ResumeTemplate.MINIMAL_BLUE,
            )

            mock_renderer.render_resume.assert_called_once_with(invalid_data, ResumeTemplate.MINIMAL_BLUE)
            mock_renderer.render_error.assert_called_once_with(
                f"Failed to validate resume data: {library_error_message}",
            )
            mock_renderer.generate_pdf.assert_called_once_with(SAMPLE_RENDERED_ERROR)

            with open(pdf_file_path, "rb") as f:
                assert f.read() == SAMPLE_PDF_BYTES

        finally:
            os.unlink(yaml_file_path)
            os.unlink(pdf_file_path)

    @pytest.mark.asyncio
    async def test_show_previews(self, resume_service, mock_renderer):
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
                await resume_service.show_previews(
                    file_path=yaml_file.name,
                    on_preview_updated=preview_recorder.on_preview_updated,
                    template=ResumeTemplate.MINIMAL_BLUE,
                )

            assert preview_recorder.previews == [SAMPLE_RENDERED_RESUME] * 3, "The preview should be updated 3 times."

            mock_renderer.render_resume.assert_has_calls(
                [
                    call(initial_data, ResumeTemplate.MINIMAL_BLUE),
                    call(first_change_data, ResumeTemplate.MINIMAL_BLUE),
                    call(second_change_data, ResumeTemplate.MINIMAL_BLUE),
                ]
            )

    @pytest.mark.asyncio
    async def test_rendering_the_error_page_when_file_open_fails(self, resume_service: ResumeService, mock_renderer):
        preview_recorder = PreviewRecorder()

        file_change_simulator = FileChangeSimulator(file_content_list=[])
        fake_path = "/a/file/that/is/not/there.yaml"

        with patch("src.service.awatch", file_change_simulator.fake_awatch):
            await resume_service.show_previews(
                file_path=fake_path,
                on_preview_updated=preview_recorder.on_preview_updated,
                template=ResumeTemplate.MINIMAL_BLUE,
            )

        assert preview_recorder.previews == [SAMPLE_RENDERED_ERROR], "The rendered error page should be sent out."
        mock_renderer.render_resume.assert_not_called()
        mock_renderer.render_error.assert_called_once_with(f"Could not open file: {fake_path}")

    @pytest.mark.asyncio
    async def test_resume_data_validation_error(self, resume_service, mock_renderer):
        library_error_message = "Missing required field: 'experience'"
        resume_data_validation_error = ResumeDataValidationError(
            jsonschema.exceptions.ValidationError(library_error_message)
        )
        mock_renderer.render_resume.side_effect = resume_data_validation_error

        test_data = {"name": "Test User"}

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml") as yaml_file:
            yaml.dump(test_data, yaml_file)

            file_change_simulator = FileChangeSimulator(file_content_list=[])

            preview_recorder = PreviewRecorder()
            with patch("src.service.awatch", file_change_simulator.fake_awatch):
                await resume_service.show_previews(
                    file_path=yaml_file.name,
                    on_preview_updated=preview_recorder.on_preview_updated,
                    template=ResumeTemplate.MINIMAL_BLUE,
                )

            assert preview_recorder.previews == [SAMPLE_RENDERED_ERROR], "The rendered error page should be sent out."
            mock_renderer.render_resume.assert_called_once_with(test_data, ResumeTemplate.MINIMAL_BLUE)
            mock_renderer.render_error.assert_called_once_with(
                f"Failed to validate resume data: {library_error_message}",
            )

    def test_create_new_resume(self, resume_service):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_path = temp_dir_path / "my_resume.yaml"

            result = ResumeService.create_new_resume(str(output_path))

            assert isinstance(result, NewResumeResult)
            assert result.resume_path == output_path
            assert result.schema_path == temp_dir_path / "cv.schema.json"

            assert output_path.exists()
            assert (temp_dir_path / "cv.schema.json").exists()

            self._assert_files_equal(PROJECT_ROOT / "cv.sample.yaml", output_path)
            self._assert_files_equal(PROJECT_ROOT / "cv.schema.json", temp_dir_path / "cv.schema.json")

    def test_create_new_resume_with_existing_directory(self, resume_service):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_path = temp_dir_path / "my_resume.yaml"

            temp_dir_path.mkdir(exist_ok=True)

            ResumeService.create_new_resume(str(output_path))

    def _assert_files_equal(self, path1: Path, path2: Path):
        with open(path1, "r") as f1, open(path2, "r") as f2:
            assert f1.read() == f2.read()
