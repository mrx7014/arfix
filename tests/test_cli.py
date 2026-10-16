"""Tests for arfix.cli - argument handling and streaming wrapper."""

import sys

import pytest

from arfix import cli
from arfix.core import fix


def test_main_fixes_argument(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["arfix", "مرحبا"])
    cli.main()
    out = capsys.readouterr().out.rstrip("\n")
    assert out == fix("مرحبا")


def test_main_reads_stdin(monkeypatch, capsys):
    import io

    monkeypatch.setattr(sys, "argv", ["arfix"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("مرحبا"))
    cli.main()
    assert capsys.readouterr().out == fix("مرحبا")


def test_main_no_args_no_stdin_errors(monkeypatch, capsys):
    import io

    class _Tty(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "argv", ["arfix"])
    monkeypatch.setattr(sys, "stdin", _Tty(""))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1


def test_run_wrapped_streams_fixed_output(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["smartcat", "python3", "-c", "print('مرحبا')"])
    with pytest.raises(SystemExit) as exc:
        cli.run_wrapped()
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == fix("مرحبا").strip()
