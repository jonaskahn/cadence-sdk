"""Runtime dependency installers for Cadence plugins.

Installs packages declared in plugin metadata into the current environment.
Prefers Poetry (via ``poetry run pip install``) when available; otherwise
falls back to ``python -m pip install``.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple


def _which(exe: str) -> bool:
    """Return True if an executable is on PATH."""
    from shutil import which

    return which(exe) is not None


def _in_poetry_project(cwd: Path | None = None) -> bool:
    """Return True if a pyproject.toml exists in cwd or parents."""
    start = cwd or Path.cwd()
    for parent in [start] + list(start.parents):
        if (parent / "pyproject.toml").exists():
            return True
    return False


def _run(
    command: List[str],
    on_output: Optional[Callable[[str], None]] = None,
) -> Tuple[int, str, str]:
    """Run a command, returning (rc, stdout, stderr).

    If on_output is provided, stream stdout/stderr lines to the callback.
    """
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=os.environ.copy(),
    )

    collected_out: List[str] = []
    if proc.stdout is not None:
        for line in proc.stdout:
            collected_out.append(line)
            if on_output:
                try:
                    on_output(line.rstrip("\n"))
                except Exception:
                    pass
    rc = proc.wait()
    out = "".join(collected_out)
    return rc, out, ""


def install_packages(
    packages: Iterable[str],
    prefer_poetry: bool = True,
    verbose: bool = True,
    on_output: Optional[Callable[[str], None]] = None,
) -> Tuple[bool, str]:
    """Install packages into the active environment.

    - When Poetry is available and a project is detected, runs:
      ``poetry run python -m pip install <packages>``
    - Otherwise, runs: ``python -m pip install <packages>``

    Returns:
        (ok, log): whether install succeeded and combined output log.
    """
    pkgs = [p for p in packages if p and str(p).strip()]
    if not pkgs:
        return True, "No packages to install"

    use_poetry = prefer_poetry and _which("poetry") and _in_poetry_project()

    verbosity_flags = ["-vv"] if verbose else []

    if use_poetry:
        cmd = (
            [
                "poetry",
                "run",
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-input",
                "--disable-pip-version-check",
            ]
            + verbosity_flags
            + pkgs
        )
    else:
        cmd = (
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-input",
                "--disable-pip-version-check",
            ]
            + verbosity_flags
            + pkgs
        )

    rc, out, err = _run(cmd, on_output=on_output)
    log = f"$ {' '.join(shlex.quote(c) for c in cmd)}\n{out}\n{err}"
    return rc == 0, log
