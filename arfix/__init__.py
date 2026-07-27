"""
arfix - Fix Arabic text rendering (reshaping + BiDi) in terminals that
don't support it natively (e.g. Termux).

Library usage:
    from arfix import fix
    print(fix("some text"))

The actual implementation is split across:
    arfix.core      - text detection, shaping, and BiDi logic
    arfix.cli       - `arfix` / `smartcat` command-line entry points
    arfix.uninstall - fully automatic removal logic for `arfix -u`

This top-level module re-exports the public API so both library users
and the pyproject.toml console_scripts entry points keep working.
"""

from arfix.core import fix, fix_line, has_arabic
from arfix.cli import main, run_wrapped
from arfix.uninstall import uninstall_self

__all__ = ["fix", "fix_line", "has_arabic", "main", "run_wrapped", "uninstall_self"]

__version__ = "1.0.0"
