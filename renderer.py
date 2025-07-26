import json
from enum import Enum
import jsonschema

from jinja2 import Environment, FileSystemLoader, select_autoescape

class Template(Enum):
    DEFAULT_RESUME = "resume.html"

class ResumeDataValidationError(Exception):
    def __init__(self, cause: jsonschema.exceptions.ValidationError):
        super().__init__(f"Invalid resume data format: {cause}")

class ResumeRenderer:
    _template_dir = "templates"
    _schema_path = "cv.schema.json"

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(self._template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render(self, resume_data, template: Template):
        self._validate_resume_data(resume_data)
        template = self.env.get_template(template.value)
        return template.render(**resume_data)

    def _validate_resume_data(self, resume_data):
        with open(self._schema_path, 'r') as schema_file:
            schema = json.load(schema_file)

        try:
            jsonschema.validate(instance=resume_data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ResumeDataValidationError(e) from e
