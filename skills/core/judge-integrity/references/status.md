# Judge status contract

| Status | Meaning | Scores |
|---|---|---|
| `ok` | Parsed a JSON object | present |
| `unparseable` | Call succeeded, output had no object | absent |
| `call_failed` | Provider raised | absent |
| `timeout` | Deadline expired | absent |

A caller must branch on status before reading a score. The four facts are
independent: a timeout can coexist with a late valid response, and a parse
failure says nothing about answer quality.
