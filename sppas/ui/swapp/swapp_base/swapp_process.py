# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.swapp_base.swapp_process.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application long process of any app.

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

from __future__ import annotations
import json
import logging
import os
from threading import Thread

from sppas.core.config import paths
from sppas.core.config import sg
from sppas.core.coreutils import sppasLogFile

from .swapp_process_progress import swappProcessProgress

# ---------------------------------------------------------------------------

# The file of a process is named as every log file of SPPAS is.
PROCESS_PATTERN = "process"
PROCESS_EXTENSION = ".json"
PROCESS_PREFIX = "{:s}_{:s}_".format(sg.__name__, PROCESS_PATTERN)

# The event of the periodic call of a page which follows a process, the same
# for every app, and the field which names the process.
PROGRESS_EVENT = "swapp_progress"
PROCESS_FIELD = "swapp_process"

# ---------------------------------------------------------------------------


class swappProcess:
    """A long process of an app: it runs in a thread, and it is followed.

    A process lasts longer than the request which started it. Where it
    stands is written in a file of the folder of the logs of SPPAS, and
    nowhere else: whatever answers a request reads it there, by the name the
    page transmits. The file is written again, at once, each time the
    process says where it stands: a reader never finds it half written.

    """

    def __init__(self, name: str):
        """Create the process of the given name.

        :param name: (str) Name of the file of the process, without its path
        :raises: ValueError: The name is not the one of the file of a process

        """
        if name != os.path.basename(name) or name.startswith(PROCESS_PREFIX) is False \
                or name.endswith(PROCESS_EXTENSION) is False:
            raise ValueError("Not the name of the file of a process: {}".format(name))
        self.__name = name

    # -----------------------------------------------------------------------

    @staticmethod
    def start(target, args: tuple):
        """Start a process: the target is performed in a thread.

        The target is given the arguments, then the progress of the process,
        under the name "progress": it says where it stands by setting it.
        Once it has returned, the process has ended, whatever happened.

        :param target: (callable) What performs the process
        :param args: (tuple) The arguments of the target
        :return: (swappProcess) The process, which the page follows by its name

        """
        _name = os.path.basename(sppasLogFile(pattern=PROCESS_PATTERN, extension=PROCESS_EXTENSION).get_filename())
        _process = swappProcess(_name)
        _progress = swappProcessProgress(_process)
        _process.write(0, "", "", False)
        Thread(target=swappProcess.__perform, args=(target, args, _progress), daemon=True).start()

        return _process

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the file of the process, without its path (str)."""
        return self.__name

    # -----------------------------------------------------------------------

    def write(self, percent: float, header: str, text: str, finished: bool) -> None:
        """Write where the process stands, at once.

        :param percent: (float) Value between 0 and 100
        :param header: (str) What the process is doing
        :param text: (str) What is said of it
        :param finished: (bool) The process has ended

        """
        _filename = os.path.join(paths.logs, self.__name)
        _written = _filename + ".part"
        with open(_written, "w", encoding="utf-8") as fp:
            json.dump({"percent": percent, "header": header, "text": text, "finished": finished}, fp)
        os.replace(_written, _filename)

    # -----------------------------------------------------------------------

    def read(self) -> tuple:
        """Return where the process stands.

        :return: (tuple) The percent, the header, the text, and whether it has ended;
        (0, "", "", False) when nothing was written

        """
        _filename = os.path.join(paths.logs, self.__name)
        if os.path.exists(_filename) is False:
            return 0, "", "", False
        with open(_filename, "r", encoding="utf-8") as fp:
            _data = json.load(fp)

        return _data["percent"], _data["header"], _data["text"], _data["finished"]

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __perform(target, args: tuple, progress: swappProcessProgress) -> None:
        """Perform the target, then say the process has ended.

        What the target raises ends the process as well: whoever runs the
        machine reads why in the log, and the page is told it has ended.

        :param target: (callable) What performs the process
        :param args: (tuple) The arguments of the target
        :param progress: (swappProcessProgress) The progress of the process

        """
        try:
            target(*args, progress=progress)
        except Exception as e:
            logging.error("The process could not be performed: {}".format(e))
        progress.finish()

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    name = property(get_name, None)
