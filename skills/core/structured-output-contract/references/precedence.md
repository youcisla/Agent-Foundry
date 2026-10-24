# Constraint precedence

1. Tool-call block
2. JSON Schema
3. Regex or grammar

One constraint per request. Record whether the backend enforced it or only the
prompt did. Parse balanced braces; keep raw output on failure.
