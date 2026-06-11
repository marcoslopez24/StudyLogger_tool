"""Command-line interface for StudyTrack."""

from datetime import date, datetime, timedelta

import typer

from studytrack.storage import get_data_file, load_data, save_data

app = typer.Typer(help="Track study sessions and review study progress.")


def format_duration(minutes: int) -> str:
    """Format a duration for command output."""
    if minutes < 60:
        unit = "min" if minutes == 1 else "mins"
        return f"{minutes} {unit}"
    return f"{minutes / 60:.1f} hrs"


def format_hours(minutes: int) -> str:
    """Format minutes as hours with one decimal place."""
    return f"{minutes / 60:.1f} hrs"


def current_week_bounds(today: date | None = None) -> tuple[date, date]:
    """Return Monday and Sunday for the current week."""
    current_date = today or date.today()
    week_start = current_date - timedelta(days=current_date.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def weekly_minutes_by_course(sessions: list[dict[str, object]]) -> dict[str, int]:
    """Return this week's completed study minutes grouped by course."""
    week_start, week_end = current_week_bounds()
    totals: dict[str, int] = {}

    for session in sessions:
        session_date_text = session.get("date")
        duration = session.get("duration_minutes")
        course = session.get("course")

        if not isinstance(session_date_text, str):
            continue
        if not isinstance(duration, int):
            continue
        if not isinstance(course, str):
            continue

        try:
            session_date = date.fromisoformat(session_date_text)
        except ValueError:
            continue

        if week_start <= session_date <= week_end:
            totals[course] = totals.get(course, 0) + duration

    return totals


def lifetime_minutes_by_course(sessions: list[dict[str, object]]) -> dict[str, int]:
    """Return all completed study minutes grouped by course."""
    totals: dict[str, int] = {}

    for session in sessions:
        duration = session.get("duration_minutes")
        course = session.get("course")

        if not isinstance(duration, int):
            continue
        if not isinstance(course, str):
            continue

        totals[course] = totals.get(course, 0) + duration

    return totals


def print_totals_report(title: str, totals: dict[str, int]) -> None:
    """Print a course totals report."""
    typer.echo(title)
    typer.echo()

    for course in sorted(totals):
        typer.echo(f"{course}: {format_hours(totals[course])}")

    typer.echo()
    typer.echo(f"Total: {format_hours(sum(totals.values()))}")


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


@app.command()
def week() -> None:
    """Show study totals for the current week."""
    data = load_data()
    weekly_totals = weekly_minutes_by_course(data["sessions"])
    if not weekly_totals:
        typer.echo("No study sessions logged this week.")
        raise typer.Exit()

    print_totals_report("This Week", weekly_totals)


@app.command()
def stats() -> None:
    """Show lifetime study totals by course."""
    data = load_data()
    lifetime_totals = lifetime_minutes_by_course(data["sessions"])
    if not lifetime_totals:
        typer.echo("No completed study sessions yet. Run 'study start COURSE' first.")
        raise typer.Exit()

    print_totals_report("Lifetime Totals", lifetime_totals)


@app.command()
def goal(course: str, hours: float) -> None:
    """Set a weekly study goal for a course."""
    if hours <= 0:
        typer.echo("Goal hours must be greater than 0.")
        raise typer.Exit(1)

    data = load_data()
    course_name = course.upper()
    data["goals"][course_name] = hours
    save_data(data)
    typer.echo(f"Set weekly goal for {course_name}: {hours:.1f} hrs.")


@app.command()
def progress() -> None:
    """Show progress toward weekly study goals."""
    data = load_data()
    goals = data["goals"]
    if not goals:
        typer.echo("No goals set yet. Run 'study goal COURSE HOURS' first.")
        raise typer.Exit()

    weekly_totals = weekly_minutes_by_course(data["sessions"])
    typer.echo("Weekly Progress")
    typer.echo()

    for course in sorted(goals):
        goal_hours = goals[course]
        studied_minutes = weekly_totals.get(course, 0)
        studied_hours = studied_minutes / 60
        percent = min(100, round((studied_hours / goal_hours) * 100))
        typer.echo(f"{course}: {studied_hours:.1f} / {goal_hours:.1f} hrs ({percent}%)")

    total_minutes = sum(weekly_totals.get(course, 0) for course in goals)
    typer.echo()
    typer.echo(f"Total toward goals: {format_hours(total_minutes)}")
