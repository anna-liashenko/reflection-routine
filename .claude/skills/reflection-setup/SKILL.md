---
name: reflection-setup
description: One-time interactive setup for the reflection routine. Use when the user says 'set up reflections', 'install the reflection routine', 'configure reflection-routine', or runs /reflection-setup. Asks four choices (delivery over Telegram or in chat; local scheduled task or cloud routine; which connectors; data folder), writes config.json into the data folder, and creates the schedule.
---

# Reflection routine setup

You are setting up a twice-daily reflection routine for the person in front of you. Ask, don't assume; everything below is a choice they make. Use AskUserQuestion for the choices, in this order: when (times and timezone), which messenger, which tools to pull context from, where to store the answers, and where it runs. Never ask for or accept a bot token in chat; tokens go into a file or an environment variable that they write themselves.

Plugin root: the folder containing this skill's parent `.claude/skills/` directory. The script is `<repo root>/evening_reflection.py`.

## 0. When

Ask for the morning time, the evening time and their IANA timezone. Defaults to offer: 06:30 and 21:00. Note the evening run must happen when they are winding down, since the night-safe rule assumes that.

## 1. Where the reflections live (the data folder)

Reflections are personal, so they never go into this repository. Ask for a data folder. Default suggestion: `~/Documents/reflections`. If they chose the cloud in step 3, the data folder must be a git repository with a private GitHub remote (the cloud routine clones it, writes replies, and pushes back). Offer to run `git init` and `gh repo create <name> --private --source . --push` for them if `gh` is installed and logged in; otherwise tell them the two commands.

Create the folder if needed. Write `.gitignore` there with `.telegram-config.json`, `*.token`, `__pycache__/`. Create `README.md` if absent with one paragraph: one file per ISO week (`YYYY-Wnn.md`), replies filed verbatim, `telegram-inbox.jsonl` and `.telegram-offset` are routine state and must stay committed.

Point the script at it: either `export REFLECTIONS_DIR=<path>` in their shell profile, or make `<repo root>/data` a symlink (`ln -s`) or Windows junction (`mklink /J`) to the folder. The junction is simplest locally.

## 2. Which messenger: Telegram or none

- **Telegram** (questions arrive on their phone, replies are filed automatically). Walk them through it: open @BotFather in Telegram, `/newbot`, pick a name, copy the token. They write `{"bot_token": "<token>", "chat_id": ""}` into `<data folder>/.telegram-config.json` themselves. Then they open the new bot and press Start, and run `python <repo root>/evening_reflection.py test`, which discovers the chat id and sends a test message. For the cloud (step 3) the token is instead set as `REFLECTION_BOT_TOKEN` and `REFLECTION_CHAT_ID` on the cloud environment at https://claude.ai/code (environment settings), never in the repo.
- **None** (no bot; `delivery: "chat"`). The routine writes the morning and evening questions into the week file under the day's heading as `**Morning questions:**` / `**Evening questions:**` lines and the person answers them in a Claude Code session or by editing the file. Nothing is sent anywhere.

## 3. Where it runs: local or cloud

- **Local scheduled task** (Claude Code desktop app, machine must be awake at the time). Create two scheduled tasks with the scheduled-tasks tool if it is available (`create_scheduled_task`), otherwise write the two task files by hand under `~/.claude/scheduled-tasks/<id>/SKILL.md`. Prompts:
  - `morning-reflection`, cron `30 6 * * *` local time: "Invoke the `reflection-run` skill with argument `morning` and follow it exactly."
  - `evening-reflection`, cron `0 21 * * *` local time: "Invoke the `reflection-run` skill with argument `evening` and follow it exactly."
  Use the times from step 0.
- **Cloud routine** (runs in Anthropic's cloud whether or not the laptop is open). They fork this repo first if they want to change anything (the cloud clones from GitHub, not from disk). Use the `/schedule` skill twice, with the prompts in `ROUTINE-morning.md` and `ROUTINE-evening.md`, both repos (their fork or this repo, and the data repo) as git sources, and the connectors from step 4 attached. Cron is UTC: convert the chosen local times and tell them the clocks-change caveat (recompute in spring and autumn, or accept a one-hour drift). Tell them to set the two secrets on the environment before the first run.

## 4. Which tools to pull context from

Multi-select: Google Calendar (shape of the day in the morning, what happened in the evening), Gmail (evening only: good news and consequential replies, never obligations), Todoist (tasks due in the morning, done today in the evening). Any can be off. Locally these need the matching MCP connector in Claude Code; in the cloud they need the claude.ai connector attached to the routine (https://claude.ai/customize/connectors). Do not claim a connector is missing without checking.

## 5. Write the config

`<data folder>/config.json`:

```json
{
  "name": "<first name>",
  "timezone": "<IANA zone, e.g. Europe/London>",
  "delivery": "telegram" | "chat",
  "runs_in": "local" | "cloud",
  "connectors": { "calendar": true, "gmail": true, "todoist": true },
  "morning_hour": 6, "evening_hour": 21
}
```

Commit it to the data repo if one exists. Then run the morning flow once by hand (`reflection-run morning`) so they see the shape of a message before the first scheduled run, and tell them in two lines what will happen tomorrow and where their replies will end up.
