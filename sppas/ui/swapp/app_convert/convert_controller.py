"""
:filename: sppas.ui.swapp.app_convert.convert_controller.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What reads the task of a request and answers it.

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

from sppas.core.config import annots
from sppas.core.coreutils import sppasTypeError

from .convert_model import swappConvertModel
from .convert_record import swappConvertRecord
from .convert_record import EVENT_TASK
from .convert_record import TASK_CONVERT
from .convert_record import TASK_RESET
from .convert_record import TASK_COMPLETE
from .convert_record import EVENT_BAKE
from .convert_record import TASKS
from .convert_view import swappConvertView

# ---------------------------------------------------------------------------


class swappConvertController:
    """Read the task a request carries, and answer it.

    The record is rebuilt from what the page transmitted, one task is done,
    and what is to be shown is put in the record. It is the only class which
    knows what the page transmits.

    """

    def __init__(self, model: swappConvertModel, view: swappConvertView):
        """Create the controller with what it is given.

        :param model: (swappConvertModel) The model of Convert
        :param view: (swappConvertView) The view of Convert
        :raises: sppasTypeError: One of the given objects is of a wrong type

        """
        if isinstance(model, swappConvertModel) is False:
            raise sppasTypeError(model, "swappConvertModel")
        if isinstance(view, swappConvertView) is False:
            raise sppasTypeError(view, "swappConvertView")

        self.__model = model
        self.__view = view
        self.__record = swappConvertRecord()
        self.__record.conversion.destination = annots.annot_extension

    # -----------------------------------------------------------------------

    @staticmethod
    def is_a_task(events: dict) -> bool:
        """Return True if the given events carry a task of Convert.

        :param events: (dict) What a page sent
        :return: (bool)

        """
        if isinstance(events, dict) is False:
            return False

        if events.get(EVENT_BAKE) == TASK_COMPLETE:
            return True
        return events.get(EVENT_TASK, "") in TASKS

    # -----------------------------------------------------------------------

    def handle(self, data: dict) -> None:
        """Rebuild the record from what a page sent, and do the task it asks.

        :param data: (dict) What a page sent

        """
        _record = swappConvertRecord()
        _record.parse(data)
        self.__set_destination(_record)

        if _record.task == TASK_CONVERT:
            self.__start(_record)
        elif _record.task == TASK_COMPLETE:
            self.__complete(_record)
        elif _record.task == TASK_RESET:
            _record = swappConvertRecord()
            _record.conversion.destination = annots.annot_extension

        self.__record = _record

    # -----------------------------------------------------------------------

    def progress(self) -> tuple:
        """Return where the conversion the page follows stands, as its report says it.

        :return: (tuple) The percent of files treated, a header and a text

        """
        try:
            _total, _results, _finished = self.__model.read_report(self.__record.report)
        except ValueError as e:
            logging.error(str(e))
            return 100, "", ""
        _percent = 0
        if _finished is True:
            _percent = 100
        elif _total > 0:
            _percent = min(99, (100 * len(_results)) // _total)
        return _percent, "", "{:d} / {:d}".format(len(_results), _total)

    # -----------------------------------------------------------------------

    def say_what_is_missing(self) -> None:
        """Have what is still missing said again: the workspace was said ready."""
        self.__record.show("ready", True)

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build its tree from the record.

        What is still missing is said again at every request: the batch is
        read where it stands, and it may have changed since the last one.

        """
        self.__record.show("missing", self.__record.conversion.what_is_missing(self.__model.batch()))
        self.__record.show("formats", self.__model.writable_formats())

        self.__view.populate_tree_content(self.__record)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __set_destination(self, record: swappConvertRecord) -> None:
        """Keep the destination if it can be written, the default one otherwise.

        :param record: (swappConvertRecord) The record of the request

        """
        if self.__format_of(record.conversion.destination) is None:
            record.conversion.destination = annots.annot_extension

    # -----------------------------------------------------------------------

    def __start(self, record: swappConvertRecord) -> None:
        """Start the conversion of the batch, when nothing is missing.

        :param record: (swappConvertRecord) The record of the request

        """
        _batch = self.__model.batch()
        if len(record.conversion.what_is_missing(_batch)) > 0:
            return

        record.report = self.__model.start(_batch, record.conversion)
        record.show("converting", True)

    # -----------------------------------------------------------------------

    def __complete(self, record: swappConvertRecord) -> None:
        """Show the results of the conversion, as its report gives them.

        :param record: (swappConvertRecord) The record of the request

        """
        try:
            _total, _results, _finished = self.__model.read_report(record.report)
        except ValueError as e:
            logging.error(str(e))
            return

        record.show("results", _results)

    # -----------------------------------------------------------------------

    def __format_of(self, destination: str):
        """Return the writable format of the given extension.

        :param destination: (str) Extension of a format, its dot included
        :return: (swappFormat) None when no writable format has this extension

        """
        for _format in self.__model.writable_formats():
            if _format.extension.lower() == destination.lower():
                return _format

        return None
