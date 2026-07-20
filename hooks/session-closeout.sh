#!/usr/bin/env bash
# session-closeout.sh - Bash hook that prompts the session-closeout skill at session end
# Hook contract varies by harness; this is the portable bash implementation.
# Wire it into your harness's session-end hook system.
echo "==> session-closeout: ending session"
echo "==> Invoke: skill_view('session-closeout') and run the 6-surface reconciliation"
echo "==> Required before /reset, before stopping, or before handoff"
