"""
arfix.cli - command-line entry points: `arfix` and `smartcat`.

Argument parsing lives here, separate from the fixing logic in
arfix.core and the removal logic in arfix.uninstall.
"""

import sys
import subprocess

from arfix.core import fix, fix_line
from arfix.uninstall import uninstall_self

HELP_TEXT = """\
arfix - Fix Arabic text rendering (reshaping + BiDi) in terminals
        that don't support it natively (e.g. Termux)

WHY:
    Terminals like Termux print Arabic letters one by one, disconnected
    and in the wrong (left-to-right) order, e.g. "hello" in Arabic
    shows up as separate, unconnected letters instead of joined ones.
    arfix reshapes the letters into their connected forms and reorders
    them for correct right-to-left display, so any Arabic in your
    terminal output looks normal — no special font or system locale
    required.

USAGE:
    arfix <text>            Fix and print the given text directly
    echo "..." | arfix       Fix text piped from another command
    cat file.txt | arfix     Fix text piped from a file
    arfix -f <file>          Fix and print a file's contents
    arfix -h, --help         Show this help message
    arfix -u, --uninstall    Remove arfix completely (see below)

EXAMPLES:
    arfix "some arabic text here"
    echo "some arabic text here" | arfix
    cat notes.txt | arfix
    arfix -f notes.txt

RELATED COMMAND:
    smartcat <command> [args...]
        Runs any command and fixes its output automatically, line by
        line, as it's produced. Example:
            smartcat cat notes.txt
            smartcat ./my_script.sh

AUTO-WRAP (no command needed):
    If the shell hook was enabled during install, common commands
    (cat, echo, grep, head, tail) already auto-fix Arabic output in
    every new terminal session — you don't need to call arfix or
    smartcat at all for those. Non-Arabic text always passes through
    unchanged.

UNINSTALLING:
    arfix -u removes everything automatically in one step: the
    shell-hook block from ~/.bashrc, the arfix Python package, and
    the .deb package registration (if arfix was installed that way).
    No further action is needed from you.
"""

USAGE_LINE = "usage: arfix <text>  |  echo text | arfix  |  arfix -f <file>  |  arfix -h"


def _fix_file(path: str):
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    sys.stdout.write(fix(content))


def _fix_stdin():
    content = sys.stdin.read()
    sys.stdout.write(fix(content))


def main():
    """Entry point for the `arfix` command."""
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help"):
        print(HELP_TEXT)
        return

    if args and args[0] in ("-u", "--uninstall"):
        uninstall_self()
        return

    if args and args[0] in ("-f", "--file"):
        if len(args) < 2:
            print("usage: arfix -f <file>", file=sys.stderr)
            sys.exit(1)
        _fix_file(args[1])
        return

    if args:
        print(fix(" ".join(args)))
        return

    # No arguments: read from stdin if it's piped, e.g.
    # `echo "..." | arfix` or `cat file | arfix`
    if not sys.stdin.isatty():
        _fix_stdin()
        return

    print(USAGE_LINE, file=sys.stderr)
    sys.exit(1)


def run_wrapped():
    """
    Entry point for the `smartcat` command: runs an arbitrary command,
    passing its stdout+stderr through the Arabic fixer line by line,
    live (streaming), so output shows up fixed as it's produced.

    Usage:
        smartcat cat somefile.txt
        smartcat ./some_script.sh
        smartcat echo "some text"
    """
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: smartcat <command> [args...]")
        print("Runs <command> and fixes Arabic text in its output live, line by line.")
        print("Example: smartcat cat notes.txt")
        sys.exit(0 if len(sys.argv) >= 2 else 1)

    cmd = sys.argv[1:]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in proc.stdout:
        sys.stdout.write(fix_line(line.rstrip("\n")) + "\n")
        sys.stdout.flush()
    proc.wait()
    sys.exit(proc.returncode)
