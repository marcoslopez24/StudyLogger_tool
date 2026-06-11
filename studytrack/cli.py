"""Command-line interface for StudyTrack."""

import typer

app = typer.Typer(help="Track study sessions and review study progress.")


@app.callback()
def main() -> None:
    """Track study sessions and review study progress."""


@app.command()
def version() -> None:
    """Show the installed StudyTrack version."""
    from studytrack import __version__

    typer.echo(f"StudyTrack {__version__}")
