#!/usr/bin/env python3
"""Validate poem files in poems/ directory."""

import sys
import yaml
from pathlib import Path

POEMS_DIR = Path(__file__).parent.parent / "poems"
ERRORS = []

def err(filename, msg):
    ERRORS.append(f"  {filename}: {msg}")

def validate(path):
    name = path.name
    raw  = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        err(name, "missing front matter — file must start with ---"); return
    parts = raw.split("---", 2)
    if len(parts) < 3:
        err(name, "front matter not closed — add a second ---"); return
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        err(name, f"invalid YAML: {e}"); return
    if not meta.get("title"):
        err(name, "missing 'title' field")
    date_val = meta.get("date")
    if date_val and str(date_val) != "undated":
        try:
            from datetime import date
            date.fromisoformat(str(date_val))
        except ValueError:
            err(name, f"date must be YYYY-MM-DD, got: {date_val!r}")
    if not parts[2].strip():
        err(name, "poem body is empty")

def main():
    files = [f for f in POEMS_DIR.glob("*.md") if not f.name.startswith("_")]
    if not files:
        print("No poem files found."); sys.exit(0)
    print(f"Validating {len(files)} poem(s)...\n")
    for f in sorted(files):
        validate(f)
    if ERRORS:
        print("Validation failed:\n")
        for e in ERRORS: print(e)
        sys.exit(1)
    else:
        print(f"All {len(files)} poem(s) valid. ✦")

if __name__ == "__main__":
    main()
