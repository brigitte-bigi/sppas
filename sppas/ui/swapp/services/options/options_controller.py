"""
:filename: sppas.ui.swapp.services.options.options_controller.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Read the task a request carries, and answer it.

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

from sppas.ui import _

from .options_file import swappFileForOption
from .options_record import swappOptionsRecord
from .options_record import FIELD_SET
from .options_record import TASK_FILE
from .options_record import TASK_VALIDATE
from .options_record import TASKS
from .options_set import swappOptionSet
from .options_view import swappOptionsView

# ---------------------------------------------------------------------------

MSG_NO_FILE = _("No file was obtained.")

# ---------------------------------------------------------------------------


class swappOptionsController:
    """Read the task a request carries, and answer it.

    It is called once per request: the set is rebuilt from what the page
    transmitted, the values she gave are taken in, and one task is done.

    """

    def __init__(self, view: swappOptionsView, options: list | None = None):
        """Create the controller with the options an app hands over.

        :param view: (swappOptionsView) The view of this service
        :param options: (list of sppasOption) What the app lets one set

        """
        self.__view = view
        self.__files = swappFileForOption()
        self.__record = swappOptionsRecord()
        self.__record.set = swappOptionSet(options)

    # -----------------------------------------------------------------------

    @staticmethod
    def is_a_task(data: dict) -> bool:
        """Return True if the given data carries a task of this service.

        :param data: (dict) What a page sent
        :return: (bool)

        """
        if isinstance(data, dict) is False:
            return False
        for _task in TASKS:
            if _task in data:
                return True

        return False

    # -----------------------------------------------------------------------

    def handle(self, data: dict) -> None:
        """Rebuild the record from what a page sent, and do the task it asks.

        What carries no set of this service changes nothing: it is a first
        request, and the options are the ones the app handed over.

        :param data: (dict) What a page sent

        """
        if isinstance(data, dict) is False or FIELD_SET not in data:
            return

        _record = swappOptionsRecord.parse(data)
        if _record.task not in (TASK_VALIDATE, TASK_FILE):
            raise NotImplementedError

        # Every request carries the whole set: what she gave is taken in
        # whatever the task, so that asking for a file loses nothing of it.
        _record.set.validate(_record.given)
        if _record.task == TASK_FILE:
            self.__obtain_file(_record)

        self.__record = _record

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build its tree from the record."""
        self.__view.populate_tree_content(self.__record)

    # -----------------------------------------------------------------------

    def options_for_app(self) -> list:
        """Return the options, every one holding the value it holds.

        :return: (list of sppasOption)

        """
        return self.__record.set.for_app()

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __obtain_file(self, record: swappOptionsRecord) -> None:
        """Ask for the file of the option the task is about, and take it in.

        An option which got no file keeps the value it held, and it is said.

        :param record: (swappOptionsRecord) The record of the request

        """
        for _option in record.set.for_app():
            if _option.get_key() == record.asked:
                _request = self.__files.ask_for(_option)
                _filename = self.__files.file_of(_request)
                if len(_filename) > 0:
                    self.__files.take_in(record.set, _request.option, _filename)
                else:
                    record.said = MSG_NO_FILE
