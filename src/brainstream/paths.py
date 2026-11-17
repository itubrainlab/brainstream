"""Where brAInStream keeps its own files (not the projects')."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _system_dir(name: str, unix_name: str) -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / name
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / name
    return Path(os.environ.get("XDG_CONFIG_HOME",
                               Path.home() / ".config")) / unix_name


def config_dir() -> Path:
    """The per-user folder for brAInStream's settings, created on demand.

    ``BRAINSTREAM_HOME`` overrides it (the tests use this), as
    ``BRAINDUMP_HOME`` did. The settings brAInStream kept under its earlier
    names (brAIn stream in 0.5.0, brAIn dump before) are moved to the new
    folder the first time.
    """
    override = os.environ.get("BRAINSTREAM_HOME") or \
        os.environ.get("BRAINDUMP_HOME")
    if override:
        path = Path(override)
    else:
        path = _system_dir("brAInStream", "brainstream")
        for old in (_system_dir("brAIn stream", "brainstream"),
                    _system_dir("brAIn dump", "braindump")):
            if path.exists():
                break
            if old != path and old.is_dir():
                try:
                    old.rename(path)
                except OSError:
                    pass
    path.mkdir(parents=True, exist_ok=True)
    return path
