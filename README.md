# StudyTrack

StudyTrack is a command-line tool for students who want a simple way to track
where their study time goes. It records study sessions by course, summarizes
weekly work, and helps compare actual study time against course goals.

## Usage

Install from a GitHub repository with `uv`:

```bash
uv add "git+https://github.com/<your-username>/studytrack.git"
```

Show the installed version:

```bash
study version
```

Start a study session for a course:

```bash
study start DSC40
```

Stop the active session:

```bash
study stop
```

Add a note when stopping a session:

```bash
study stop --note "Reviewed BFS and DFS"
```

View study time for the current week:

```bash
study week
```

View lifetime totals by course:

```bash
study stats
```

Set a weekly study goal for a course:

```bash
study goal DSC40 10
```

Check progress toward weekly goals:

```bash
study progress
```

View the current and longest study streak:

```bash
study streak
```

StudyTrack stores data locally in JSON so it can stay lightweight, inspectable,
and easy to back up.
