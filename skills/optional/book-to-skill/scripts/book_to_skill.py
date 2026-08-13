#!/usr/bin/env python3
"""book-to-skill: turn a PDF, MD, TXT, or URL into a runnable skill folder.

Layout produced:
  ./<skill-name>/
    SKILL.md                 # generated YAML frontmatter + instructions
    references/
      chapter-01.md          # original chapter text
      chapter-02.md
      ...
    assets/
      glossary.json          # extracted concepts
      summary.json           # high-level summary
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path


def read_input(args):
    if args.input:
        p = Path(args.input)
        if not p.exists():
            print("ERROR: input not found: " + str(p))
            sys.exit(1)
        if p.suffix.lower() == ".pdf":
            return extract_pdf(p)
        return p.read_text(encoding="utf-8", errors="replace")
    if args.url:
        with urllib.request.urlopen(args.url, timeout=30) as resp:
            data = resp.read()
        if args.url.lower().endswith(".pdf"):
            return extract_pdf_bytes(data)
        return data.decode("utf-8", errors="replace")
    print("ERROR: --input or --url required")
    sys.exit(1)


def extract_pdf(p):
    try:
        from pypdf import PdfReader
    except ImportError:
        print("ERROR: pypdf not installed. Run: pip install pypdf")
        sys.exit(1)
    reader = PdfReader(str(p))
    parts = []
    for i, page in enumerate(reader.pages):
        parts.append("## Page " + str(i + 1) + "\n\n" + page.extract_text() + "\n")
    return "\n".join(parts)


def extract_pdf_bytes(data):
    try:
        from pypdf import PdfReader
    except ImportError:
        print("ERROR: pypdf not installed. Run: pip install pypdf")
        sys.exit(1)
    import io
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for i, page in enumerate(reader.pages):
        parts.append("## Page " + str(i + 1) + "\n\n" + page.extract_text() + "\n")
    return "\n".join(parts)


def split_into_sections(text):
    """Split text by H1 (#) and H2 (##) markdown headers."""
    lines = text.split("\n")
    sections = []
    current_title = None
    current_body = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            # H1 - flush previous
            if current_title is not None:
                sections.append((current_title, "\n".join(current_body).strip()))
            current_title = stripped[2:].strip()
            current_body = []
        elif stripped.startswith("## "):
            # H2 - flush previous
            if current_title is not None:
                sections.append((current_title, "\n".join(current_body).strip()))
            current_title = stripped[3:].strip()
            current_body = []
        else:
            current_body.append(line)
    if current_title is not None:
        sections.append((current_title, "\n".join(current_body).strip()))
    if not sections and text.strip():
        sections.append(("Full Text", text.strip()))
    return sections[:30]


def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s[:64] or "chapter"


def extract_instructions(body):
    bullets = []
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith(("- ", "* ", "1. ", "2. ", "3. ")):
            bullets.append(line.lstrip("-*0123456789. "))
        elif line.startswith("##") or line.startswith("#"):
            continue
        elif len(line) > 30 and len(line) < 200 and line.endswith("."):
            bullets.append(line)
    return bullets[:10]


def build_skill(text, skill_name, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    refs = out / "references"
    refs.mkdir(exist_ok=True)
    assets = out / "assets"
    assets.mkdir(exist_ok=True)

    sections = split_into_sections(text)
    print("[b2s] " + str(len(sections)) + " sections found")

    chapter_files = []
    glossary = {}
    for idx, (title, body) in enumerate(sections, 1):
        slug = "ch-" + str(idx).zfill(2) + "-" + slugify(title)
        chapter_path = refs / (slug + ".md")
        chapter_path.write_text("# " + title + "\n\n" + body, encoding="utf-8")
        chapter_files.append(str(chapter_path.relative_to(out)))
        # Terms in chapter
        for term in re.findall(r"\*\*([A-Z][A-Za-z0-9 ]{2,30})\*\*", body):
            if term not in glossary:
                glossary[term] = ""

    # SKILL.md frontmatter + body
    fm = "---\nname: " + skill_name + "\ndescription: \"Extracted from source material. Use when the user asks about: " + skill_name.replace("-", " ") + ".\"\nversion: 0.1.0\ntags: [book-to-skill, extracted]\nplatforms: [linux, macos, windows]\n---\n\n"
    body_lines = ["# " + skill_name.replace("-", " "), "", "This skill was auto-extracted from source material using `book-to-skill`.", ""]
    body_lines.append("## Outline\n")
    for idx, (title, _) in enumerate(sections, 1):
        body_lines.append("-" + str(idx) + ". " + title)
    body_lines.append("")
    body_lines.append("## Key concepts\n")
    for term in list(glossary.keys())[:20]:
        body_lines.append("- " + term)
    body_lines.append("")
    body_lines.append("## Reference chapters\n")
    for cf in chapter_files:
        body_lines.append("- `" + cf + "`")

    (out / "SKILL.md").write_text(fm + "\n".join(body_lines), encoding="utf-8")
    (assets / "glossary.json").write_text(json.dumps(glossary, indent=2), encoding="utf-8")
    summary = {"sections": len(sections), "terms": len(glossary), "skill_name": skill_name}
    (assets / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("[b2s] Wrote SKILL.md + " + str(len(chapter_files)) + " reference chapters + glossary.json")
    print("[b2s] Output: " + str(out))


def main():
    p = argparse.ArgumentParser(description="Convert book/PDF/URL into a skill")
    p.add_argument("--input", help="Path to PDF/MD/TXT")
    p.add_argument("--url", help="URL to fetch")
    p.add_argument("--skill-name", default=None, help="Skill name (default: derived from input)")
    p.add_argument("--output-dir", required=True, help="Where to write the skill folder")
    args = p.parse_args()

    text = read_input(args)
    if not text.strip():
        print("ERROR: input is empty")
        sys.exit(1)

    name = args.skill_name or slugify(Path(args.input or args.url).stem)
    build_skill(text, name, args.output_dir)


if __name__ == "__main__":
    main()
