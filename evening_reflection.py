#!/usr/bin/env python3
"""Reflection over Telegram, on its OWN bot (separate from the digest bot).

Usage:
    python evening_reflection.py test                          # discover chat_id, send a test message
    python evening_reflection.py send <message.md> [--morning]  # send one message (🌙 evening by default, ☀️ with --morning)
    python evening_reflection.py pull                          # fetch new replies into telegram-inbox.jsonl
    python evening_reflection.py pending                       # print unfiled replies as JSON lines
    python evening_reflection.py mark-filed                    # mark every pending reply as filed
    python evening_reflection.py week-file [ISO-date|ISO-datetime]
    python evening_reflection.py local-hour

Config: .telegram-config.json next to this script:
    {"bot_token": "<token from @BotFather for the reflection bot>", "chat_id": ""}
The token is a credential. Anna writes it into the file herself; it never goes in a prompt,
a skill, or a chat. chat_id is discovered on first run after she presses Start in the bot.

Inbox lines: {"at": ISO time UTC, "text": ..., "reply_to": snippet, "kind": "morning"|"evening",
"filed": false}. kind comes from the message she replied to (☀️ or 🌙), else from the hour
(04:00-13:00 UK = morning, otherwise evening). Sent messages are stamped "🌙 YYYY-MM-DD" on
their first line; a reply to a stamped message is filed under that date whenever it arrives.

Filing rule: an answer written after midnight and before 04:00 UK belongs to the day that
just ended. `week-file` applies that rule when given an ISO timestamp.
"""

import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))


def data_dir(env_name):
    """Where the personal files live: $REFLECTIONS_DIR, else ./data next to this script.
    The code repo is shareable; the data repo is private and cloned alongside."""
    d = os.environ.get(env_name) or os.path.join(HERE, "data")
    if not os.path.isdir(d):
        sys.exit(f"Data folder not found: {d}. Set {env_name} or create ./data.")
    return d


DATA = data_dir("REFLECTIONS_DIR")
CONFIG = os.path.join(DATA, ".telegram-config.json")
OFFSET = os.path.join(DATA, ".telegram-offset")
INBOX = os.path.join(DATA, "telegram-inbox.jsonl")


def load_settings():
    """Optional $REFLECTIONS_DIR/config.json written by the reflection-setup skill."""
    path = os.path.join(DATA, "config.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


SETTINGS = load_settings()
LONDON = ZoneInfo(os.environ.get("REFLECTION_TZ") or SETTINGS.get("timezone") or "Europe/London")
EVENING = "\U0001F319"  # 🌙
MORNING = "☀️"  # ☀️
API = "https://api.telegram.org/bot{token}/{method}"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from telegram_format import to_telegram_html, chunk  # noqa: E402


def api(token, method, fields):
    req = urllib.request.Request(
        API.format(token=token, method=method), data=urllib.parse.urlencode(fields).encode()
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Telegram API error {exc.code} on {method}: {exc.read().decode(errors='replace')}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach Telegram: {exc.reason}")


def load_config():
    token = os.environ.get("REFLECTION_BOT_TOKEN")
    if token:
        chat_id = os.environ.get("REFLECTION_CHAT_ID") or discover_chat_id(token)
        return {"bot_token": token, "chat_id": chat_id}
    if not os.path.exists(CONFIG):
        sys.exit(
            "No reflection-bot config found.\n"
            f"Create {CONFIG} containing:\n"
            '  {"bot_token": "<token from @BotFather>", "chat_id": ""}\n'
            "Then open the bot in Telegram, press Start, and run: python evening_reflection.py test"
        )
    with open(CONFIG, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if not cfg.get("bot_token"):
        sys.exit("Reflection-bot config is missing bot_token.")
    if not cfg.get("chat_id"):
        cfg["chat_id"] = discover_chat_id(cfg["bot_token"])
        with open(CONFIG, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2)
        print(f"Discovered and saved chat_id {cfg['chat_id']}.")
    return cfg


def discover_chat_id(token):
    data = api(token, "getUpdates", {"timeout": 0})
    chats = {}
    for upd in data.get("result", []):
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat") or {}
        if chat.get("type") == "private" and chat.get("id"):
            chats[chat["id"]] = chat.get("username") or chat.get("first_name", "")
    if not chats:
        sys.exit(
            "No chat_id yet. A bot cannot message you first: open the reflection bot in Telegram, "
            "press Start (or send it anything), then run this again."
        )
    chat_id = list(chats)[-1]
    print(f"Found private chat {chat_id} ({chats[chat_id]}).")
    return str(chat_id)


def send(path, morning=False):
    cfg = load_config()
    mark = MORNING if morning else EVENING
    with open(path, encoding="utf-8") as fh:
        raw = fh.read().strip()
    # The mark carries the date so a reply filed later still lands on the right day.
    stamp = dt.datetime.now(LONDON).strftime("%Y-%m-%d")
    if raw.startswith((EVENING, MORNING)):
        raw = raw.split(" ", 1)[1] if " " in raw else ""
    raw = f"{mark} {stamp}" + chr(10) + raw
    words = len(raw.split())
    if words > 160:
        sys.exit(f"REFUSED: message is {words} words, ceiling is 160. Cut it. Nothing was sent.")
    for part in chunk(to_telegram_html(raw)):
        api(
            cfg["bot_token"],
            "sendMessage",
            {"chat_id": cfg["chat_id"], "text": part, "parse_mode": "HTML", "disable_web_page_preview": "true"},
        )
    print(f"Sent {'morning' if morning else 'evening'} reflection ({words} words).")


def test():
    cfg = load_config()
    me = api(cfg["bot_token"], "getMe", {}).get("result", {}).get("username", "unknown")
    api(
        cfg["bot_token"],
        "sendMessage",
        {
            "chat_id": cfg["chat_id"],
            "text": "<b>Reflection bot is wired up.</b>\nMorning questions at 6:30, evening questions at 10pm. Reply here in any form.",
            "parse_mode": "HTML",
        },
    )
    print(f"Connected as @{me} and sent a test message to chat {cfg['chat_id']}.")


def kind_of(reply_to, local_dt):
    if reply_to.startswith(MORNING):
        return "morning"
    if reply_to.startswith(EVENING):
        return "evening"
    return "morning" if 4 <= local_dt.hour < 13 else "evening"


def pull():
    cfg = load_config()
    offset = None
    if os.path.exists(OFFSET):
        with open(OFFSET, encoding="utf-8") as fh:
            offset = int(fh.read().strip() or 0) or None
    params = {"timeout": 0}
    if offset:
        params["offset"] = offset
    updates = api(cfg["bot_token"], "getUpdates", params).get("result", [])
    new, last_id = [], (offset - 1 if offset else None)
    for upd in updates:
        last_id = upd["update_id"]
        msg = upd.get("message")
        if not msg or str(msg.get("chat", {}).get("id")) != str(cfg["chat_id"]):
            continue
        text = (msg.get("text") or "").strip()
        if not text or text.startswith("/"):  # bot commands like /start are not reflections
            continue
        when = dt.datetime.fromtimestamp(msg["date"], dt.timezone.utc)
        reply_to = (msg.get("reply_to_message") or {}).get("text", "")
        new.append(
            {
                "at": when.isoformat(),
                "text": text,
                "reply_to": reply_to[:120],
                "kind": kind_of(reply_to, when.astimezone(LONDON)),
                "filed": False,
            }
        )
    if new:
        with open(INBOX, "a", encoding="utf-8") as fh:
            for entry in new:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if last_id is not None:
        with open(OFFSET, "w", encoding="utf-8") as fh:
            fh.write(str(last_id + 1))
    print(f"New replies pulled: {len(new)}")


def _read_inbox():
    if not os.path.exists(INBOX):
        return []
    out = []
    with open(INBOX, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def stamped_day(reply_to):
    """If she replied to a stamped message (🌙 2026-09-28 ...), that date wins over the clock."""
    m = re.match(r"^(?:🌙|☀️?)\s*(\d{4}-\d{2}-\d{2})", reply_to or "")
    return m.group(1) if m else None


def reflection_day(local_dt):
    """After midnight but before 04:00 counts as the day that just ended."""
    if local_dt.hour < 4:
        return (local_dt - dt.timedelta(days=1)).date()
    return local_dt.date()


def pending():
    entries = [e for e in _read_inbox() if not e.get("filed")]
    if not entries:
        print("No pending reflection replies.")
        return
    for entry in entries:
        local = dt.datetime.fromisoformat(entry["at"]).astimezone(LONDON)
        entry = dict(entry)
        entry["local"] = local.strftime("%Y-%m-%d %H:%M")
        entry["belongs_to"] = stamped_day(entry.get("reply_to", "")) or reflection_day(local).isoformat()
        print(json.dumps(entry, ensure_ascii=False))


def mark_filed():
    entries = _read_inbox()
    changed = sum(1 for e in entries if not e.get("filed"))
    for entry in entries:
        entry["filed"] = True
    with open(INBOX, "w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Marked {changed} reply(ies) as filed.")


def week_file(arg=None):
    if arg:
        try:
            when = dt.datetime.fromisoformat(arg)
            if when.tzinfo is None:
                when = when.replace(tzinfo=LONDON)
            day = reflection_day(when.astimezone(LONDON))
        except ValueError:
            day = dt.date.fromisoformat(arg)
    else:
        day = reflection_day(dt.datetime.now(LONDON))
    y, w, _ = day.isocalendar()
    print(os.path.join(DATA, f"{y}-W{w:02d}.md"))
    print(f"day={day.isoformat()} weekday={day.strftime('%a')}")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__)
    cmd, rest = argv[0], argv[1:]
    if cmd == "test":
        test()
    elif cmd == "send" and rest:
        send(rest[0], morning="--morning" in rest)
    elif cmd == "pull":
        pull()
    elif cmd == "pending":
        pending()
    elif cmd == "mark-filed":
        mark_filed()
    elif cmd == "week-file":
        week_file(rest[0] if rest else None)
    elif cmd == "local-hour":
        print(dt.datetime.now(LONDON).hour)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
