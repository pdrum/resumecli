import typer

app = typer.Typer()

@app.command()
def preview():
    import uvicorn
    typer.echo("Previewing...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

@app.command()
def build():
    """Build the resume or project."""
    typer.echo("Building...")

@app.command()
def new():
    """Create a new resume or project."""
    typer.echo("Creating new...")

if __name__ == "__main__":
    app()
