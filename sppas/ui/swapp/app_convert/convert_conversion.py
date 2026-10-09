"""
:filename: sppas.ui.swapp.app_convert.convert_conversion.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The conversion of the files of a batch.

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

import logging
import os

from sppas.core.coreutils import sppasTypeError
from sppas.src.anndata import sppasTrsRW
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States
from sppas.ui import _

# ---------------------------------------------------------------------------

STATUS_WRITTEN = "written"
STATUS_SKIPPED = "skipped"
STATUS_REFUSED = "refused"

MSG_EXISTS = _("The output file already exists.")

# ---------------------------------------------------------------------------


class swappFileResult:
    """What happened to one file of the batch.

    """

    def __init__(self, filename: str, status: str, cause: str = "", produced: list | None = None):
        """Create the result of one file.

        :param filename: (str) Name of the file of the batch, with its path
        :param status: (str) What happened to it: written, skipped or refused
        :param cause: (str) Why it was skipped or refused, empty when it was written
        :param produced: (list of str) Names of the files written from it, with their path

        """
        if produced is None:
            produced = list()

        self.__file = filename
        self.__status = status
        self.__cause = cause
        self.__produced = produced

    # -----------------------------------------------------------------------

    def get_file(self) -> str:
        """Return the name of the file of the batch, with its path (str)."""
        return self.__file

    # -----------------------------------------------------------------------

    def get_status(self) -> str:
        """Return what happened to the file: written, skipped or refused (str)."""
        return self.__status

    # -----------------------------------------------------------------------

    def get_cause(self) -> str:
        """Return why the file was skipped or refused (str)."""
        return self.__cause

    # -----------------------------------------------------------------------

    def get_produced(self) -> list:
        """Return the names of the files written from it, with their path (list)."""
        return list(self.__produced)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    file = property(get_file, None)
    status = property(get_status, None)
    cause = property(get_cause, None)
    produced = property(get_produced, None)

# ---------------------------------------------------------------------------


class swappModelConversion:
    """Read every file of a batch, write it in the destination format.

    It is the only class of this application which reads or writes a file of
    the user. A file is written beside the one it was made from, under the
    same name and the extension of the destination, and it is added to the
    workspace the batch is. The failure of one file never interrupts the
    others: it is a result.

    """

    @staticmethod
    def files_to_convert(batch: sppasWorkspace) -> list:
        """Return the files of the batch, in the order the workspace holds them.

        :param batch: (sppasWorkspace) Workspace holding the files to be converted
        :raises: sppasTypeError: The given batch is not a sppasWorkspace
        :return: (list of str) Names of the checked files, with their path

        """
        if isinstance(batch, sppasWorkspace) is False:
            raise sppasTypeError(batch, "sppasWorkspace")

        _files = list()
        for _path in batch.get_paths():
            for _root in _path:
                for _file in _root:
                    if _file.get_state() == States().CHECKED:
                        _files.append(_file.get_id())

        return _files

    # -----------------------------------------------------------------------

    def convert(self, batch: sppasWorkspace, destination: str, answers: dict, general_options: dict) -> list:
        """Convert every file of the batch into the destination format.

        What was written is added to the workspace the batch is. No file of
        the batch is removed or rewritten.

        :param batch: (sppasWorkspace) Workspace holding the files to be converted
        :param destination: (str) Extension of the destination format, its dot included
        :param answers: (dict) The answer standing for each option, by option
        :param general_options: (dict) "override" and "heuristic", both booleans
        :raises: sppasTypeError: The given batch is not a sppasWorkspace
        :return: (list of swappFileResult) One result per file, in the order of the batch

        """
        _results = list()
        for _filename in swappModelConversion.files_to_convert(batch):
            _results.append(self.convert_one(_filename, destination, answers, general_options))

        for _result in _results:
            for _produced in _result.produced:
                batch.add_file(_produced)

        return _results

    # -----------------------------------------------------------------------

    def convert_one(self, filename: str, destination: str, answers: dict, general_options: dict) -> swappFileResult:
        """Convert one file into the destination format.

        The file is read, then written beside itself with the extension of the
        destination. It is skipped when that file exists already and override
        is not allowed; it is refused, with the cause, when it cannot be read
        or written.

        :param filename: (str) Name of the file, with its path
        :param destination: (str) Extension of the destination format, its dot included
        :param answers: (dict) The answer standing for each option, by option
        :param general_options: (dict) "override" and "heuristic", both booleans
        :return: (swappFileResult)

        """
        _override = general_options.get("override", False)
        _heuristic = general_options.get("heuristic", False)
        _output = os.path.splitext(filename)[0] + destination

        if _override is False and os.path.exists(_output) is True:
            return swappFileResult(filename, STATUS_SKIPPED, MSG_EXISTS)

        try:
            _transcription = sppasTrsRW(filename).read(heuristic=_heuristic)
        except Exception as e:
            logging.error("The file {} could not be read: {}".format(filename, e))
            return swappFileResult(filename, STATUS_REFUSED, str(e))

        try:
            sppasTrsRW(_output).write(_transcription)
        except Exception as e:
            logging.error("The file {} could not be written: {}".format(_output, e))
            return swappFileResult(filename, STATUS_REFUSED, str(e))

        return swappFileResult(filename, STATUS_WRITTEN, produced=[_output])
