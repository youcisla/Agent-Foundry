# Community Skills

Skills contributed by the community. Each skill must pass the three quality
gates before it can be merged to `main`.

## Adding a skill

1. Fork the repo
2. Create `skills/community/<your-skill>/SKILL.md` following the template
3. Open a PR — CI will run the gates automatically
4. When gates pass and a maintainer approves, it ships

## Quality gate requirements

- `scripts/foundry-eval.py` — skill body meets quality thresholds
- `scripts/validate.sh` — frontmatter is correct
- `scripts/nox.sh` — zero external references
