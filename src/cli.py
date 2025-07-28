import os

import typer
import uvicorn

import server
from renderer import ResumeRenderer
from service import ResumeService

app = typer.Typer()


@app.command()
def preview(file: str = typer.Argument(..., help="Path to the source YAML file for the resume")) -> None:
    typer.echo(f"Previewing {file}...")
    os.environ[server.ENV_KEY_RESUME_SOURCE_FILE] = os.path.abspath(file)
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)


@app.command()
def build(
    file: str = typer.Argument(..., help="Path to the source YAML file for the resume"),
    output: str = typer.Option("output.pdf", help="Output PDF file path"),
) -> None:
    """Build the resume or project."""
    service = ResumeService(renderer=ResumeRenderer())
    service.generate_pdf(csv_data_path=file, output_path=output)
    typer.echo("Building...")


@app.command()
def new() -> None:
    """Create a new resume or project."""
    typer.echo("Creating new...")


if __name__ == "__main__":
    app()
