"""
:filename: sppas.ui.swapp.app_convert.convert_model.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The façade of the model of Convert.

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

from sppas.ui import _

from ..services.files import swappFilesManager

from .convert_formats import swappModelFormats
from .convert_conversion import swappModelConversion
from .convert_provision import swappModelProvision

# ---------------------------------------------------------------------------

MSG_NO_DESTINATION = _("The format {} cannot be written.")
MSG_NO_FILE = _("No file is to be converted.")

# ---------------------------------------------------------------------------


class swappConvertModel:
    """The façade of the model of Convert.

    It holds the knowledge of the formats, the conversion of the files, and
    the access to the provision of files, and it is the only interface the
    controller expects.

    """

    def __init__(self, manager: swappFilesManager):
        """Create the model of Convert.

        :param manager: (swappFilesManager) What the response holds of the provision of files
        :raises: sppasTypeError: The given manager is not a swappFilesManager

        """
        self.__formats = swappModelFormats()
        self.__conversion = swappModelConversion()
        self.__provision = swappModelProvision(manager)

    # -----------------------------------------------------------------------

    def writable_formats(self) -> list:
        """Return the formats which can be written.

        :return: (list of swappFormat)

        """
        return self.__formats.writable_formats()

    # -----------------------------------------------------------------------

    @staticmethod
    def properties() -> list:
        """Return the properties of a format, in the order they are shown.

        :return: (list of tuple) The identifier and the text of every property

        """
        return swappModelFormats.properties()

    # -----------------------------------------------------------------------

    def can_be_written(self, destination: str) -> bool:
        """Return True if the given extension is one of a writable format.

        :param destination: (str) Extension of a format, its dot included
        :return: (bool)

        """
        return self.__formats.can_be_written(destination)

    # -----------------------------------------------------------------------

    def properties_of(self, destination: str) -> dict:
        """Return what the destination format holds.

        :param destination: (str) Extension of a writable format, its dot included
        :return: (dict) True or False for every property

        """
        return self.__formats.properties_of(destination)

    # -----------------------------------------------------------------------

    def batch(self):
        """Return the batch: the workspace the provision of files hands.

        :return: (sppasWorkspace) Can hold no file at all

        """
        return self.__provision.batch()

    # -----------------------------------------------------------------------

    @staticmethod
    def files_of(batch) -> list:
        """Return the files of the batch which are to be converted.

        :param batch: (sppasWorkspace) Workspace holding the files to be converted
        :return: (list of str) Names of the files, with their path

        """
        return swappModelConversion.files_to_convert(batch)

    # -----------------------------------------------------------------------

    def convert(self, batch, destination: str, answers: dict, general_options: dict) -> list:
        """Convert the batch, and give back to the provision of files what was produced.

        The files of the batch are locked while they are converted, and
        released once each has its result. What was written is added to the
        batch, which is given back, and that the batch has been treated is said.

        :param batch: (sppasWorkspace) The workspace the provision of files handed
        :param destination: (str) Extension of the destination format, its dot included
        :param answers: (dict) The answer standing for each option, by option
        :param general_options: (dict) "override" and "heuristic", both booleans
        :raises: ValueError: The destination cannot be written, or the batch holds no file
        :return: (list of swappFileResult) One result per file, in the order of the batch

        """
        if self.__formats.can_be_written(destination) is False:
            raise ValueError(MSG_NO_DESTINATION.format(destination))

        _filenames = swappModelConversion.files_to_convert(batch)
        if len(_filenames) == 0:
            raise ValueError(MSG_NO_FILE)

        self.__provision.lock(_filenames)
        _results = self.__conversion.convert(batch, destination, answers, general_options)
        self.__provision.release(_filenames)
        self.__provision.produced(batch)
        self.__provision.finished()

        return _results
