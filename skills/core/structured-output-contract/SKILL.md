---
name: structured-output-contract
description: 'When output feeds a program, define the schema before calling the model.
  Parse strictly, validate required fields and types, allow one repair attempt,
  then fail closed instead of guessing. Use when JSON, tool arguments, or any
  machine-read value is required.'
version: 0.1.0
license: MIT
author: Agent Foundry Contributors
---

# Structured Output Contract

A program will read this output. Treat the schema as the contract, not a hint.

## Auto-trigger

- The caller passes a JSON Schema or names required fields.
- Output is parsed by code, stored in a database, or passed to another tool.
- A workflow branches on a field the model must emit.
- The model answers with prose around what should be a single value.

## When to Use

- Tool arguments, function-call payloads, extraction tasks.
- Classification where the label set is closed.
- Reports consumed by a dashboard or evaluator.
- Any retry loop where malformed output would waste a paid call.

## Procedure

### 1 — Define the schema first

State the exact shape before prompting:

```json
{
  "type": "object",
  "required": ["decision", "reasons"],
  "properties": {
    "decision": {"type": "string", "enum": ["allow", "deny"]},
    "reasons": {"type": "array", "items": {"type": "string"}}
  }
}
```

Rules:
- `required` lists every field the consumer reads.
- Closed choices use `enum`, not prose instructions.
- No optional fields unless the consumer handles absence.
- Numbers state integer versus number. Booleans never arrive as strings.

### 2 — Constrain the prompt to one value

Ask for exactly one JSON value. Forbid fences, preamble, and trailing notes.
Keep the schema in the final user turn where it is closest to generation.

### 3 — Parse tolerantly, validate strictly

Extraction may unwrap a fenced block or surrounding prose. Validation does not
soften: missing required field, wrong type, or out-of-enum value is a failure.

### 4 — One repair, then stop

On failure, send the invalid reply back with the exact validation errors and ask
for corrected JSON. One repair. A second failure returns an error; it does not
silently coerce, drop fields, or substitute a default.

### 5 — Surface validity separately

Return the parsed value and a validity flag. A caller must be able to tell
"valid structured output" from "best-effort text" without re-parsing.

## Anti-patterns

- Accepting `"true"` where a boolean is required.
- Filling missing fields with guesses.
- Looping repairs until the budget disappears.
- Letting markdown fences reach the parser as data.
- Declaring success when validation only warned.

## Verification Checklist

- [ ] Every field the consumer reads is in `required`
- [ ] Invalid output produces an error, not a default value
- [ ] One repair attempt is enforced
- [ ] Validity is reported to the caller
- [ ] Tests cover missing field, wrong type, and fenced JSON
