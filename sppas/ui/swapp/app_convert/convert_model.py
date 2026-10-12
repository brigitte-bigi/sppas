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

import os
from threading import Thread

from sppas.core.coreutils import sppasLogFile
from sppas.src.wkps import States

from ..services.files import swappFilesManager

from .convert_formats import swappModelFormats
from .convert_conversion import swappModelConversion
from .convert_conversion import swappConversionReport
from .convert_conversion import REPORT_PATTERN
from .convert_conversion import REPORT_EXTENSION
from .convert_provision import swappModelProvision
from .convert_record import swappConversion

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
        """Return the formats which can be written, with what each of them holds.

        :return: (list of swappFormat)

        """
        return self.__formats.writable_formats()

    # -----------------------------------------------------------------------

    def batch(self):
        """Return the batch: the workspace the provision of files hands.

        :return: (sppasWorkspace) Can hold no file at all

        """
        return self.__provision.batch()

    # -----------------------------------------------------------------------

    def start(self, batch, conversion: swappConversion) -> str:
        """Start the conversion of the batch on the server, and return the name of its report.

        The report is written before the conversion starts: whoever asks where
        it stands finds it, with no file treated yet.

        :param batch: (sppasWorkspace) The workspace the provision of files handed
        :param conversion: (swappConversion) What was decided
        :return: (str) Name of the report, without its path

        """
        _report = swappConversionReport(os.path.basename(sppasLogFile(pattern=REPORT_PATTERN, extension=REPORT_EXTENSION).get_filename()))
        _report.write(len(batch.get_filename_from_state(States().CHECKED)), list())
        Thread(target=self.convert, args=(batch, conversion, _report), daemon=True).start()
        return _report.name

    # -----------------------------------------------------------------------

    @staticmethod
    def read_report(name: str) -> tuple:
        """Return where a conversion stands, as its report says it.

        :param name: (str) Name of the report, without its path
        :raises: ValueError: The name is not the one of a report of Convert
        :return: (tuple) Number of files, the results written, and whether the batch was treated

        """
        return swappConversionReport(name).read()

    # -----------------------------------------------------------------------

    def convert(self, batch, conversion: swappConversion, report=None) -> list:
        """Convert the batch, and give back to the provision of files what was produced.

        The files of the batch are locked while they are converted, and
        released once each has its result. What was written is added to the
        batch, which is given back, and that the batch has been treated is said.
        When a report is given, it is written as the files have their result,
        and finished once the batch has been treated.

        :param batch: (sppasWorkspace) The workspace the provision of files handed
        :param conversion: (swappConversion) What was decided
        :param report: (swappConversionReport|None) The report of the conversion
        :return: (list of swappFileResult) One result per file, in the order of the batch

        """
        _filenames = list()
        for _file in batch.get_filename_from_state(States().CHECKED):
            _filenames.append(_file.get_id())

        _general_options = dict()
        _general_options["override"] = conversion.override
        _general_options["heuristic"] = conversion.heuristic

        self.__provision.lock(_filenames)
        _results = self.__conversion.convert(batch, conversion.destination, dict(), _general_options, report)
        self.__provision.release(_filenames)
        self.__provision.produced(batch)
        self.__provision.finished()
        if report is not None:
            report.write(len(_filenames), _results, finished=True)

        return _results
