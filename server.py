"""
QUEERDOS Community Poetry Capsule
Gemini server — pip install jetforce pyyaml
Run: python server.py --hostname your.domain
"""

import yaml
from pathlib import Path
from jetforce import GeminiServer, JetforceApplication, Response, Status

BASE  = Path(__file__).parent
POEMS = BASE / "poems"

app = JetforceApplication()

def load_poem(path):
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        meta = yaml.safe_load(parts[1])
        body = parts[2].strip()
    else:
        meta = {}
        body = raw.strip()
    meta["body"] = body
    meta.setdefault("slug",   path.stem)
    meta.setdefault("title",  path.stem.replace("-", " ").title())
    meta.setdefault("author", "anonymous")
    meta.setdefault("date",   "undated")
    return meta

def all_poems():
    poems = []
    for f in POEMS.glob("*.md"):
        if f.name.startswith("_"):
            continue
        try:
            poems.append(load_poem(f))
        except Exception:
            pass
    def sort_key(p):
        d = p.get("date", "")
        return str(d) if d and str(d) != "undated" else "0000-00-00"
    return sorted(poems, key=sort_key, reverse=True)

def footer():
    return (
        "\n\n─────────────────────────────\n"
        "=> /           ← home\n"
        "=> /submit     submit a poem\n"
        "=> /about      about this archive\n\n"
        "QUEERDOS community poetry · Berlin\n"
        "production@queerdos.eu\n"
    )

@app.route("/")
def index(request):
    poems = all_poems()
    body  = "# QUEERDOS poetry\n"
    body += "## An open community archive\n\n"
    body += f"{len(poems)} poem{'s' if len(poems) != 1 else ''} in the archive.\n\n"
    current_year = None
    for p in poems:
        yr = str(p.get("date", ""))[:4] or "undated"
        if yr != current_year:
            body += f"\n### {yr}\n\n"
            current_year = yr
        body += f"=> /poems/{p['slug']}  {p['title']} — {p.get('author','anonymous')}\n"
    body += "\n─────────────────────────────\n"
    body += "=> /submit  ✦ submit a poem\n"
    body += "=> /about   ✦ about this space\n"
    body += "=> /contribute  ✦ how to contribute via Git\n"
    return Response(Status.SUCCESS, "text/gemini", body.encode())

@app.route("/poems/(?P<slug>[a-z0-9_-]+)")
def poem(request, slug):
    path = POEMS / f"{slug}.md"
    if not path.exists():
        return Response(Status.NOT_FOUND, "Poem not found.")
    p = load_poem(path)
    body  = f"# {p['title']}\n"
    body += f"## {p.get('author','anonymous')}\n\n"
    if p.get("content_note"):
        body += f"[ content note: {p['content_note']} ]\n\n"
    body += p["body"]
    if p.get("bio"):
        body += f"\n\n─────────────────────────────\n{p['author']}: {p['bio']}\n"
    body += "\n\n─────────────────────────────\n"
    body += "=> /  ← back to archive\n"
    body += footer()
    return Response(Status.SUCCESS, "text/gemini", body.encode())

@app.route("/about")
def about(request):
    body = (
        "# About this archive\n\n"
        "Open archive of trans* and queer voices.\n"
        "No tracking. No ads. No algorithm.\n\n"
        "Built by IQTIA Berlin.\n\n"
        "=> https://queerdos.eu  queerdos.eu\n"
        "=> /contribute  How to submit via Git\n"
    )
    body += footer()
    return Response(Status.SUCCESS, "text/gemini", body.encode())

@app.route("/contribute")
def contribute(request):
    body = (
        "# How to submit a poem\n\n"
        "Fork github.com/IQTIA/queerdo-poetry-repo\n"
        "Add your poem to the poems/ folder\n"
        "Open a pull request\n\n"
        "Or email: production@queerdos.eu\n\n"
        "=> mailto:production@queerdos.eu  production@queerdos.eu\n"
        "=> https://github.com/IQTIA/queerdo-poetry-repo  GitHub\n"
    )
    body += footer()
    return Response(Status.SUCCESS, "text/gemini", body.encode())

@app.route("/submit")
def submit(request):
    if not request.query:
        return Response(Status.INPUT, "Your name or handle (or leave blank for anonymous):")
    return Response(Status.REDIRECT_TEMPORARY, "/contribute")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostname", default="localhost")
    parser.add_argument("--port",     type=int, default=1965)
    parser.add_argument("--certfile", default="cert.pem")
    parser.add_argument("--keyfile",  default="key.pem")
    args = parser.parse_args()
    server = GeminiServer(app, host=args.hostname, port=args.port,
                          certfile=args.certfile, keyfile=args.keyfile)
    print(f"✦ QUEERDOS poetry · gemini://{args.hostname}:{args.port}")
    server.run()
