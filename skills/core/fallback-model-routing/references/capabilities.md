# Capability fields

| Field | Effect |
|---|---|
| `context_window` | preflight rejects an over-context request |
| `supports_system_prompt` | false folds skill text into the user turn |
| `default_temperature` | used only when the caller omits temperature |
| `stop_tokens` | per mode: chat, fim, completion |
| `revision` | part of cache and score identity |
