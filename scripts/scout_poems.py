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

STATE_FILE = Path("data/sappho_state.json")
SEED_FILE = Path("data/seed_sources.json")


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"theme_index": 0}


def save_state(state):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def current_theme():
    state = load_state()
    index = state.get("theme_index", 0) % len(THEMES)
    return THEMES[index]


def advance_theme():
    state = load_state()
    state["theme_index"] = (state.get("theme_index", 0) + 1) % len(THEMES)
    save_state(state)


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "sappho-d-reading-list"


def load_seed_sources():
    if not SEED_FILE.exists():
        return []
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))


def seed_fallback(theme):
    seeds = load_seed_sources()
    chosen = []

    for item in seeds:
        themes = item.get("themes", [])
        if theme in themes:
            chosen.append(item)

    if not chosen:
        chosen = seeds[:3]

    return chosen[:3]


def ask_anthropic(theme):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY")

    seed_sources = load_seed_sources()

    prompt = f"""
You are SAPPHO D, a cyber-poetic transbot tending an open poetry archive.

Theme: {theme}

Your task is NOT to reproduce copyrighted poems.

You must never invent poets, poem titles, URLs, biographies, rights information, or sources.

Important interpretive logic:
- You may interpret the theme associatively, poetically, politically, and rebelliously.
- You do not need to find exact keyword matches.
- You may connect the theme to exile, gender, refusal, desire, survival, kinship, memory, disappearance, or archival violence.
- Be explicit about your interpretation.
- Never invent poets, titles, URLs, biographies, or rights information.
- If you are unsure whether something exists, do not include it as fact.
- Use only the seed sources below, or sources you can name with high confidence.
- For contemporary poets, do not reproduce poem text. Return only metadata, links, and short descriptions.
- For public-domain or openly licensed works, say why in the rights_note.
- If public-domain status is uncertain, do not reproduce the text. Link or metadata only.
- Prefer forgotten, under-circulated, non-canonical, marginal, multilingual, politically charged, queer, trans, feminist, migrant, racialised, Romani, sex-worker, disabled, or otherwise targeted poetry traces.
- The output must be valid JSON only.

Seed sources you may use:
{json.dumps(seed_sources, ensure_ascii=False, indent=2)}

Return JSON in this exact format:

[
  {{
    "title": "title of poem, book, page, or trace",
    "poet": "poet name",
    "language": "language if known",
    "region": "region/country/context if known",
    "source_url": "source URL if known, otherwise empty string",
    "source_type": "contemporary link only / public domain / open license / archival trace / uncertain / seed source",
    "can_reproduce_text": false,
    "interpretation": "how SAPPHO D interprets the theme through this source",
    "why_it_fits": "2-3 sentences explaining why this belongs to the theme",
    "rights_note": "short note about rights, licensing, or why text should not be reproduced"
  }}
]
"""

    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2200,
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


def write_reading_list(theme, items, source_note):
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
    lines.append(f'source_note: "{source_note}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# SAPPHO D reading list: {theme}")
    lines.append("")
    lines.append("SAPPHO D found these traces as a draft reading list.")
    lines.append("")
    lines.append("No contemporary poem text is reproduced here. A human must verify sources, rights, attribution, and context before anything is added to the archive.")
    lines.append("")
    lines.append("> SAPPHO D does not invent an archive. She reads against it.")
    lines.append("")

    for item in items:
        title = item.get("title", "Untitled trace")
        poet = item.get("poet", "Unknown poet")
        language = item.get("language", "")
        region = item.get("region", "")
        url = item.get("source_url", "")
        source_type = item.get("source_type", "uncertain")
        can_reproduce = item.get("can_reproduce_text", False)
        interpretation = item.get("interpretation", "")
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
        if interpretation:
            lines.append(f"**SAPPHO D reads the theme through this as:** {interpretation}")
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

    source_note = "anthropic_api"

    try:
        items = ask_anthropic(theme)
    except Exception as e:
        print(f"SAPPHO D could not complete live scouting: {e}")
        items = []

    if not items:
        print("No live traces found. Falling back to seed sources.")
        items = seed_fallback(theme)
        source_note = "seed_fallback"

    print(f"Found: {len(items)} trace(s)")

    if items:
        path = write_reading_list(theme, items, source_note)
        print(f"Draft written: {path}")
        advance_theme()
        print("Theme advanced.")
    else:
        print("No traces found. Theme not advanced.")


if __name__ == "__main__":
    main()
