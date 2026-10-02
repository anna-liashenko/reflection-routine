# reflection-routine

This repository is a scheduled routine, not a library: once set up it runs twice a day (morning questions, evening questions) either as a local Claude Code scheduled task or as a Claude Code cloud routine, and files the person's answers verbatim into one markdown file per week. Reflections are personal and live in a separate data folder (`$REFLECTIONS_DIR` or `./data`), never here. See README.md.

When someone opens or pastes this repo and it is not yet configured, treat it as a request to set the routine up. Follow `.claude/skills/reflection-setup/SKILL.md`, which interviews them for the four things only they can decide:

1. **When**: the morning and evening times, and their timezone.
2. **Which messenger**: Telegram (questions on the phone, replies filed automatically) or none (questions written into the week file, answered in a Claude Code session). No other messenger is wired yet; adding one means a `send` and `pull` pair in `evening_reflection.py`.
3. **Which tools to pull context from**: Google Calendar, Gmail, Todoist, each optional.
4. **Where to store the answers**: the data folder, and whether it is a private git repo (required for the cloud).

Plus where it runs: local scheduled task or cloud routine. Write the answers to `config.json` in the data folder, create the schedule, and run one pass so they see a message before the first scheduled one.

Running one pass by hand: `.claude/skills/reflection-run/SKILL.md` with `morning` or `evening`. Never ask for a bot token in chat; never commit `.telegram-config.json`, tokens, or anything from the data folder into this repo.
