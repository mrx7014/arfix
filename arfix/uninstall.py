"""
arfix.uninstall - fully automatic removal of everything arfix set up.

Isolated from arfix.cli so the uninstall procedure can be read, tested,
or reused independently of argument parsing.
"""

import os
import shutil
import subprocess


def _remove_hook_from_bashrc() -> bool:
    """Remove the arfix auto-wrap block from ~/.bashrc, if present."""
    bashrc = os.path.expanduser("~/.bashrc")
    if not os.path.isfile(bashrc):
        return False

    with open(bashrc, encoding="utf-8") as fh:
        content = fh.read()

    start_marker = "# ==== arfix auto-wrap"
    end_marker = "# ==== end arfix auto-wrap ===="

    start = content.find(start_marker)
    if start == -1:
        return False
    end = content.find(end_marker, start)
    if end == -1:
        return False
    end += len(end_marker)

    # Also eat a single leading blank line we added before the block
    new_start = start
    if new_start > 1 and content[new_start - 1] == "\n" and content[new_start - 2] == "\n":
        new_start -= 1

    new_content = content[:new_start] + content[end:]
    with open(bashrc, "w", encoding="utf-8") as fh:
        fh.write(new_content)
    return True


def _find_pip() -> str:
    for candidate in ("pip3", "pip"):
        if shutil.which(candidate):
            return candidate
    return None


def _uninstall_pip_package() -> bool:
    """Uninstall the arfix pip package. Returns True on success."""
    pip_cmd = _find_pip()
    if not pip_cmd:
        print("arfix: pip not found, could not uninstall the Python package")
        return False

    result = subprocess.run(
        [pip_cmd, "uninstall", "-y", "--break-system-packages", "arfix"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # retry without --break-system-packages for pip versions that reject it
        result = subprocess.run(
            [pip_cmd, "uninstall", "-y", "arfix"],
            capture_output=True, text=True,
        )

    if result.returncode == 0:
        print("arfix: Python package uninstalled")
        return True

    print("arfix: could not uninstall the Python package automatically")
    print(result.stderr.strip())
    return False


def _is_installed_via_deb() -> bool:
    if not shutil.which("dpkg"):
        return False
    return subprocess.run(["dpkg", "-s", "arfix"], capture_output=True).returncode == 0


def _schedule_deb_removal():
    """
    Schedule `dpkg -r arfix` to run right after this process exits.

    We can't run it synchronously from inside arfix itself — dpkg would
    be trying to remove the very file currently executing — so it's
    detached to run a moment after this process ends.
    """
    dpkg_path = shutil.which("dpkg") or "dpkg"
    needs_sudo = hasattr(os, "geteuid") and os.geteuid() != 0
    cmd = (["sudo"] if needs_sudo else []) + [dpkg_path, "-r", "arfix"]
    subprocess.Popen(
        ["sh", "-c", "sleep 1; " + " ".join(cmd) + " >/dev/null 2>&1"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print("arfix: removing .deb package registration...")


def uninstall_self():
    """
    Removes everything the installer set up, fully automatically:
      1. The auto-wrap block from ~/.bashrc
      2. The arfix pip package itself
      3. The .deb registration, if arfix was installed that way

    No further action is required from the user.
    """
    print("arfix: uninstalling...")

    if _remove_hook_from_bashrc():
        print("arfix: removed auto-wrap block from ~/.bashrc")
    else:
        print("arfix: no auto-wrap block found in ~/.bashrc (nothing to remove)")

    installed_via_deb = _is_installed_via_deb()

    _uninstall_pip_package()

    if installed_via_deb:
        _schedule_deb_removal()

    print("")
    print("arfix: uninstall complete. Restart your terminal (or run 'source ~/.bashrc')")
    print("       to make sure cat/echo/grep/head/tail are back to normal.")
