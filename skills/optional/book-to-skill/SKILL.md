---
name: book-to-skill
description: Convert book chapters, PDF excerpts, or long articles into a runnable skill. Use when the user says 'turn this book into a skill', 'extract from this PDF', 'make a skill from chapter X', or wants to convert any long-form knowledge into agent instructions.
version: 1.0.0
license: MIT
author: Agent Foundry Contributors
category: optional
tags: [agent-foundry, skill-authoring, book, pdf, extraction, knowledge-base, rag]
platforms: [linux, macos, windows]
---

# Book to Skill

Turn any book, PDF, or long-form document into a working agent skill.

## Usage

```bash
# From a PDF
python scripts/book_to_skill.py extract --input=book.pdf --output-dir=./skills/my-book

# From text/markdown chapter
python scripts/book_to_skill.py extract --input=chapter.md --output-dir=./skills/my-book

# From URL
python scripts/book_to_skill.py extract --url=https://example.com/book.pdf --output-dir=./skills/my-book
```

## What it does

1. Reads the input (PDF, MD, TXT, or URL)
2. Splits into chapters/sections
3. For each section, generates:
   - A short title
   - 3-7 actionable instructions
   - Key concepts / glossary
   - Example transformations
4. Writes SKILL.md + references/ folder
5. Validates against effective-agent-skills standards

## Companion skills

- effective-agent-skills (installed): for skill quality standards
- deep-research (installed): for sourcing the book content
- push-skill-to-github (installed): to publish the resulting skill
- agent-memory-vault (installed): to remember what was learned
