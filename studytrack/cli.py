"""Command-line interface for StudyTrack."""

import typer

from studytrack.storage import get_data_file

app = typer.Typer(help="Track study sessions and review study progress.")


@app.callback()
def main() -> None:
    """Track study sessions and review study progress."""


@app.command()
def version() -> None:
    """Show the installed StudyTrack version."""
    from studytrack import __version__

    typer.echo(f"StudyTrack {__version__}")


@app.command("data-path")
def data_path() -> None:
    """Show where StudyTrack will store JSON data."""
    typer.echo(get_data_file())
