"""
:filename: sppas.ui.swapp.app_convert.convert_record.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What one request holds, and what was decided.

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

from sppas.core.coreutils import sppasTypeError
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

# ---------------------------------------------------------------------------

# The name of the event which carries the task of a request.
EVENT_TASK = "convert_task"

TASK_CONVERT = "convert"
TASK_RESET = "reset"

TASKS = (TASK_CONVERT, TASK_RESET)

# The events which follow a conversion, named as the ones of the Setup:
# where it stands is asked by an event, its results by an event which bakes.
EVENT_NAME = "event_name"
EVENT_BAKE = "event_bake"
TASK_UPDATE = "update"
TASK_COMPLETE = "complete"

# The name of the field which carries the name of the report of a conversion.
FIELD_REPORT = "convert_report"

MISSING_BATCH = "batch"

# ---------------------------------------------------------------------------


class swappConversion:
    """What was decided for one conversion.

    The destination and the two general options. It is rebuilt at every
    request from what the page transmitted, and held between none. There is
    always one destination, once the controller has set its default.

    """

    def __init__(self):
        """Create a conversion with nothing decided."""
        self.__destination = ""
        self.__override = False
        self.__heuristic = False

    # -----------------------------------------------------------------------

    def what_is_missing(self, batch: sppasWorkspace) -> list:
        """Return what is still missing before the conversion can run.

        The batch is given and not held: it belongs to the provision of files.

        :param batch: (sppasWorkspace) The workspace the provision of files hands
        :raises: sppasTypeError: The given batch is not a sppasWorkspace
        :return: (list of str) Empty when the conversion may run

        """
        if isinstance(batch, sppasWorkspace) is False:
            raise sppasTypeError(batch, "sppasWorkspace")

        _missing = list()
        if len(batch.get_filename_from_state(States().CHECKED)) == 0:
            _missing.append(MISSING_BATCH)

        return _missing

    # -----------------------------------------------------------------------

    def get_destination(self) -> str:
        """Return the extension of the destination format (str)."""
        return self.__destination

    # -----------------------------------------------------------------------

    def set_destination(self, destination: str) -> None:
        """Set the extension of the destination format.

        :param destination: (str) Extension of the format, its dot included
        :raises: sppasTypeError: The given destination is not a string

        """
        if isinstance(destination, str) is False:
            raise sppasTypeError(destination, "str")

        self.__destination = destination.strip()

    # -----------------------------------------------------------------------

    def get_override(self) -> bool:
        """Return True if an existing output file may be replaced (bool)."""
        return self.__override

    # -----------------------------------------------------------------------

    def set_override(self, value: bool) -> None:
        """Set whether an existing output file may be replaced.

        :param value: (bool)
        :raises: sppasTypeError: The given value is not a boolean

        """
        if isinstance(value, bool) is False:
            raise sppasTypeError(value, "bool")

        self.__override = value

    # -----------------------------------------------------------------------

    def get_heuristic(self) -> bool:
        """Return True if the format of an unknown extension may be detected (bool)."""
        return self.__heuristic

    # -----------------------------------------------------------------------

    def set_heuristic(self, value: bool) -> None:
        """Set whether the format of an unknown extension may be detected.

        :param value: (bool)
        :raises: sppasTypeError: The given value is not a boolean

        """
        if isinstance(value, bool) is False:
            raise sppasTypeError(value, "bool")

        self.__heuristic = value

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    destination = property(get_destination, set_destination)
    override = property(get_override, set_override)
    heuristic = property(get_heuristic, set_heuristic)

# ---------------------------------------------------------------------------


class swappConvertRecord:
    """What one request holds: its task, what was decided, and what is shown.

    The view serialises it at each action and the controller parses it back,
    and neither of them holds it between two requests. What is to be shown is
    not serialised: it is decided by the request which shows it.

    """

    def __init__(self):
        """Create a record with nothing in it."""
        self.__task = ""
        self.__report = ""
        self.__conversion = swappConversion()
        self.__to_be_shown = dict()

    # -----------------------------------------------------------------------

    def serialize(self) -> dict:
        """Return what was decided, as strings a page carries.

        :return: (dict) One entry per name, each of them a string

        """
        _data = dict()
        _data["destination"] = self.__conversion.destination
        _data[FIELD_REPORT] = self.__report

        return _data

    # -----------------------------------------------------------------------

    def parse(self, data: dict) -> None:
        """Fill in the record with what a page sent.

        An entry which is absent takes its default value.

        :param data: (dict) What a page sent
        :raises: sppasTypeError: The given data is not a dictionary

        """
        if isinstance(data, dict) is False:
            raise sppasTypeError(data, "dict")

        self.__task = ""
        self.__report = ""
        self.__conversion = swappConversion()
        self.__to_be_shown = dict()

        if isinstance(data.get(EVENT_TASK), str) is True:
            self.__task = data[EVENT_TASK]
        elif data.get(EVENT_NAME) == TASK_UPDATE:
            self.__task = TASK_UPDATE
        elif data.get(EVENT_BAKE) == TASK_COMPLETE:
            self.__task = TASK_COMPLETE
        if isinstance(data.get(FIELD_REPORT), str) is True:
            self.__report = data[FIELD_REPORT]
        if isinstance(data.get("destination"), str) is True:
            self.__conversion.destination = data["destination"]
        self.__conversion.override = str(data.get("override", False)) == "True"
        self.__conversion.heuristic = str(data.get("heuristic", False)) == "True"

    # -----------------------------------------------------------------------

    def show(self, key: str, value) -> None:
        """Put one thing to be shown in the record.

        :param key: (str) What it is
        :param value: What is to be shown

        """
        self.__to_be_shown[key] = value

    # -----------------------------------------------------------------------

    def get_task(self) -> str:
        """Return the task the request asks for, empty if none (str)."""
        return self.__task

    # -----------------------------------------------------------------------

    def get_report(self) -> str:
        """Return the name of the report of the conversion, empty if none (str)."""
        return self.__report

    # -----------------------------------------------------------------------

    def set_report(self, name: str) -> None:
        """Set the name of the report of the conversion the page follows.

        :param name: (str) Name of the report, without its path

        """
        self.__report = str(name)

    # -----------------------------------------------------------------------

    def get_conversion(self) -> swappConversion:
        """Return what was decided (swappConversion)."""
        return self.__conversion

    # -----------------------------------------------------------------------

    def get_to_be_shown(self) -> dict:
        """Return what is to be shown (dict)."""
        return self.__to_be_shown

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    task = property(get_task, None)
    report = property(get_report, set_report)
    conversion = property(get_conversion, None)
    to_be_shown = property(get_to_be_shown, None)
