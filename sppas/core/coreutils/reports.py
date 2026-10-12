# -*- coding: UTF-8 -*-
"""
:filename: sppas.core.config.reports.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Log system of SPPAS.

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

import sys
import os
import platform
from datetime import date
from datetime import datetime

from sppas.core.config.settings import paths
from sppas.core.config.settings import sg

# ---------------------------------------------------------------------------


class sppasLogFile(object):
    """Manager for logs of SPPAS runs.

    """

    def __init__(self, pattern="log", extension=".txt"):
        """Create a sppasLogFile instance.

        Create the log directory if it does not already exist, then fix the
        log filename with increment=0.

        :param extension: (str) Extension of the log filename, with its dot

        """
        self.__extension = extension
        log_dir = paths.logs
        if os.path.exists(log_dir) is False:
            os.mkdir(log_dir)

        self.__filename = "{:s}_{:s}_".format(sg.__name__, pattern)
        self.__filename += str(date.today()) + "_"
        self.__filename += str(os.getpid()) + "_"

        self.__current = 1
        while os.path.exists(self.get_filename()) is True:
            self.__current += 1

    # -----------------------------------------------------------------------

    def get_filename(self):
        """Return the current log filename."""
        fn = os.path.join(paths.logs, self.__filename)
        fn += "{0:04d}".format(self.__current)
        return fn + self.__extension

    # -----------------------------------------------------------------------

    def increment(self):
        """Increment the current log filename."""
        self.__current += 1

    # -----------------------------------------------------------------------

    @staticmethod
    def get_header():
        """Return a string with an header for logs."""
        header = "-"*78
        header += "\n\n"
        header += " {:s} {:s}".format(sg.__name__, sg.__version__)
        header += "\n"
        header += " {:s}".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        header += "\n"
        header += " {:s}".format(platform.platform())
        header += "\n"
        header += " {:s}".format(sys.executable)
        header += "\n"
        header += " python {:s}".format(platform.python_version())
        header += "\n\n"
        header += "-"*78
        header += "\n\n"
        return header
