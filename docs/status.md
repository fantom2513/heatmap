# Verification status — 2026-10-20

## Verified

- Dedicated virtual environment: Windows, Python 3.12.10.
- All 12 tests pass with `python -m pytest tests -q -p no:cacheprovider`.
- `python -m pip check`: no broken requirements.
- Python syntax compilation of `src/` and `tests/` succeeds.
- The local checkpoint loads into the copied architecture. A separate inference probe with a synthetic 320×240 image produces a finite normalized 240×320 map and correctly sized overlay.
- All 21 Python files matched the parent working tree immediately after copying; see `source-manifest.csv`. Application source has not been changed.

## Test corrections

The initial copied suite produced 10 passes and two failures. The missing-file test expected `FileNotFoundError`, but the existing service raises `ModelLoadError`. API mocks patched the dependency function's module name after FastAPI had already captured the callable, so they did not intercept requests. Tests now use dependency overrides and isolate the health cache. The initial tests are preserved in the first Git commit.

The original `fastapi[test]` dependency extra no longer installed the required test client. It was replaced with explicit `httpx`, with the owner's approval. Current Starlette emits a deprecation warning for httpx; this does not fail the suite.

## Remaining limits

- Docker configuration is supplied but the image has not been built or run.
- Dependency lists are inherited and not pinned. `verified-windows-environment.txt` records the installed package versions for the checked Windows environment; it is not a portable cross-platform lockfile.
- Benchmark runner scripts, full protocols and hardware metadata are absent. Archived metrics have not been rerun.
- A fresh clone has no checkpoint. The local checkpoint is ignored by Git, pending a public distribution decision.
- Existing model preprocessing and overlay channel ordering have not been changed or independently validated for color fidelity. Two auxiliary channels are zero-filled.
- The health endpoint's inherited error path constructs a string representation of a dictionary with an application/json media type. Valid JSON on that failure path has not been established or repaired in this extraction.
- GitHub CLI authentication for the existing account is invalid. No remote repository has been created or published.
