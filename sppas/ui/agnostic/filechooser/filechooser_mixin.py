"""
:filename: sppas.ui.agnostic.filechooser.filechooser_mixin.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Mixin class to access file/folder selection dialogs safely from subprocesses.

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

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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

from __future__ import annotations
import subprocess
import json
import os
import sys

class FileChooserMixin:
    """Mixin to provide file/folder selection dialogs via a subprocess.

    This class provides functions to call a standalone Python script using Tkinter
    to safely launch native file dialogs from non-main threads, e.g., from a local HTTP server.

    Requirements:
    - Python with Tkinter installed (default in most distributions)
    - filechooser_worker.py must be located in the same directory as this module

    :example:
    >>>class MyResponse(ExtendResponseRecipe, FileChooserMixin):
    >>>    def _process_events(self, events, **kwargs):
    >>>        path = self.ask_file("openfile")

    """

    # Define the path to the standalone worker script that launches the native
    # dialog. This path is resolved relative to this mixin's location.
    FILECHOOSER_WORKER = os.path.join(os.path.dirname(__file__), "filechooser_worker.py")

    def ask_file(self,
                 mode: str = "openfile",
                 title: str | None = None,
                 multiple: bool = False,
                 filetypes: list | None = None,
                 defaultextension: str | None = None) -> list | str:
        """Launch the filechooser_worker in a subprocess.

        It allows to display a native file or folder dialog.

        :param mode: (str) 'openfile', 'savefile', or 'directory'
        :param title: (str|None) Optional title for the dialog
        :param multiple: (bool) Only valid with 'openfile' (select multiple files)
        :param filetypes: (list) List of tuples (label, pattern), e.g., [('Audio', '*.wav')]
        :param defaultextension: (str|None) Default file extension for 'savefile'
        :return: (str|list) Selected path(s) as str or list or error

        """
        args = [sys.executable, self.FILECHOOSER_WORKER, mode]

        if title is not None:
            args += ["--title", title]

        if multiple is True:
            args += ["--multiple"]

        if defaultextension is not None:
            args += ["--defaultext", defaultextension]

        if filetypes is not None:
            # filetypes as a JSON string
            args += ["--filetypes", json.dumps(filetypes)]

        try:
            result = subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)
            output = json.loads(result.strip())
            return output.get("paths", output.get("path", ""))
        except subprocess.CalledProcessError as e:
            return f"Error: {e.output}"
        except json.JSONDecodeError as e:
            return f"Error: JSON decode failed: {e}"
        except Exception as e:
            return f"Error: {e}"
