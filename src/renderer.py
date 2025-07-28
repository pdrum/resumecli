import json
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, cast

import jsonschema
from jinja2 import Environment, FileSystemLoader, select_autoescape


class ResumeTemplate(Enum):
    DEFAULT = "resume.html"


class ResumeDataValidationError(Exception):
    def __init__(self, cause: jsonschema.exceptions.ValidationError):
        super().__init__(f"Invalid resume data format: {cause}")


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
        return resolved_template.render(**resume_data)  # type: ignore[no-any-return]

    def render_error(self, error_message: str) -> str:
        template = self.env.get_template("error.html")
        return template.render(error_message=error_message, json_schema=self._schema)  # type: ignore[no-any-return]

    def _validate_resume_data(self, resume_data: Dict[str, Any]) -> None:
        try:
            jsonschema.validate(instance=resume_data, schema=self._schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ResumeDataValidationError(e) from e

    @cached_property
    def _schema(self) -> Dict[str, Any]:
        with open(self._schema_path, "r") as schema_file:
            return cast(Dict[str, Any], json.load(schema_file))
