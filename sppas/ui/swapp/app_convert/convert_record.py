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

# ---------------------------------------------------------------------------

# The name of the event which carries the task of a request.
EVENT_TASK = "convert_task"

TASK_DESTINATION = "destination"
TASK_GENERAL = "general"
TASK_CONVERT = "convert"
TASK_RESET = "reset"

TASKS = (TASK_DESTINATION, TASK_GENERAL, TASK_CONVERT, TASK_RESET)

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

    def what_is_missing(self, filenames: list) -> list:
        """Return what is still missing before the conversion can run.

        :param filenames: (list of str) The files of the batch
        :raises: sppasTypeError: The given files are not a list
        :return: (list of str) Empty when the conversion may run

        """
        if isinstance(filenames, (list, tuple)) is False:
            raise sppasTypeError(filenames, "list")

        _missing = list()
        if len(filenames) == 0:
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
        self.__conversion = swappConversion()
        self.__to_be_shown = dict()

    # -----------------------------------------------------------------------

    def serialize(self) -> dict:
        """Return what was decided, as strings a page carries.

        :return: (dict) One entry per name, each of them a string

        """
        _data = dict()
        _data["destination"] = self.__conversion.destination

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
        self.__conversion = swappConversion()
        self.__to_be_shown = dict()

        if isinstance(data.get(EVENT_TASK), str) is True:
            self.__task = data[EVENT_TASK]
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
    conversion = property(get_conversion, None)
    to_be_shown = property(get_to_be_shown, None)
