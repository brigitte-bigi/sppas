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

import json
import logging
import os

from sppas.core.config import paths
from sppas.core.config import sg
from sppas.core.coreutils import sppasTypeError
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata.anndataexc import AioMultiTiersError
from sppas.src.anndata.anndataexc import AioNoTiersError
from sppas.src.anndata.anndataexc import AioEmptyTierError
from sppas.src.anndata.anndataexc import AioLocationTypeError
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States
from sppas.ui import _

# ---------------------------------------------------------------------------

STATUS_WRITTEN = "written"
STATUS_SKIPPED = "skipped"
STATUS_REFUSED = "refused"

# The report of a conversion is named as every report of SPPAS is.
REPORT_PATTERN = "convert"
REPORT_EXTENSION = ".json"
REPORT_PREFIX = "{:s}_{:s}_".format(sg.__name__, REPORT_PATTERN)

MSG_EXISTS = _("The output file already exists.")
MSG_NOT_READ = _("The file could not be read.")
MSG_NOT_WRITTEN = _("The file could not be written.")

# The typed causes of the API when writing. They are bound to the properties
# of the destination, and are stated as they stand.
TYPED_CAUSES = (AioMultiTiersError, AioNoTiersError, AioEmptyTierError, AioLocationTypeError)

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

    def convert(self, batch: sppasWorkspace, destination: str, answers: dict, general_options: dict,
                report=None) -> list:
        """Convert every file of the batch into the destination format.

        What was written is added to the workspace the batch is. No file of
        the batch is removed or rewritten. When a report is given, it is
        written again each time a file has its result.

        :param batch: (sppasWorkspace) Workspace holding the files to be converted
        :param destination: (str) Extension of the destination format, its dot included
        :param answers: (dict) The answer standing for each option, by option
        :param general_options: (dict) "override" and "heuristic", both booleans
        :param report: (swappConversionReport|None) The report of the conversion
        :raises: sppasTypeError: The given batch is not a sppasWorkspace
        :return: (list of swappFileResult) One result per file, in the order of the batch

        """
        if isinstance(batch, sppasWorkspace) is False:
            raise sppasTypeError(batch, "sppasWorkspace")

        _files = batch.get_filename_from_state(States().CHECKED)
        _results = list()
        for _file in _files:
            _results.append(self.convert_one(_file.get_id(), destination, answers, general_options))
            if report is not None:
                report.write(len(_files), _results)

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
            return swappFileResult(filename, STATUS_REFUSED, MSG_NOT_READ)

        try:
            sppasTrsRW(_output).write(_transcription)
        except TYPED_CAUSES as e:
            logging.error("The file {} could not be written: {}".format(_output, e))
            return swappFileResult(filename, STATUS_REFUSED, str(e))
        except Exception as e:
            logging.error("The file {} could not be written: {}".format(_output, e))
            return swappFileResult(filename, STATUS_REFUSED, MSG_NOT_WRITTEN)

        return swappFileResult(filename, STATUS_WRITTEN, produced=[_output])

# ---------------------------------------------------------------------------


class swappConversionReport:
    """The report of one conversion: where it stands, and the result of each file.

    It is a file of the folder of the logs of SPPAS, and it is what any
    process of the server reads to say where a conversion stands. It is
    written again, at once, each time a file has its result: a reader never
    finds it half written. It is finished once the batch has been treated.

    """

    def __init__(self, name: str):
        """Create the report of the given name.

        :param name: (str) Name of the report, without its path
        :raises: ValueError: The name is not the one of a report of Convert

        """
        if name != os.path.basename(name) or name.startswith(REPORT_PREFIX) is False \
                or name.endswith(REPORT_EXTENSION) is False:
            raise ValueError("Not the name of a report of a conversion: {}".format(name))
        self.__name = name

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the report, without its path (str)."""
        return self.__name

    # -----------------------------------------------------------------------

    def write(self, total: int, results: list, finished: bool = False) -> None:
        """Write the report, at once.

        :param total: (int) Number of files of the batch
        :param results: (list of swappFileResult) The results of the files treated
        :param finished: (bool) The batch has been treated

        """
        _lines = list()
        for _result in results:
            _lines.append({"file": _result.file, "status": _result.status,
                           "cause": _result.cause, "produced": _result.produced})
        _filename = os.path.join(paths.logs, self.__name)
        _written = _filename + ".part"
        with open(_written, "w", encoding="utf-8") as fp:
            json.dump({"total": total, "finished": finished, "results": _lines}, fp)
        os.replace(_written, _filename)

    # -----------------------------------------------------------------------

    def read(self) -> tuple:
        """Return the number of files, the results written, and whether the batch was treated.

        :return: (tuple) (int, list of swappFileResult, bool); (0, [], False) when nothing was written

        """
        _filename = os.path.join(paths.logs, self.__name)
        if os.path.exists(_filename) is False:
            return 0, list(), False
        with open(_filename, "r", encoding="utf-8") as fp:
            _data = json.load(fp)
        _results = list()
        for _line in _data["results"]:
            _results.append(swappFileResult(_line["file"], _line["status"], _line["cause"], _line["produced"]))
        return _data["total"], _results, _data["finished"]

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    name = property(get_name, None)
