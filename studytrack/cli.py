"""Command-line interface for StudyTrack."""

import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

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


def parse_session_date(session: dict[str, object]) -> date | None:
    """Return a session date, or None when the saved value is invalid."""
    session_date_text = session.get("date")
    if not isinstance(session_date_text, str):
        return None

    try:
        return date.fromisoformat(session_date_text)
    except ValueError:
        return None


def weekly_minutes_by_course(sessions: list[dict[str, object]]) -> dict[str, int]:
    """Return this week's completed study minutes grouped by course."""
    week_start, week_end = current_week_bounds()
    totals: dict[str, int] = {}

    for session in sessions:
        session_date = parse_session_date(session)
        duration = session.get("duration_minutes")
        course = session.get("course")

        if session_date is None:
            continue
        if not isinstance(duration, int):
            continue
        if not isinstance(course, str):
            continue

        if week_start <= session_date <= week_end:
            totals[course] = totals.get(course, 0) + duration

    return totals


def today_minutes_by_course(sessions: list[dict[str, object]]) -> dict[str, int]:
    """Return today's completed study minutes grouped by course."""
    today = date.today()
    totals: dict[str, int] = {}

    for session in sessions:
        session_date = parse_session_date(session)
        duration = session.get("duration_minutes")
        course = session.get("course")

        if session_date != today:
            continue
        if not isinstance(duration, int):
            continue
        if not isinstance(course, str):
            continue

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


def study_dates(sessions: list[dict[str, object]]) -> set[date]:
    """Return unique dates with completed study sessions."""
    return {
        session_date
        for session in sessions
        if (session_date := parse_session_date(session)) is not None
    }


def current_streak(dates: set[date], today: date | None = None) -> int:
    """Return the number of consecutive study days ending today or yesterday."""
    if not dates:
        return 0

    current_date = today or date.today()
    if current_date not in dates and current_date - timedelta(days=1) in dates:
        current_date -= timedelta(days=1)

    streak_count = 0
    while current_date in dates:
        streak_count += 1
        current_date -= timedelta(days=1)

    return streak_count


def longest_streak(dates: set[date]) -> int:
    """Return the longest run of consecutive study days."""
    if not dates:
        return 0

    longest = 0
    for study_date in dates:
        if study_date - timedelta(days=1) in dates:
            continue

        streak_count = 1
        next_date = study_date + timedelta(days=1)
        while next_date in dates:
            streak_count += 1
            next_date += timedelta(days=1)

        longest = max(longest, streak_count)

    return longest


def completed_courses(sessions: list[dict[str, object]]) -> set[str]:
    """Return courses with completed sessions."""
    return {
        course
        for session in sessions
        if isinstance(course := session.get("course"), str)
    }


def latest_session_index(sessions: list[dict[str, object]]) -> int | None:
    """Return the index of the most recently started completed session."""
    latest_index: int | None = None
    latest_started_at = ""

    for index, session in enumerate(sessions):
        started_at = session.get("started_at")
        if not isinstance(started_at, str):
            continue
        if latest_index is None or started_at > latest_started_at:
            latest_index = index
            latest_started_at = started_at

    return latest_index


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
def status() -> None:
    """Show the current active study session, if any."""
    data = load_data()
    active_session = data["active_session"]
    if active_session is None:
        typer.echo("No active study session.")
        raise typer.Exit()

    course = active_session.get("course", "unknown course")
    started_at = datetime.fromisoformat(str(active_session["started_at"]))
    now = datetime.now().astimezone()
    elapsed_minutes = max(0, round((now - started_at).total_seconds() / 60))

    typer.echo(f"Currently studying {course}")
    typer.echo(f"Started: {started_at.strftime('%I:%M %p')}")
    typer.echo(f"Elapsed: {format_duration(elapsed_minutes)}")


@app.command()
def today() -> None:
    """Show study totals for today."""
    data = load_data()
    today_totals = today_minutes_by_course(data["sessions"])
    if not today_totals:
        typer.echo("No study sessions logged today.")
        raise typer.Exit()

    print_totals_report("Today", today_totals)


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
def courses() -> None:
    """List courses found in sessions and goals."""
    data = load_data()
    course_names = completed_courses(data["sessions"]) | set(data["goals"])
    active_session = data["active_session"]
    if active_session is not None and isinstance(
        active_course := active_session.get("course"),
        str,
    ):
        course_names.add(active_course)

    if not course_names:
        typer.echo("No courses found yet. Run 'study start COURSE' first.")
        raise typer.Exit()

    typer.echo("Courses")
    typer.echo()
    for course in sorted(course_names):
        typer.echo(course)


@app.command()
def history(
    course: str,
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum sessions to show."),
) -> None:
    """Show recent sessions for a course."""
    if limit <= 0:
        typer.echo("History limit must be greater than 0.")
        raise typer.Exit(1)

    data = load_data()
    course_name = course.upper()
    sessions = [
        session
        for session in data["sessions"]
        if session.get("course") == course_name
        and parse_session_date(session) is not None
    ]
    if not sessions:
        typer.echo(f"No sessions logged for {course_name}.")
        raise typer.Exit()

    sessions.sort(key=lambda session: str(session.get("started_at", "")), reverse=True)

    typer.echo(f"{course_name} History")
    for session in sessions[:limit]:
        session_date = parse_session_date(session)
        duration = session.get("duration_minutes")
        if session_date is None or not isinstance(duration, int):
            continue

        typer.echo()
        typer.echo(f"{session_date.strftime('%b %d')} - {format_hours(duration)}")

        note = session.get("note")
        if isinstance(note, str) and note:
            typer.echo(note)


@app.command()
def streak() -> None:
    """Show current and longest study streaks."""
    data = load_data()
    dates = study_dates(data["sessions"])
    if not dates:
        typer.echo("No completed study sessions yet. Run 'study start COURSE' first.")
        raise typer.Exit()

    typer.echo(f"Current streak: {current_streak(dates)} days")
    typer.echo(f"Longest streak: {longest_streak(dates)} days")


@app.command("delete-last")
def delete_last() -> None:
    """Delete the most recently completed study session."""
    data = load_data()
    session_index = latest_session_index(data["sessions"])
    if session_index is None:
        typer.echo("No completed study sessions to delete.")
        raise typer.Exit()

    deleted_session = data["sessions"].pop(session_index)
    save_data(data)

    course = deleted_session.get("course", "unknown course")
    duration = deleted_session.get("duration_minutes")
    if isinstance(duration, int):
        typer.echo(f"Deleted last session: {course}, {format_duration(duration)}.")
    else:
        typer.echo(f"Deleted last session: {course}.")


@app.command()
def export(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="CSV file to write. Prints to the terminal by default.",
    ),
) -> None:
    """Export completed sessions as CSV."""
    data = load_data()
    sessions = data["sessions"]
    if not sessions:
        typer.echo("No completed study sessions to export.")
        raise typer.Exit()

    fieldnames = [
        "course",
        "date",
        "started_at",
        "ended_at",
        "duration_minutes",
        "note",
    ]

    if output is None:
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(sessions)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sessions)

    typer.echo(f"Exported {len(sessions)} sessions to {output}.")


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
