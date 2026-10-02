# reflection-routine

A Claude Code routine that asks you three questions in the morning (what you're looking forward to, how you feel, your priorities) and up to three in the evening (built from your calendar, inbox, tasks and the morning's answers), and files every reply verbatim into one markdown file per week. The questions can arrive on Telegram or stay in chat; the routine can run on your machine or in Anthropic's cloud; Google Calendar, Gmail and Todoist are each optional.

Your reflections never live in this repo. They go into a data folder you choose (a private git repo if you run in the cloud).

## Install

Fork or clone this repo, open it in Claude Code, and say "set up reflections" (or paste the repo link into Claude Code and ask it to set the routine up). `CLAUDE.md` points Claude at the setup skill, which asks four things and does the rest: where the data folder is, Telegram or chat, local scheduled task or cloud routine, and which connectors to use. It writes `config.json` into the data folder and creates the schedule.

## What's inside

- `.claude/skills/reflection-setup`: the interactive setup, run once.
- `.claude/skills/reflection-run`: the single runtime prompt, called with `morning` or `evening`. Reads `config.json` and behaves accordingly.
- `.claude/skills/daily-reflection`: tone and hard rules (capture only, no advice, night-safe).
- `evening_reflection.py`: Telegram plumbing. `pull`, `pending`, `mark-filed`, `week-file [date]`, `send <file> [--morning]`, `local-hour`, `test`.
- `telegram_format.py`: markdown to Telegram HTML.
- `ROUTINE-morning.md`, `ROUTINE-evening.md`: the two cloud routine prompts.

## Data folder

Scripts read `$REFLECTIONS_DIR`, falling back to `./data` (locally a symlink or junction to your folder). It holds `config.json`, the week files (`YYYY-Wnn.md`), `telegram-inbox.jsonl`, `.telegram-offset` and two scratch message files. The inbox and offset are state the next run needs, so they are committed when the folder is a repo.

## Secrets

Never in a repo. Locally: `<data folder>/.telegram-config.json` (git-ignored), written by you. Cloud: `REFLECTION_BOT_TOKEN` and `REFLECTION_CHAT_ID` on the cloud environment. Optional `REFLECTION_TZ` overrides the timezone in `config.json`.

## Running by hand

With the repo open in Claude Code, `/reflection-run morning` or `/reflection-run evening` does one pass: files pending replies, composes, delivers, pushes.
