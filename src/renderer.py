import json
from enum import Enum
from typing import Any, Dict

import jsonschema
from jinja2 import Environment, FileSystemLoader, select_autoescape


class ResumeTemplate(Enum):
    DEFAULT = "resume.html"


class ResumeDataValidationError(Exception):
    def __init__(self, cause: jsonschema.exceptions.ValidationError):
        super().__init__(f"Invalid resume data format: {cause}")


class ResumeRenderer:
    _template_dir = "../templates"
    _schema_path = "../cv.schema.json"

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
        return template.render(error_message=error_message)  # type: ignore[no-any-return]

    def _validate_resume_data(self, resume_data: Dict[str, Any]) -> None:
        with open(self._schema_path, "r") as schema_file:
            schema = json.load(schema_file)

        try:
            jsonschema.validate(instance=resume_data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ResumeDataValidationError(e) from e
