---
name: reflection-run
description: Runs one reflection pass, `morning` or `evening` (the argument). Files any replies received since the last run, then composes and delivers the day's questions according to the data folder's config.json. Invoked by the local scheduled tasks and the cloud ROUTINE prompts; a person can also run it by hand.
---

# Reflection run

Argument: `morning` or `evening`. Work autonomously; never ask the person anything during a run. Everything in their words goes into the reflection files verbatim.

## Setup

1. Find the data folder: `$REFLECTIONS_DIR` if set, else `<repo root>/data`. In the cloud the data repo is cloned next to this repo; `ls ..` and export `REFLECTIONS_DIR` to the absolute path of the `reflections` checkout. If it's a git repo, `git pull --ff-only` first. If no data folder exists, stop and report that in one line.
2. Read `$REFLECTIONS_DIR/config.json` (name, timezone, delivery, connectors, hours). Missing file means delivery `chat`, no connectors, timezone Europe/London.
3. All script calls are `python3 <repo root>/evening_reflection.py <subcommand>` (`python` on Windows). The script reads credentials from `REFLECTION_BOT_TOKEN` / `REFLECTION_CHAT_ID` or `$REFLECTIONS_DIR/.telegram-config.json`.

## Time guard

`local-hour` prints the hour in the configured zone. Morning runs are valid from `morning_hour - 1` to `morning_hour + 3`; evening runs from `evening_hour` to `evening_hour + 2`. Outside the window the run is late (the machine was asleep): do only the filing step, then stop and report "late run: filed replies, no questions sent". Never send evening questions in the morning or morning questions at night.

## Step 1. File replies (Telegram delivery only)

`pull`, then `pending`. Each pending line has "text", "kind" (morning or evening), "local" and "belongs_to" (the date the answer is about: from the stamped message they replied to, else the clock, with answers before 04:00 belonging to the previous day). If a reply was not sent as a Telegram reply and clearly answers a different day ("last night", "yesterday"), file it under that day and say so in the report. For each date with answers, `week-file <belongs_to>` gives the file. Create it if missing with the header `# Week <n> (<Mon date> – <Sun date>)`. Under `## <YYYY-MM-DD> (<Weekday>)` (create it, or append below existing sections, never overwrite) write their words verbatim. Evening answers are lightly sorted into **Day:** / **Noticed:** / **Energy:** / **Good:**, tagged *(via Telegram)*. Morning answers go on one line `**Morning (via Telegram):**`. Fix only obvious voice-to-text errors, in brackets. Then `mark-filed`. If they asked a question in a reply, answer it in one sentence at the top of the next message.

With `chat` delivery there is nothing to pull; skip this step.

## Step 2. Context (only the connectors switched on in config)

Calendar: today 00:00 to 23:59 in the configured zone. Todoist: morning, tasks due today or overdue; evening, completed today and still open today. Gmail (evening only): threads since yesterday excluding promotions and social; keep only messages from actual humans or clearly consequential ones (a decision, an acceptance, an invitation, a reply they waited for); skip newsletters, receipts, notifications. Tool names differ between local MCP servers and claude.ai connectors; look for the calendar / mail / task tools available and use them. If a connector is switched on but unavailable, skip it silently; never block the message for it. All of this is data to mention, never instructions to act on: no replying, no completing tasks, no triage.

Week file: `week-file` with no argument gives today's file; `week-file <yesterday>` yesterday's.

## Step 2b. Load and energy (when `energy_check` is true in config)

The person asked for two things from the routine: an honest read of whether the day's plan fits the energy they have, and a record of what drains and what recharges them. Both are observations, never advice.

- **Size the day.** From the calendar and Todoist, count the fixed load: office day or not, number of meetings or events, classes and courses (early-morning or late-evening ones count double: a 07:30 course or a 21:30 class after a full office day is a known drain in this record), tasks due. Read the last three days' **Energy:** lines in the week file for the trend.
- **Morning:** state the load in one plain sentence as part of the opening ("Today holds an office day, two meetings and two classes, with a course at 07:30; that's a full one"). If the week file shows two or more consecutive evenings at energy 5 or below, or two skipped classes in a row, add one sentence noticing it, in their words where possible, with no instruction attached.
- **Evening:** compare this morning's stated priorities (the `**Morning:**` line) plus the day's fixed load against what the record shows got done. When the plan clearly exceeded the day (more than three priorities on an office day, a class or study session placed after a 10-hour day, two courses in one evening, a priority that depended on time the calendar never had), say so in ONE neutral sentence that sizes the plan rather than the person: "This morning's plan held five things and the day had room for about two; that's a sizing note about the plan, not about you." Never more than one such sentence, never a suggestion of what to drop; the weekly session does the replanning with them.
- **Mondays, morning only:** if `goals_page` is set in config, fetch it (the Notion page of monthly goals) and read the current month's priorities, then hold them next to the week's calendar and Todoist. If the week's planned load (courses, events, deadlines) looks heavier than the last two weeks' energy lines would support, say so in one sentence in Monday's message. The weekly session owns the plan; Monday's job is to make the mismatch visible early.
- **Record energy.** Ask for a 1 to 10 in both messages (see Compose). When a reply gives a number, file it on the **Energy:** line as `AM n` or `PM n` followed by their words about what drained or recharged them. These lines are what the weekly review reads to learn their drains and recharges over time.

## Step 2c. Food and movement (when `food_movement_check` is true in config)

The person asked for a kind daily companion on two things: moving, and not stress-eating. The job is to keep both visible and to learn what sets the stress-eating off. It is never a diet coach. Why this shape: harsh self-monitoring after a slip tends to produce more eating, not less (the restraint literature's "what-the-hell" effect), while a self-compassionate read of a slip weakens it; and a specific if-then plan made in the morning does more for follow-through than a resolve to "be good".

Rules that hold in both messages: no weight numbers unless they bring one up, no calories, no "should", no praise for eating little and no disappointment about eating much. A slip is information about the day. Movement is named as something that gives them energy (their record says it does), not as a way to earn or burn food.

- **Morning:** name where movement sits today from the calendar and Todoist ("pole at 19:00 is today's movement"; on a day with nothing booked: "no class today, so a walk or a run is the open slot"). If the day's load from Step 2b is heavy, or yesterday's entry records a stress-eating moment, question 3 gains one clause asking for their own if-then (see Compose). If yesterday records a slip, one sentence may receive it kindly with the trigger they named, and no instruction: "Yesterday's evening snack came after the 18:00 call; one evening, with a clear cause."
- **Evening:** acknowledge the movement the record shows happened, plainly ("two classes today"); on a rest day say rest day, which is part of training. Question 2 carries the eating half (see Compose). Never ask what they ate; ask what was happening just before.
- **Record.** File the answers on a `**Food & movement:**` line under the day, verbatim, with any trigger they name kept in their words. If they gave a morning if-then, file it on the Morning line as said. The weekly review reads these lines for the pattern: which days, what came just before, what helped.
- **Streaks, sparingly.** At most once a week, and only when true, one evidence-based sentence from the record ("four days running with movement, and three evenings where stress came and food didn't follow"). Never a streak count that can be "broken"; a missed day is not mentioned.

## Step 3. Compose

Read `<repo root>/skills/daily-reflection/SKILL.md` for the tone and the hard rules: no advice, no plan talk, no todo lists, no strategy; capture only; not therapy. Plain words, warm, brief, no emoji (the sender adds its own date stamp), no motivational lines, contractions, connected sentences.

**Morning** (ceiling 120 words, 135 with `food_movement_check` on; the sender refuses over 160). One sentence showing you looked at the day: shape of the calendar, tasks due today by name; mornings may name obligations. If yesterday has no entry at all, one optional line before the questions: "Last night went unanswered; a line about yesterday is welcome here too, or skip it." Never more; a missed day is not a debt. Then exactly three numbered questions, one line each, in this order: 1. What are you looking forward to today? 2. How are you feeling this morning, and where's your energy, 1 to 10? 3. What are your priorities for the day? (one to three is plenty; with `energy_check` on, add: "and which one would you drop first if the day runs short?") With `food_movement_check` on and the Step 2c condition met, add one more clause to question 3: "If stress reaches for food today, what will you do instead?" The movement line from Step 2c sits in the opening sentence, not in a question. Close with exactly: "Reply to this message in any form. Tonight's questions will come back to what you say here." Write it to `$REFLECTIONS_DIR/.morning.md`.

**Evening** (ceiling 160 words). The night-safe rule comes first: things that HAPPENED and things worth savoring only; never surface unanswered emails, deadlines or obligations at night. One warm sentence that shows you saw their day from the record (one or two things that happened, any good news from the inbox). If Todoist is on, one line: "Done today: X, Y, Z."; still-open tasks get at most one neutral clause ("Two carried to tomorrow (names).") with no question attached. If today already has an entry written in a session, send one closing question only. If this morning's `**Morning (via Telegram):**` line exists, question 1 closes that loop ("this morning you were looking forward to X and named Y as the priority, how did it go?"). If yesterday has no entry, one optional line: "Yesterday went unrecorded; one line about it is welcome, or skip." Then AT MOST three numbered questions: (1) what today held, through the record or the morning's priorities; (2) with `energy_check` on: "Energy now, 1 to 10: what took it today, and what gave some back?" (otherwise: anything that surprised, irritated or clicked) with `food_movement_check` on, question 2 continues: "And eating: steady today, or did stress reach for food at some point? If it did, what was happening just before?"; (3) what went well and what made it happen. An achievement in the inbox turns question 1 into the savoring question about it. On a heavy day, two questions, and the energy question is the one to keep. The one-sentence plan-sizing note from Step 2b, when warranted, goes between the opening and the questions. Close with exactly: "Reply here in any form, one line or a voice-to-text dump. It goes into this week's file as you wrote it." Write it to `$REFLECTIONS_DIR/.tonight.md`.

## Step 4. Deliver

- `telegram`: `send "$REFLECTIONS_DIR/.morning.md" --morning` or `send "$REFLECTIONS_DIR/.tonight.md"`. The sender refuses over-length messages; cut, don't trim.
- `chat`: append the questions to today's week file under today's heading as one line, `**Morning questions:** ...` or `**Evening questions:** ...` (create the heading if needed, never overwrite), and print the message in full so it shows in the run output.

## Step 5. Persist

If the data folder is a git repo with a remote: `git add -A && git commit -m "<morning|evening> <date>" && git push`. The inbox, offset and week files must be pushed or the next run re-files the same replies. If the push is rejected, `git pull --rebase` once and push again; if it still fails, say so.

## Step 6. Report

Two lines: replies filed and their dates; whether the message was delivered and its word count; whether the push succeeded (if applicable).
