"""
:filename: sppas.bin.tktools.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Install tkinter, the dialogs to choose files, for macOS and Windows.

.. _This file is part of SPPAS: https://sppas.org/
..
    -------------------------------------------------------------------------

     ######   ########   ########      ###      ######
    ##    ##  ##     ##  ##     ##    ## ##    ##    ##     the automatic
    ##        ##     ##  ##     ##   ##   ##   ##            annotation
     ######   ########   ########   ##     ##   ######        and
          ##  ##         ##         #########        ##        analysis
    ##    ##  ##         ##         ##     ##  ##    ##         of speech
     ######   ##         ##         ##     ##   ######

    Copyright (C) 2011-2026  Brigitte Bigi, CNRS
    Laboratoire Parole et Langage, Aix-en-Provence, France

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    This banner notice must not be removed.

    -------------------------------------------------------------------------

"""

import os
import shutil
import subprocess
import sys

if sys.version_info < (3, 9):
    print("The version of Python is too old: "
          "This program requires at least version 3.9.")
    sys.exit(1)
if sys.platform not in ("darwin", "win32"):
    print(f"This program is dedicated to 'darwin' and 'win32' platforms "
          f"but your is {sys.platform}. On this one, tkinter is a package of "
          f"the system: install 'python3-tk' or 'python3-tkinter'.")
    sys.exit(1)

# ---------------------------------------------------------------------------


BREW_CANDIDATES = (
    "/opt/homebrew/bin/brew",
    "/usr/local/bin/brew",
)

TK_FORMULA = "python-tk@{}.{}".format(sys.version_info.major,
                                     sys.version_info.minor)

MSG_WINDOWS = (
    "tkinter is missing. Run the installer of Python of python.org again, "
    "choose 'Repair', and keep the option 'tcl/tk and IDLE' checked."
)

MSG_PYTHON_ORG = (
    "tkinter is missing. Install Python from python.org: its installer "
    "brings tkinter. To keep the Python of Homebrew instead, install its "
    "formula {}.".format(TK_FORMULA)
)

# ---------------------------------------------------------------------------


def _run(command, env=None):
    """Run a shell command and stop on error."""
    print("Run: {}".format(command))
    result = subprocess.run(
        command,
        shell=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr:
            sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return result

# ---------------------------------------------------------------------------

def _has_tkinter():
    """Return True if the Python in use can import tkinter."""
    result = subprocess.run(
        [sys.executable, "-c", "import tkinter"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

# ---------------------------------------------------------------------------

def _get_brew_path():
    """Return the absolute path of brew, or None."""
    for candidate in BREW_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return shutil.which("brew")

# ---------------------------------------------------------------------------

def _make_env(brew_path):
    """Return an environment with brew in PATH."""
    env = os.environ.copy()
    brew_dir = os.path.dirname(brew_path)
    current_path = env.get("PATH", "")
    if brew_dir not in current_path.split(os.pathsep):
        env["PATH"] = brew_dir + os.pathsep + current_path if current_path else brew_dir
    return env

# ---------------------------------------------------------------------------

def _is_brew_python(brew_path):
    """Return True if the Python in use is the one Homebrew installed."""
    brew_prefix = os.path.dirname(os.path.dirname(brew_path))
    return sys.base_prefix.startswith(brew_prefix)

# ---------------------------------------------------------------------------

def _is_formula_installed(brew_path, env, formula):
    """Return True if a Homebrew formula is already installed."""
    result = subprocess.run(
        [brew_path, "list", "--formula", formula],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if _has_tkinter() is True:
    print("tkinter is already installed. Nothing to do.")
    sys.exit(0)

# Windows: tkinter comes with the installer of Python, and with it only.
# Nothing installs it afterwards, so the way to get it is said and nothing
# is attempted.
if sys.platform == "win32":
    print(MSG_WINDOWS)
    sys.stderr.write(MSG_WINDOWS)
    sys.exit(1)

# macOS: the installer of python.org brings its own Tcl/Tk, and the Python
# of Homebrew does not. Only the second one has something to install, and
# its formula is the one of the version in use: python-tk@3.13 for 3.13.
brew_path = _get_brew_path()
if brew_path is None:
    print(MSG_PYTHON_ORG)
    sys.stderr.write(MSG_PYTHON_ORG)
    sys.exit(1)

if _is_brew_python(brew_path) is False:
    print(MSG_PYTHON_ORG)
    sys.stderr.write(MSG_PYTHON_ORG)
    sys.exit(1)

env = _make_env(brew_path)

if _is_formula_installed(brew_path, env, TK_FORMULA) is True:
    print("{} is already installed.".format(TK_FORMULA))
else:
    _run('"{}" install {}'.format(brew_path, TK_FORMULA), env=env)

if _has_tkinter() is False:
    sys.stderr.write("{} installation failed.".format(TK_FORMULA))
    sys.exit(1)

sys.exit(0)
