# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.swapp_base.swapp_process_progress.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application progress of a long process of any app.

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
import logging

from sppas.core.coreutils import sppasBaseProgress

# ---------------------------------------------------------------------------


class swappProcessProgress(sppasBaseProgress):
    """The progress a long process of an app is given.

    It is a sppasBaseProgress: what performs the process -- the API, or the
    app itself -- sets it as it sets any other one. Where the process stands
    is written in the file of the process each time it is set, so that any
    request reads it there.

    """

    def __init__(self, process):
        """Create the progress of the given process.

        :param process: (swappProcess) The process whose file is written

        """
        super(swappProcessProgress, self).__init__()
        self.__process = process

    # -----------------------------------------------------------------------

    def set_header(self, header: str) -> None:
        """Override. Set the header, and write where the process stands.

        :param header: (str) What the process is doing

        """
        self._header = str(header)
        logging.info(self._header)
        self.__write(False)

    # -----------------------------------------------------------------------

    def update(self, percent: float | None = None, message: str | None = None) -> None:
        """Override. Set the percent and the text, and write where the process stands.

        :param percent: (float) Value between 0 and 100, None to leave it unchanged
        :param message: (str) The text, None to leave it unchanged

        """
        if percent is not None:
            self._percent = percent
        if message is not None:
            logging.info("  => " + message)
            self._text = str(message)
        self.__write(False)

    # -----------------------------------------------------------------------

    def finish(self) -> None:
        """Write that the process has ended: its percent is the hundred."""
        self._percent = 100
        self.__write(True)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __write(self, finished: bool) -> None:
        """Write where the process stands in its file.

        :param finished: (bool) The process has ended

        """
        self.__process.write(self._percent, self._header, self._text, finished)
