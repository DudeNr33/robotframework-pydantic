# AGENTS.md

## Testing conventions

- Keep unit tests grouped by related behavior using `Test...` classes (for example: initialization, execution, metadata).
- Prefer clear, behavior-focused test names.
- Test behavior through public interfaces; avoid tests that directly call private/internal helpers (e.g. `_internal_method`).
- If a behavior currently appears only behind an internal helper, exercise that behavior through the closest public API.
- Keep Robot/acceptance tests separate from unit tests unless explicitly requested.

## Running checks

Run all checks via `uv`:

- Tests: `uv run pytest ...`
- Lint: `uv run ruff check`
- Formatting: `uv run ruff format`

Do not invoke global tools directly when `uv run` is available.
