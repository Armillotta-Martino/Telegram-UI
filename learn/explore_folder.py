"""
Small utility to recursively explore a folder while skipping PermissionError.

Usage:
    python learn/explore_folder.py [PATH]

If PATH is omitted, current working directory is used.
"""
from __future__ import annotations

import os
import sys
from typing import Generator, Dict, Optional, Set


def iter_dir(path: str, seen: Optional[Set[str]] = None) -> Generator[Dict, None, None]:
    """Recursively iterate a directory tree yielding simple dicts for each entry.

    Skips entries that raise PermissionError or other OSErrors and avoids
    visiting the same real path twice (symlink loops).
    """
    if seen is None:
        seen = set()

    try:
        real = os.path.realpath(path)
    except Exception:
        real = path

    if real in seen:
        return
    seen.add(real)

    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                except PermissionError:
                    yield {"path": entry.path, "type": "unknown", "error": "PermissionError"}
                    continue
                except OSError as e:
                    yield {"path": entry.path, "type": "unknown", "error": f"OSError: {e}"}
                    continue

                if is_dir:
                    yield {"path": entry.path, "type": "dir"}
                    # Recurse into directory (avoid following symlinks)
                    try:
                        for child in iter_dir(entry.path, seen):
                            yield child
                    except PermissionError:
                        yield {"path": entry.path, "type": "dir", "error": "PermissionError"}
                    except OSError as e:
                        yield {"path": entry.path, "type": "dir", "error": f"OSError: {e}"}
                else:
                    # Try to get size, but tolerate errors
                    try:
                        stat = entry.stat(follow_symlinks=False)
                        size = stat.st_size
                    except Exception:
                        size = None
                    yield {"path": entry.path, "type": "file", "size": size}
    except PermissionError:
        yield {"path": path, "type": "dir", "error": "PermissionError"}
    except OSError as e:
        yield {"path": path, "type": "dir", "error": f"OSError: {e}"}


def print_tree(root: str, indent: str = "    ") -> None:
    """Print a simple tree view produced by iter_dir.

    Files and directories that couldn't be accessed show an "[error]" tag.
    """
    if not os.path.exists(root):
        print(f"Path does not exist: {root}")
        return

    # Print root
    print(root)

    for item in iter_dir(root):
        rel = os.path.relpath(item["path"], root)
        # Limit indentation levels
        parts = rel.split(os.sep)
        depth = len(parts) - 1
        pad = indent * depth

        if item.get("type") == "dir":
            if "error" in item:
                print(f"{pad}└─ [dir] {parts[-1]} [error: {item['error']}]")
            else:
                print(f"{pad}└─ [dir] {parts[-1]}")
        elif item.get("type") == "file":
            size = item.get("size")
            size_str = f" ({size} bytes)" if size is not None else ""
            print(f"{pad}└─ [file] {parts[-1]}{size_str}")
        else:
            print(f"{pad}└─ [unknown] {parts[-1]} [error: {item.get('error')}]")


def main(argv: Optional[list] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = argv[0] if argv else os.getcwd()
    print_tree(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
