# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.config.logsetup.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Logging setup of SPPAS.

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

import logging

# ---------------------------------------------------------------------------


class sppasLogSetup(object):
    """A convenient class to initialize the python logging system.

    """

    def __init__(self, log_level=0):
        """Create a sppasLogSetup instance.

        By default, the NullHandler is assigned: no output.
        The numeric values of logging levels are the followings:

            - CRITICAL 	50
            - ERROR 	40
            - WARNING 	30
            - INFO 	    20
            - DEBUG 	10
            - NOTSET 	 0

        Logging messages which are less severe than the given level value
        will be ignored. When NOTSET is assigned, all messages are printed.

        :param log_level: Set the threshold logger value

        """
        self._log_level = int(log_level)

        # Fix the format of the messages
        format_msg = "%(asctime)s [%(levelname)s] %(message)s"
        # Create a log formatter
        self._formatter = logging.Formatter(format_msg)

        # The handlers added beside the main one -- a stream asked for with
        # a file -- are held, so that they are removed with it and nothing
        # else is.
        self.__companions = list()

        # Remove all existing handlers in the logging
        for h in reversed(list(logging.getLogger().handlers)):
            logging.getLogger().removeHandler(h)

        # Add our own handler in the logging
        self._handler = logging.NullHandler()
        logging.getLogger().addHandler(self._handler)
        logging.getLogger().setLevel(self._log_level)

    # -----------------------------------------------------------------------

    def set_log_level(self, log_level):
        """Fix the log level.

        :param log_level: Set the threshold for the logger

        """
        if log_level == self._log_level:
            return

        self._log_level = int(log_level)
        if self._handler is not None:
            self._handler.setLevel(self._log_level)
        logging.getLogger().setLevel(self._log_level)

        logging.info("Logging set up level={:d}"
                     "".format(self._log_level))

    # -----------------------------------------------------------------------

    def stream_handler(self):
        """Start to redirect to logging StreamHandler.

        """
        self.__stop_handler()
        self._handler = logging.StreamHandler()  # sys.stderr
        self._handler.setFormatter(self._formatter)
        self._handler.setLevel(self._log_level)
        logging.getLogger().addHandler(self._handler)

        logging.debug("Logging redirected to StreamHandler (level={:d})."
                      "".format(self._log_level))

    # -----------------------------------------------------------------------

    def null_handler(self):
        """Start to redirect to logging NullHandler.

        """
        self.__stop_handler()
        self._handler = logging.NullHandler()
        logging.getLogger().addHandler(self._handler)

    # -----------------------------------------------------------------------

    def file_handler(self, filename, with_stream=False):
        """Start to redirect to logging FileHandler.

        :param filename: a FileHandler has to be created using this filename.
        :param with_stream: (bool) A StreamHandler is added too.

        """
        self.__stop_handler()
        self._handler = logging.FileHandler(filename, "a+")
        self._handler.setFormatter(self._formatter)
        self._handler.setLevel(self._log_level)
        logging.getLogger().addHandler(self._handler)
        if with_stream is True:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self._formatter)
            console_handler.setLevel(self._log_level)
            logging.getLogger().addHandler(console_handler)
            self.__companions.append(console_handler)

        logging.info("Logging redirected to FileHandler (level={:d}) "
                     "in file {:s}."
                     "".format(self._log_level, filename))

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __stop_handler(self):
        """Stops the handlers this instance added, and only them.

        A handler somebody else added to the root logger stays: it was not
        put there by this class, and removing it silently cuts whoever was
        collecting the records -- the Journal of the web interface collects
        them that way, and a page changing the destination of the logs would
        empty it without saying so.

        """
        if self._handler is not None:
            # Show a bye message on the console!
            logging.info("Stops current logging handler.")
            # Remove the current handler, and the stream which came with it
            logging.getLogger().removeHandler(self._handler)
            for h in reversed(self.__companions):
                logging.getLogger().removeHandler(h)

        self.__companions = list()
        self._handler = None
