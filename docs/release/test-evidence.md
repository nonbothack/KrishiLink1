# Packet 15 test evidence

## Commands

| Command | Result |
|---|---|
| `python -m pytest -q` | Run after Packet 15 changes; result recorded in `docs/work/15-result.md` |
| `python -m ruff check app` | Run after Packet 15 changes; result recorded in `docs/work/15-result.md` |
| `python -m mypy app` | Run after Packet 15 changes; result recorded in `docs/work/15-result.md` |
| `python -m compileall -q app alembic/versions` | Run after Packet 15 changes; result recorded in `docs/work/15-result.md` |
| `npm ci` / lint / test / build / e2e | Run where dependencies and browser are available; result recorded in `docs/work/15-result.md` |
| `python scripts/check_release_candidate.py` | Required release-evidence envelope check |

The full suite and frontend checks are reported with exact counts; no skipped
or unavailable command is represented as a pass.
