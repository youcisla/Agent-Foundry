# Quality Protocol - Details

Deep material that was moved out of the main skill body to keep it under the 150-line cap.

## Composes With

- `plan-then-act` — the action layer of this protocol
- `constraint-then-solve` — the reasoning layer of this protocol
- `verify-first` — adds triangle verification to the whole flow
- `prompt-discipline` — applies the same rules at code level

## Verification

After applying: confirm each of the 7 steps appears in the response in order, and the final output includes the constraint-by-constraint self-verify line.


## Anti-patterns

- Skipping verification when the change "feels small"
- Reasoning by analogy without a real example
- Acting on a claim you have not verified this session
- Choosing speed over accuracy when accuracy is what the task requires


## Verification Checklist

- [ ] The claim or action has been verified against a live source
- [ ] The output matches the request's scope (no scope creep)
- [ ] Slop markers are absent (filler, hedging, emoji headers)
