import json
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, cast

import jsonschema
import markdown  # type: ignore[import]
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from weasyprint import HTML


class ResumeTemplate(Enum):
    DEFAULT = "minimal_blue.html"
    MINIMAL_BLUE = "minimal_blue.html"


class ResumeDataValidationError(Exception):
    def __init__(self, cause: jsonschema.exceptions.ValidationError):
        super().__init__(f"Failed to validate resume data: {cause}")


class ResumeRenderer:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    _template_dir = PROJECT_ROOT / "templates"
    _schema_path = PROJECT_ROOT / "cv.schema.json"

    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(self._template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_resume(self, resume_data: Dict[str, Any], resume_template: ResumeTemplate) -> str:
        self._validate_resume_data(resume_data)
        resolved_template = self.env.get_template(resume_template.value)
        resume_data_with_processed_markdown = self._markdown_to_html_for_dict(resume_data)
        return resolved_template.render(**resume_data_with_processed_markdown)  # type: ignore[no-any-return]

    def render_error(self, error_message: str) -> str:
        template = self.env.get_template("error.html")
        return template.render(error_message=error_message, json_schema=self._schema)  # type: ignore[no-any-return]

    def generate_pdf(self, rendered_resume: str) -> bytes:
        return cast(bytes, HTML(string=rendered_resume).write_pdf())

    def _validate_resume_data(self, resume_data: Dict[str, Any]) -> None:
        try:
            jsonschema.validate(instance=resume_data, schema=self._schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ResumeDataValidationError(e) from e

    @cached_property
    def _schema(self) -> Dict[str, Any]:
        with open(self._schema_path, "r") as schema_file:
            return cast(Dict[str, Any], json.load(schema_file))

    def _markdown_to_html(self, markdown_text: str) -> Markup:
        """Convert Markdown text to HTML."""
        html = markdown.markdown(markdown_text.strip(), extensions=["fenced_code", "tables"])
        if html.startswith("<p>") and html.endswith("</p>"):
            html = html[3:-4]
        return Markup(html)

    def _markdown_to_html_for_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively convert Markdown strings in a dictionary to HTML."""
        for key, value in data.items():
            data[key] = self._turn_to_html_recursively(value)
        return data

    def _turn_to_html_recursively(self, data: Any) -> Any:
        if isinstance(data, str):
            return self._markdown_to_html(data)
        if isinstance(data, dict):
            return {key: self._turn_to_html_recursively(value) for key, value in data.items()}
        if isinstance(data, list):
            return [self._turn_to_html_recursively(item) for item in data]
        if isinstance(data, tuple):
            return tuple(self._turn_to_html_recursively(item) for item in data)
        return data
