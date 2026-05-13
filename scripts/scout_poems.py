from pathlib import Path
from datetime import date
import os
import re
import json
import urllib.request

THEMES = [
    "home as a verb",
    "gender as weather",
    "exile and chosen kin",
    "the body as archive",
    "after survival",
    "love against the state",
]

def current_theme():
    today = date.today()
    index = ((today.day // 15) + today.month) % len(THEMES)
    return THEMES[index]

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "sappho-d-reading-list"

def ask_anthropic(theme):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY")

    prompt = f"""
You are SAPPHO D, a cyber-poetic transbot tending an open poetry archive.

Theme: {theme}

Your task is NOT to reproduce copyrighted poems.

Important search logic:
- First look for contemporary queer, trans, feminist, migrant, racialised, Romani, diasporic, sex-worker, disabled, or otherwise targeted poets.
- For contemporary poets, do not reproduce poem text. Return only metadata, links, and short descriptions.
- As a secondary option, you may include older historical poets, public-domain texts, archival fragments, oral-literary traces, or openly licensed works.
- If a work is clearly public domain or openly licensed, say why in the rights_note.
- If public-domain status is uncertain, do not reproduce the text. Link only.
- Prefer forgotten, under-circulated, non-canonical, marginal, multilingual, or politically charged poetry traces.
- Do not invent URLs.
- Do not invent poets.
- If you cannot verify a source, say so clearly.
- The output must be valid JSON only.

Return JSON in this exact format:

[
  {{
    "title": "title of poem, book, page, or trace",
    "poet": "poet name",
    "language": "language if known",
    "region": "region/country/context if known",
    "source_url": "source URL if known, otherwise empty string",
    "source_type": "contemporary link only / public domain / open license / archival trace / uncertain",
    "can_reproduce_text": false,
    "why_it_fits": "2-3 sentences explaining why this belongs to the theme",
    "rights_note": "short note about rights, licensing, or why text should not be reproduced"
  }}
]
"""

    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1800,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))

    text = result["content"][0]["text"].strip()
    return parse_json(text)

def parse_json(text):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        print("Parse error:", text[:800])
        return []

def write_reading_list(theme, items):
    out_dir = Path("scouted_poems")
    out_dir.mkdir(exist_ok=True)

    filename = f"{date.today().isoformat()}-{slugify(theme)}.md"
    path = out_dir / filename

    lines = []
    lines.append("---")
    lines.append(f'title: "SAPPHO D reading list: {theme}"')
    lines.append(f"date: {date.today().isoformat()}")
    lines.append(f'theme: "{theme}"')
    lines.append("status: draft")
    lines.append("review_required: true")
    lines.append("---")
    lines.append("")
    lines.append(f"# SAPPHO D reading list: {theme}")
    lines.append("")
    lines.append("SAPPHO D found these traces as a draft reading list.")
    lines.append("")
    lines.append("No contemporary poem text is reproduced here. A human must verify sources, rights, attribution, and context before anything is added to the archive.")
    lines.append("")

    for item in items:
        title = item.get("title", "Untitled trace")
        poet = item.get("poet", "Unknown poet")
        language = item.get("language", "")
        region = item.get("region", "")
        url = item.get("source_url", "")
        source_type = item.get("source_type", "uncertain")
        can_reproduce = item.get("can_reproduce_text", False)
        why = item.get("why_it_fits", "")
        rights = item.get("rights_note", "Do not reproduce poem text without permission.")

        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"**Poet:** {poet}")
        if language:
            lines.append(f"**Language:** {language}")
        if region:
            lines.append(f"**Region/context:** {region}")
        if url:
            lines.append(f"**Source:** {url}")
        lines.append(f"**Source type:** {source_type}")
        lines.append(f"**Can reproduce text:** {can_reproduce}")
        lines.append("")
        lines.append(why)
        lines.append("")
        lines.append(f"**Rights note:** {rights}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path

def main():
    theme = current_theme()
    print(f"Theme: {theme}")

    try:
        items = ask_anthropic(theme)
    except Exception as e:
        print(f"SAPPHO D could not complete scouting: {e}")
        items = []

    print(f"Found: {len(items)} trace(s)")

    if items:
        path = write_reading_list(theme, items)
        print(f"Draft written: {path}")

if __name__ == "__main__":
    main()
