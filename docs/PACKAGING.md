# Packaging

This document describes two packaging workflows for `Telegram-UI`:

1. Single-file Windows executable using PyInstaller
2. Creating a pip-installable package (wheel) and publishing

Follow the minimal instructions below; adapt paths and names as needed.

---

## 1) Single-file executable (Windows) — PyInstaller

Prerequisites:
- Python 3.10+ in a virtualenv
- Install `pyinstaller` in the environment

```powershell
python -m pip install --upgrade pip
python -m pip install pyinstaller
```

Basic one-file GUI build (Windows):

```powershell
pyinstaller --noconfirm --clean --onefile --windowed \
  --name "Telegram-UI" \
  --add-data "ffmpeg;ffmpeg" \
  --add-data "images;images" \
  --add-data "icons;icons" \
  --icon docs/images/logo.ico \
  src/main.py
```

Notes:
- On Windows the `--add-data` path separator is `;` (on mac/linux use `:`).
- Include any runtime files or folders the app needs (e.g. `ffmpeg`, `icons`, `images`).
- Use `--windowed` to avoid a console window for GUI apps; remove it to see stdout/stderr.
- If PyInstaller misses imports at runtime, add them with `--hidden-import <module>` or a `.spec` file.

Output:
- The single executable will be in `dist/Telegram-UI/Telegram-UI.exe`.

Troubleshooting:
- If ffmpeg runtime expects a specific folder layout, use `--add-data` to preserve it.
- For large projects, create a `.spec` file to control packaging, data, and runtime hooks.

Cross-building:
- Build on the target OS when possible. For Windows you can use GitHub Actions to produce Windows executables.

---

## 2) Pip-installable package (wheel)

Two options:
A) Lightweight: keep repo layout and add a small `pyproject.toml` and a `telegram_ui` package folder (recommended).
B) If you prefer not to change code layout, follow the "restructure" steps below.

Recommended minimal restructuring (makes packaging clean):
1. Create a package folder `telegram_ui/` and move library modules there (e.g. `config.py`, `utils.py`, `file_manager/`, etc.). Keep `src/main.py` as the CLI/GUI entrypoint or move it into the package.
2. Add `__init__.py` to the package root and update imports to use `telegram_ui.*`.

Example `pyproject.toml` (PEP 621) to place at repo root after restructuring:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "telegram-ui"
version = "0.1.0"
description = "Telegram-UI: upload/manage files to Telegram as a cloud"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "telethon",
  # add other runtime deps from requirements.txt
]

[project.scripts]
telegram-ui = "telegram_ui.main:main"
```

Build and install locally:

```bash
python -m pip install --upgrade build
python -m build   # creates dist/*.whl and source archive
python -m pip install dist/telegram_ui-0.1.0-py3-none-any.whl
```

Publish to PyPI (optional):

```bash
python -m pip install --upgrade twine
python -m twine upload dist/*
```

Notes and caveats:
- Packaging as a wheel requires turning your code into a proper Python package (package dir + `__init__.py`).
- If the app bundles ffmpeg or other binary data, consider leaving those as external assets and document how to provide them.

---

## CI / GitHub Actions example (build artifacts)

You can build both the wheel and executables in CI. Example (Windows runner) steps:

- Checkout repo
- Setup Python
- Install dependencies
- Run `pyinstaller` to create the exe
- Run `python -m build` to create wheel
- Upload artifacts (exe + wheel) to release or actions artifacts

A complete workflow snippet is provided in the repository wiki or can be added as `.github/workflows/build.yml` on request.

---

## Quick tips

- Keep a `packaging/` or `docs/` note describing which files must be bundled.
- Test the executable on a clean Windows VM to ensure no missing DLLs.
- Use `--debug all` during development builds to see runtime errors from the frozen app.

If you'd like, I can:
- Add a ready-to-run `pyinstaller` PowerShell script for Windows.
- Add a `pyproject.toml` template and a small GitHub Actions workflow to build artifacts.
- Help refactor the repo into a proper `telegram_ui` package to enable wheel publishing.

Tell me which of those you want next and I'll implement it.
