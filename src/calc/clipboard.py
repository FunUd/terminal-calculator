"""Clipboard utility for copying calculation results on Windows and terminals."""

from __future__ import annotations
import subprocess
import sys
from typing import Any, Optional


def copy_to_clipboard(text: str, app: Optional[Any] = None) -> bool:
    """Copy text to system clipboard using Windows clip.exe or Textual OSC 52."""
    copied = False

    # Try Textual's built-in clipboard support first
    if app is not None and hasattr(app, "copy_to_clipboard"):
        try:
            app.copy_to_clipboard(text)
            copied = True
        except Exception:
            pass

    # On Windows, use clip.exe for native OS clipboard integration
    if sys.platform == "win32":
        try:
            # clip.exe expects text encoded in utf-16le
            subprocess.run(
                ["clip.exe"],
                input=text.encode("utf-16le"),
                check=True,
                capture_output=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            copied = True
        except Exception:
            pass

    return copied
