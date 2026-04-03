Testing
=======

This folder contains pytest tests for the project.

Quick start
-----------
1. Activate your venv (Windows):

```powershell
venv\Scripts\Activate.ps1
```

2. Install dev/test deps and the package in editable mode:

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip install pytest
```

3. Run tests:

```powershell
pytest
```

Debugging tests
---------------
To step into your own modules while debugging tests in VS Code, set `justMyCode` to `false` in the debug configuration. Example `.vscode/launch.json` snippet:

```json
{
  "name": "Pytest: Single Test",
  "type": "python",
  "request": "launch",
  "module": "pytest",
  "args": ["-q", "tests/compression/test_FFMPEG__ensure_ffmpeg.py::test_ensure_ffmpeg__creates_files"],
  "env": {"PYTHONPATH": "${workspaceFolder}/src"},
  "justMyCode": false,
  "console": "integratedTerminal"
}
```

With `justMyCode: false` the debugger will enter library and module code (including your `src/` modules) instead of only your test files.

Tests structure and file name schema (cascade rules)
------------------------------------

Follow a cascading layout so tests stay small and easy to navigate as they grow:

1. Start simple — module-level file
   - `test_<module>.py` — the default layout. Use this for up to ~20 tests related to the module.

2. Split by function when large
   - If a `test_<module>.py` grows beyond ~20 tests, split it into per-function files:
     - `test_<module>__<function>.py` (double-underscore separates module and function).
     - Example: `test_file_manager__upload.py`.

3. Group by case when function files grow
   - If a `test_<module>__<function>.py` file exceeds ~20 tests, group tests by case:
     - `test_<module>__<function>__<case>.py` or `test_<module>__<function>_<case>.py` (pick one consistent form in the repo — this project uses the single underscore for case suffix).
     - Example: `test_file_manager__upload_error_cases.py` or `test_file_manager__upload_retry_case.py`.

Naming guidelines
 - Use lowercase names and underscores. Keep the double-underscore only to separate module and function parts.
 - Test function names inside files should start with `test_` and describe the behavior.

Why cascade
 - Keeps files small and focused, making them faster to edit and easier to review.
 - Allows progressive refactor as module complexity increases without an upfront heavy structure.

Fixtures and running
 - Place shared fixtures in `tests/conftest.py` (use `scope="session"` for resources to share, e.g., a single `TelegramManagerClient`).
 - Run tests serially to avoid single-client conflicts: `pytest -p no:xdist`.

This cascade keeps tests discoverable and scalable as the codebase and test coverage grow.