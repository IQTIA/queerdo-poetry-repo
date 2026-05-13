#!/usr/bin/env python3
"""
IQTIA biweekly poetry scout
Every two weeks: find 3 queer/trans/intersex/nonbinary poets,
one poem each, all matching the cycle theme.
"""

import os
import re
import json
import anthropic
from pathlib import Path
from datetime import date

THEMES = [
    "borders and belonging",
    "the body as archive",
    "chosen family",
    "grief and survival",
    "language and mother tongue",
    "desire and shame",
    "visibility and invisibility",
    "transition — any kind of crossing",
    "rage and tenderness",
    "home as a verb",
    "memory and erasure",
    "joy as resistance",
    "names we give ourselves",
    "the night and what lives there",
    "solidarity across difference",
    "getting older, queerly",
    "sex and intimacy",
    "the state and our bodies",
    "dreams and futures",
    "ordinary days",
    "romani and migrant voices",
    "disability and crip poetics",
    "religion, spirituality, the sacred",
    "climate and the more-than-human",
    "Berlin and other cities of refuge",
]

def current_theme():
    today = date.today()
    start = date(today.year, 1, 1)
    cycle = ((today - start).days // 14) % len(THEMES)
    return THEMES[cycle]

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    return re.sub(r'-+', '-', s)[:60].strip('-')

def write_poem(poem, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(poem.get('title','untitled'))
    path = output_dir / f"{slug}.md"
    i = 1
    while path.exists():
        path = output_dir / f"{slug}-{i}.md"
        i += 1
    lines = ["---"]
    for key in ['title','author','date','content_note','bio','source_url','license']:
        if poem.get(key):
            lines.append(f'{key}: "{poem[key]}"')
    lines += ["scouted: true", "---", "", poem["body"]]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

def scout(theme):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""You are the poetry scout for IQTIA — Institute for Queer and Trans Autonomy, Berlin.

This cycle theme: "{theme}"

Find 3 real poems by 3 different poets. Each poet must identify as queer, trans*, intersex, or nonbinary. Each poem must be published under an open license (CC0, CC BY, or CC BY-SA). Each poem must relate to the theme.

Return ONLY a JSON array of 3 objects, each with:
- title, author, date (YYYY-MM-DD or year), body (full poem text),
  bio (one sentence), source_url, license, content_note (or null)

No preamble. No markdown fences. Real poets only — do not invent."""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role":"user","content":prompt}]
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r'^```json\s*','',raw)
    raw = re.sub(r'\s*```$','',raw)
    try:
        poems = json.loads(raw)
        return poems if isinstance(poems,list) else [poems]
    except:
        print("Parse error:", raw[:300])
        return []

def main():
    theme = current_theme()
    print(f"Theme: {theme}")
    with open(os.environ.get("GITHUB_ENV","/dev/null"),"a") as f:
        f.write(f"THEME={theme}\n")
    poems = scout(theme)
    print(f"Found: {len(poems)} poem(s)")
    output_dir = Path("scouted_poems")
    for p in poems:
        if not p.get("title") or not p.get("body"):
            continue
        path = write_poem(p, output_dir)
        print(f"  + {p['title']} — {p['author']}")
        print(f"    {p.get('source_url','')}")

if __name__ == "__main__":
    main()
