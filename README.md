# StudyTrack

StudyTrack is a command-line tool for students who want a simple way to track
where their study time goes. It records study sessions by course, summarizes
daily and weekly work, and helps compare actual study time against course goals.

## Usage

Install from a GitHub repository with `uv`:

```bash
uv add "git+https://github.com/marcoslopez24/StudyLogger_tool.git"
```

Show the installed version:

```bash
study version
```

Show where StudyTrack stores its JSON data:

```bash
study data-path
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

Check whether a session is active:

```bash
study status
```

View study time for today:

```bash
study today
```

View study time for the current week:

```bash
study week
```

View lifetime totals by course:

```bash
study stats
```

List all courses found in sessions and goals:

```bash
study courses
```

Set a weekly study goal for a course:

```bash
study goal DSC40 10
```

Check progress toward weekly goals:

```bash
study progress
```

View recent sessions for a course:

```bash
study history DSC40
study history DSC40 --limit 5
```

View the current and longest study streak:

```bash
study streak
```

Delete the most recently completed session:

```bash
study delete-last
```

Export completed sessions as CSV:

```bash
study export
study export --output sessions.csv
```

StudyTrack stores data locally in JSON so it can stay lightweight, inspectable,
and easy to back up. By default, data is stored at:

```text
~/.studytrack/data.json
```

For testing, you can use a temporary data file without changing your real log:

```bash
STUDYTRACK_DATA_FILE=/private/tmp/studytrack-test.json study start DSC40
```
