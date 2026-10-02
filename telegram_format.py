"""Markdown-to-Telegram-HTML formatting shared by the reflection sender.
Copied from digest-routine/send_to_telegram.py so this repo stands alone."""
import html
import re

CHUNK_LIMIT = 3800  # Telegram hard limit is 4096; leave headroom for tags.


def to_telegram_html(md):
    """Convert the digest's markdown subset to the HTML Telegram accepts."""
    out = []
    for line in md.split("\n"):
        if line.strip() in ("---", "***"):
            out.append("")
            continue
        # Extract links before escaping so the URLs survive intact.
        links = []

        def stash(match):
            links.append((match.group(1), match.group(2)))
            return f"\x00{len(links) - 1}\x00"

        line = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", stash, line)
        line = html.escape(line, quote=False)

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            line = f"<b>{heading.group(2)}</b>"
        else:
            line = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", line)
            line = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<i>\1</i>", line)

        def restore(match):
            text, url = links[int(match.group(1))]
            return f'<a href="{html.escape(url, quote=True)}">{html.escape(text, quote=False)}</a>'

        line = re.sub(r"\x00(\d+)\x00", restore, line)
        out.append(line)
    return "\n".join(out)


def chunk(text, limit=CHUNK_LIMIT):
    """Split on blank lines so no item is torn in half mid-tag."""
    blocks = text.split("\n\n")
    chunks, current = [], ""
    for block in blocks:
        candidate = block if not current else current + "\n\n" + block
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(block) > limit:
            cut = block.rfind("\n", 0, limit)
            cut = cut if cut > 0 else limit
            chunks.append(block[:cut])
            block = block[cut:].lstrip("\n")
        current = block
    if current:
        chunks.append(current)
    return chunks
