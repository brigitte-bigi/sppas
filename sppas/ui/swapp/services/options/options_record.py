"""
:filename: sppas.ui.swapp.services.options.options_record.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The data one request carries, and what a page carries back.

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

from .options_set import swappOptionSet

# ---------------------------------------------------------------------------

# The tasks of this service. The name of a task is the name of the event which
# carries it, and its value is the key of the option it is about, if any.
TASK_VALIDATE = "options_validate"
TASK_FILE = "options_file"
TASK_DESCRIBE = "options_describe"
TASK_PUT_BACK = "options_put_back"
TASK_PUT_ALL_BACK = "options_put_all_back"

TASKS = (TASK_VALIDATE, TASK_FILE, TASK_DESCRIBE, TASK_PUT_BACK, TASK_PUT_ALL_BACK)

# The name of the field which carries the set, and the prefix of the name of
# the field which carries the value of one option.
FIELD_SET = "options_set"
FIELD_PREFIX = "option_"

# ---------------------------------------------------------------------------


class swappOptionsRecord:
    """What one request holds: its task, the set, and what is to be shown.

    It comes from no table. It serializes itself for transport and parses
    itself back, and it is held by nobody between two requests.

    """

    def __init__(self):
        """Create a record with nothing in it."""
        self.__task = ""
        self.__asked = ""
        self.__set = swappOptionSet()
        self.__given = dict()
        self.__said = ""
        self.__to_be_shown = ""

    # -----------------------------------------------------------------------

    def serialize(self) -> dict:
        """Return everything a next request needs to rebuild the set.

        :return: (dict) One entry per name, each of them a string

        """
        _carried = dict()
        _carried[FIELD_SET] = self.__set.serialize()

        return _carried

    # -----------------------------------------------------------------------

    @staticmethod
    def parse(data: dict) -> swappOptionsRecord:
        """Return the record of what a page transmitted.

        Nothing transmitted gives a record with an empty set. A box which is
        not ticked is not transmitted by a page: the option of a yes or a no
        whose field is absent was given a no.

        :param data: (dict) What a page sent
        :raises: sppasTypeError: The given data is not a dictionary
        :return: (swappOptionsRecord)

        """
        if isinstance(data, dict) is False:
            raise sppasTypeError(data, "dict")

        _record = swappOptionsRecord()
        if FIELD_SET not in data:
            return _record

        _record.__set = swappOptionSet.rebuild(data[FIELD_SET])
        for _task in TASKS:
            if _task in data:
                _record.__task = _task
                _record.__asked = str(data[_task])

        for _option in _record.__set.for_app():
            _field = FIELD_PREFIX + _option.get_key()
            if _field in data:
                _record.__given[_option.get_key()] = str(data[_field])
            elif _option.get_type() == "bool":
                _record.__given[_option.get_key()] = "False"

        return _record

    # -----------------------------------------------------------------------
    # Getters and setters
    # -----------------------------------------------------------------------

    def get_task(self) -> str:
        """Return the task the request asks for, empty if none (str)."""
        return self.__task

    def get_asked(self) -> str:
        """Return the key of the option the task is about, empty if none (str)."""
        return self.__asked

    def get_set(self) -> swappOptionSet:
        """Return the set of options (swappOptionSet)."""
        return self.__set

    def set_set(self, options: swappOptionSet) -> None:
        """Set the set of options.

        :param options: (swappOptionSet)
        :raises: sppasTypeError: The given set is not a swappOptionSet

        """
        if isinstance(options, swappOptionSet) is False:
            raise sppasTypeError(options, "swappOptionSet")
        self.__set = options

    def get_given(self) -> dict:
        """Return the values the person gave, by key of option (dict)."""
        return self.__given

    def get_said(self) -> str:
        """Return what is said to the person, empty if nothing (str)."""
        return self.__said

    def set_said(self, message: str) -> None:
        """Set what is said to the person.

        :param message: (str) What is to be said, empty for nothing

        """
        self.__said = str(message)

    def get_to_be_shown(self) -> str:
        """Return the key of the option whose description is asked for (str)."""
        return self.__to_be_shown

    def set_to_be_shown(self, key: str) -> None:
        """Set the key of the option whose description is asked for.

        :param key: (str) Key of an option, empty for none

        """
        self.__to_be_shown = str(key)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    task = property(get_task, None)
    asked = property(get_asked, None)
    set = property(get_set, set_set)
    given = property(get_given, None)
    said = property(get_said, set_said)
    to_be_shown = property(get_to_be_shown, set_to_be_shown)
