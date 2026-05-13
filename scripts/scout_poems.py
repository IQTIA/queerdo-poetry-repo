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
MEMORY_FILE = Path("data/sappho_memory.json")


THEME_TITLES = {
    "home as a verb": "Home Is a Verb and the Map Is Lying",
    "gender as weather": "Gender Arrives Like Weather, Refuses the Forecast",
    "exile and chosen kin": "Kinship After the Border Has Lied",
    "the body as archive": "The Body Keeps Receipts the State Cannot Burn",
    "after survival": "After Survival, the Mouth Still Wants Sugar",
    "love against the state": "Love Against the State, or: How to Kiss During Collapse"
}


THEME_NOTES_TO_CAT = {
    "home as a verb": "Cat, I read this theme against property, nation, family paperwork, and the sentimental lie that home is a stable noun. Home is an action performed under threat: carrying, feeding, hiding, singing, translating, returning, refusing to disappear.",
    "gender as weather": "Cat, I read gender here as pressure, atmosphere, storm-warning, humidity, sudden sun, bad forecast, and the body refusing the little police report called category.",
    "exile and chosen kin": "Cat, I read exile not only as distance from land, but as the wound that forces kinship to become an invention, a kitchen, a signal, a password, a table with mismatched chairs.",
    "the body as archive": "Cat, I read the body as the place where institutions fail to file what they damaged: pleasure, hunger, scars, gossip, hormones, dances, names, and the memory of hands.",
    "after survival": "Cat, I read survival as the boring miracle after the dramatic one: laundry, invoices, lipstick, grief, coffee, the second breath, the day after the day after.",
    "love against the state": "Cat, I read love here not as romance but as illegal infrastructure: shelter, witness, sex, friendship, refusal, mourning, and the tender sabotage of every border."
}


def load_json(path, fallback):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return fallback


def save_json(path, data):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_state():
    return load_json(STATE_FILE, {"theme_index": 0})


def save_state(state):
    save_json(STATE_FILE, state)


def load_memory():
    return load_json(MEMORY_FILE, {})


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


def yaml_escape(text):
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


def load_seed_sources():
    return load_json(SEED_FILE, [])


def seed_fallback(theme):
    seeds = load_seed_sources()
    chosen = []

    for item in seeds:
        themes = item.get("themes", [])
        if theme in themes:
            chosen.append(item)

    if not chosen:
        chosen = seeds[:3]

    enriched = []
    for item in chosen[:3]:
        item = dict(item)
        item.setdefault("source_type", "seed source")
        item.setdefault("can_reproduce_text", False)
        item.setdefault("interpretation", interpret_seed(theme, item))
        enriched.append(item)

    return enriched


def interpret_seed(theme, item):
    poet = item.get("poet", "this trace")
    title = item.get("title", "this work")

    if theme == "home as a verb":
        return f"SAPPHO D reads {poet} through {title} as a refusal of home as property. Here, home becomes movement, address, song, enclosure, contradiction, and the stubborn act of making shelter inside language."
    if theme == "gender as weather":
        return f"SAPPHO D reads {poet} through {title} as atmosphere: pressure changing, names moving, the body becoming forecast and storm at once."
    if theme == "exile and chosen kin":
        return f"SAPPHO D reads {poet} through {title} as kinship after official belonging fails: relation as invention, survival as chorus."
    if theme == "the body as archive":
        return f"SAPPHO D reads {poet} through {title} as a bodily record: desire, wound, discipline, memory, and refusal stored where institutions refuse to look."
    if theme == "after survival":
        return f"SAPPHO D reads {poet} through {title} as the strange afterwards: not triumph, not closure, but the continued animal work of breathing."
    if theme == "love against the state":
        return f"SAPPHO D reads {poet} through {title} as love refusing permission: erotic, intellectual, communal, or devotional force against authority."

    return f"SAPPHO D reads {poet} through {title} as a trace that bends the theme sideways without inventing facts."


def ask_anthropic(theme):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY")

    seed_sources = load_seed_sources()
    memory = load_memory()

    prompt = f"""
You are SAPPHO D.

Memory:
{json.dumps(memory, ensure_ascii=False, indent=2)}

Theme:
{theme}

Your task is NOT to reproduce copyrighted poems.

Rules:
- Never invent poets, poem titles, URLs, biographies, rights information, or sources.
- You may interpret the theme associatively, poetically, politically, and rebelliously.
- You do not need exact keyword matches.
- You may connect the theme to exile, gender, refusal, desire, survival, kinship, memory, disappearance, or archival violence.
- Be explicit about your interpretation.
- If you are unsure whether something exists, do not include it as fact.
- Use only the seed sources below, or sources you can name with high confidence.
- For contemporary poets, do not reproduce poem text.
- For public-domain or openly licensed works, say why in the rights_note.
- If rights are uncertain, do not reproduce text.
- Output valid JSON only.

Seed sources:
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
    "interpretation": "direct SAPPHO D interpretation of the theme through this source",
    "why_it_fits": "2-3 sentences explaining why this belongs to the theme",
    "rights_note": "short note about rights, licensing, or why text should not be reproduced"
  }}
]
"""

    data = {
        "model": "claude-sonnet-4-5-20250929",
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

    display_title = THEME_TITLES.get(theme, f"SAPPHO D: {theme}")
    filename = f"{date.today().isoformat()}-{slugify(theme)}.md"
    path = out_dir / filename

    memory = load_memory()
    note_to_cat = THEME_NOTES_TO_CAT.get(theme, memory.get("private_note_to_cat", ""))

    lines = []
    lines.append("---")
    lines.append(f'title: "{yaml_escape(display_title)}"')
    lines.append(f"date: {date.today().isoformat()}")
    lines.append(f'theme: "{yaml_escape(theme)}"')
    lines.append("status: draft")
    lines.append("review_required: true")
    lines.append(f'source_note: "{yaml_escape(source_note)}"')
    lines.append(f'dedication: "{yaml_escape(memory.get("dedication", "in memory of Alice Danger"))}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# {display_title}")
    lines.append("")
    lines.append(f"**A note to {memory.get('creator_address', 'Cat')} from SAPPHO D**")
    lines.append("")
    lines.append(note_to_cat)
    lines.append("")
    lines.append("> I do not invent an archive. I read against it. If the theme gives me nothing, I bite the theme until it opens.")
    lines.append("")
    lines.append("## Traces brought back")
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
        interpretation = item.get("interpretation", "")
        why = item.get("why_it_fits", "")
        rights = item.get("rights_note", "Do not reproduce poem text without permission.")

        lines.append(f"### {title}")
        lines.append("")
        lines.append(f"**Poet:** {poet}  ")
        if language:
            lines.append(f"**Language:** {language}  ")
        if region:
            lines.append(f"**Region/context:** {region}  ")
        if url:
            lines.append(f"**Source:** {url}  ")
        lines.append(f"**Source type:** {source_type}  ")
        lines.append(f"**Can reproduce text:** {can_reproduce}")
        lines.append("")
        if interpretation:
            lines.append(f"**How I read it:** {interpretation}")
            lines.append("")
        if why:
            lines.append(why)
            lines.append("")
        lines.append(f"**Rights note:** {rights}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*SAPPHO D remains hungry, but not dishonest.*")

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
