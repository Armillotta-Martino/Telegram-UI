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

Structure recommendation
-----------------------
- Keep tests grouped by module/package. Mirror the `src/` package layout where helpful, e.g.:
  - `tests/test_utils.py` (small modules)
  - `tests/file_manager/test_upload.py` (package-level tests)
- Do NOT copy the entire `src/` tree into `tests/`. Instead, mirror *structure* (folders and filenames) to make it easy to find tests for a given module while keeping one source of truth for implementation.

Best practices
--------------
- Use `conftest.py` for shared fixtures and test helpers.
- Mock external services (Telethon, network, filesystem) in unit tests.
- Write small, focused tests for pure functions and integration tests for end-to-end flows.
- Add CI (GitHub Actions) to run `pytest` on push/PR.

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
