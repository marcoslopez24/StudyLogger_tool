"""Command-line interface for StudyTrack."""

from datetime import datetime

import typer

from studytrack.storage import get_data_file, load_data, save_data

app = typer.Typer(help="Track study sessions and review study progress.")


def format_duration(minutes: int) -> str:
    """Format a duration for command output."""
    if minutes < 60:
        unit = "min" if minutes == 1 else "mins"
        return f"{minutes} {unit}"
    return f"{minutes / 60:.1f} hrs"


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


@app.command()
def start(course: str) -> None:
    """Start a study session for a course."""
    data = load_data()
    if data["active_session"] is not None:
        active_course = data["active_session"].get("course", "unknown course")
        typer.echo(f"Already studying {active_course}. Run 'study stop' first.")
        raise typer.Exit(1)

    course_name = course.upper()
    started_at = datetime.now().astimezone()
    data["active_session"] = {
        "course": course_name,
        "started_at": started_at.isoformat(timespec="seconds"),
    }
    save_data(data)
    typer.echo(f"Started studying {course_name} at {started_at.strftime('%I:%M %p')}.")


@app.command()
def stop(
    note: str | None = typer.Option(None, "--note", "-n", help="Note for the session."),
) -> None:
    """Stop the active study session."""
    data = load_data()
    active_session = data["active_session"]
    if active_session is None:
        typer.echo("No active study session. Run 'study start COURSE' first.")
        raise typer.Exit(1)

    course = str(active_session["course"])
    started_at = datetime.fromisoformat(str(active_session["started_at"]))
    ended_at = datetime.now().astimezone()
    duration_minutes = max(1, round((ended_at - started_at).total_seconds() / 60))

    session = {
        "course": course,
        "date": ended_at.date().isoformat(),
        "started_at": started_at.isoformat(timespec="seconds"),
        "ended_at": ended_at.isoformat(timespec="seconds"),
        "duration_minutes": duration_minutes,
    }
    if note:
        session["note"] = note

    data["sessions"].append(session)
    data["active_session"] = None
    save_data(data)

    typer.echo(f"Stopped {course}. Logged {format_duration(duration_minutes)}.")
