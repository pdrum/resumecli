import asyncio
import os

import typer
import uvicorn

from src.renderer import ResumeRenderer, ResumeTemplate
from src.server import ENV_KEY_RESUME_SOURCE_FILE, ENV_KEY_RESUME_TEMPLATE_NAME
from src.service import ResumeService

app = typer.Typer()


@app.command()
def preview(
    file: str = typer.Argument(..., help="Path to the source YAML file for the resume"),
    template: ResumeTemplate = typer.Option(ResumeTemplate.MINIMAL_BLUE.value, help="Template to use for the resume"),
) -> None:
    typer.echo(f"Previewing {file}...")
    os.environ[ENV_KEY_RESUME_SOURCE_FILE] = os.path.abspath(file)
    os.environ[ENV_KEY_RESUME_TEMPLATE_NAME] = template.value
    uvicorn.run("src.server:app", host="127.0.0.1", port=8000, reload=True)


@app.command()
def build(
    file: str = typer.Argument(..., help="Path to the source YAML file for the resume"),
    output: str = typer.Option("output.pdf", help="Output PDF file path"),
) -> None:
    typer.echo(f"Building resume from {file}...")

    async def build_resume():
        service = ResumeService(renderer=ResumeRenderer())
        await service.generate_pdf(cv_data_path=file, output_path=output)

    asyncio.run(build_resume())


@app.command()
def new() -> None:
    """Create a new resume or project."""
    typer.echo("Creating new...")


if __name__ == "__main__":
    app()
