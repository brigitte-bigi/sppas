"""
:filename: sppas.ui.swapp.services.options.options_file.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Ask the provision of files for the file an option takes.

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

from sppas.core.coreutils import sppasTypeError

from ...swapp_core.swappsg import swapp_serverstate
from ..files.files_chooser import swappFileChooser

from .options_request import swappFileRequest
from .options_set import swappOptionSet

# ---------------------------------------------------------------------------


class swappFileForOption:
    """Ask for the file an option takes, and take in what comes back.

    It is the only class of this service which speaks to the provision of
    files. It opens no file and reads none: what comes back is the value of
    an option, and nothing more.

    """

    def __init__(self, chooser: swappFileChooser | None = None):
        """Create the tie to the provision of files.

        :param chooser: (swappFileChooser) What asks the person, None for the one of that service

        """
        self.__chooser = chooser

    # -----------------------------------------------------------------------

    def ask_for(self, option) -> swappFileRequest:
        """Return the request of a file for the given option.

        Nothing is opened on any machine: the request says which option the
        file is for.

        :param option: (sppasOption) An option whose kind takes a file
        :raises: sppasTypeError: The kind of the given option takes no file
        :return: (swappFileRequest)

        """
        if option.get_type().startswith("file") is False:
            raise sppasTypeError(option.get_type(), "filename, filepath")

        return swappFileRequest(option.get_key())

    # -----------------------------------------------------------------------

    def file_of(self, request: swappFileRequest) -> str:
        """Return the file the person designates for a request.

        Where SPPAS runs on her machine, she designates it with the file
        chooser of the provision of files.

        :param request: (swappFileRequest) What was asked
        :raises: sppasTypeError: The given request is not a swappFileRequest
        :return: (str) Empty when no file was obtained

        """
        if isinstance(request, swappFileRequest) is False:
            raise sppasTypeError(request, "swappFileRequest")
        if swapp_serverstate.local is False:
            raise NotImplementedError

        if self.__chooser is None:
            self.__chooser = swappFileChooser()
        _files = self.__chooser.ask_for_files()
        if len(_files) == 0:
            return ""

        return _files[0]

    # -----------------------------------------------------------------------

    def take_in(self, options: swappOptionSet, key: str, filename: str) -> None:
        """Set the file which came back as the value of the option it was asked for.

        :param options: (swappOptionSet) The set the option belongs to
        :param key: (str) Key of the option the file was asked for
        :param filename: (str) What came back
        :raises: KeyError: No option of the set has this key

        """
        options.set_value(key, filename)
