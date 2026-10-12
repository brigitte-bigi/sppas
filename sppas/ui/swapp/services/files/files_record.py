"""
:filename: sppas.ui.swapp.services.files.files_record.py
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

import json

from sppas.core.coreutils import sppasTypeError
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps.wio import sppasWJSON

from .files_feeding import swappDataFeeding

# ---------------------------------------------------------------------------

TASK_DESIGNATE = "designate"
TASK_TAKE_BACK = "take_back"
TASK_SEND = "send"
TASK_READY = "ready"
TASK_PRODUCED = "produced"
TASK_FINISHED = "finished"

TASKS = (TASK_DESIGNATE, TASK_TAKE_BACK, TASK_SEND, TASK_READY, TASK_PRODUCED, TASK_FINISHED)

# ---------------------------------------------------------------------------


class swappFilesRecord:
    """Convenient class to hold the data of one request.

    It holds the task the request asks for, the workspace the files are known
    to, the files fed so far -- a name and a size each, where they have to be
    brought and are nowhere yet -- and what is to be shown. The two first are serialized into
    strings a page carries and sends back; the third is not, being decided by
    the request which shows it. The files are written as JSON: a name holds any
    character but a separator of paths, and no character is safe to cut on.

    """

    def __init__(self):
        """Create a record with nothing in it."""
        self.__task = ""
        self.__fed = list()
        self.__workspace = None
        self.__reachable = True
        self.__has_workspace = False
        self.__place = ""
        self.__treated = list()
        self.__to_be_shown = dict()

    # -----------------------------------------------------------------------

    def reset(self) -> None:
        """Set every entry of the record back to its default value."""
        self.__task = ""
        self.__fed = list()
        self.__workspace = None
        self.__reachable = True
        self.__has_workspace = False
        self.__place = ""
        self.__treated = list()
        self.__to_be_shown = dict()

    # -----------------------------------------------------------------------

    def serialize(self) -> dict:
        """Return the task and the fed files as strings.

        The task is not in it, and what is to be shown is not either: the
        task is what the control the person pressed says, and what is shown
        is decided by the request which shows it.

        :return: (dict) One entry per name, each of them a string

        """
        _fed = list()
        for _name, _size in self.__fed:
            _fed.append([_name, _size])

        _data = dict()
        _data["reachable"] = str(self.__reachable)
        _data["has_workspace"] = str(self.__has_workspace)
        _data["place"] = self.__place
        _data["fed"] = json.dumps(_fed)
        _data["treated"] = json.dumps(self.__treated)
        if self.__workspace is not None:
            _wjson = sppasWJSON()
            _wjson.set(self.__workspace)
            _data["workspace"] = json.dumps(_wjson.serialize())

        return _data

    # -----------------------------------------------------------------------

    def parse(self, data: dict) -> None:
        """Fill in the record with what a page sent.

        An entry which is absent keeps its default value, and an entry which
        cannot be read is left out rather than guessed.

        :param data: (dict) What a page sent
        :raises: sppasTypeError: The given data is not a dictionary

        """
        if isinstance(data, dict) is False:
            raise sppasTypeError(data, "dict")

        self.reset()
        if "task" in data:
            self.set_task(data["task"])
        if "reachable" in data:
            self.set_reachable(str(data["reachable"]) == "True")
        if "has_workspace" in data:
            self.set_has_workspace(str(data["has_workspace"]) == "True")
        if "place" in data:
            self.set_place(data["place"])

        for _one in swappFilesRecord.__fed_entry(data):
            try:
                self.feed(_one[0], _one[1])
            except (TypeError, ValueError):
                pass

        self.__workspace = swappFilesRecord.__workspace_entry(data)
        self.__treated = swappFilesRecord.__treated_entry(data)

    # -----------------------------------------------------------------------

    def feed(self, name: str, size: int | float) -> None:
        """Add a fed file to the record.

        :param name: (str) Name of the file, without any path
        :param size: (int|float) Size of the file, in bytes, a whole number
        :raises: sppasTypeError: The name or the size is of a wrong type
        :raises: sppasValueError: The name is empty or is a path, or the size is not whole
        :raises: NegativeValueError: The size is negative

        """
        self.__fed.append((swappDataFeeding.validate_name(name),
                           swappDataFeeding.validate_size(size)))

    # -----------------------------------------------------------------------

    def get_workspace(self):
        """Return the workspace the files are known to.

        :return: (sppasWorkspace) None when the page carried none

        """
        return self.__workspace

    # -----------------------------------------------------------------------

    def set_workspace(self, workspace) -> None:
        """Set the workspace the files are known to.

        :param workspace: (sppasWorkspace) Workspace to be carried, or None
        :raises: sppasTypeError: The given workspace is not a sppasWorkspace

        """
        if workspace is not None and isinstance(workspace, sppasWorkspace) is False:
            raise sppasTypeError(workspace, "sppasWorkspace")

        self.__workspace = workspace

    # -----------------------------------------------------------------------

    def get_reachable(self) -> bool:
        """Return whether the files stand already where SPPAS reads them.

        :return: (bool) False when they have to be brought

        """
        return self.__reachable

    # -----------------------------------------------------------------------

    def set_reachable(self, reachable: bool) -> None:
        """Set whether the files stand already where SPPAS reads them.

        It is said by the interface the person gives through -- a path or a
        content -- and never read from anything else.

        :param reachable: (bool) True when the files stand already
        :raises: sppasTypeError: The given value is not a boolean

        """
        if isinstance(reachable, bool) is False:
            raise sppasTypeError(reachable, "bool")

        self.__reachable = reachable

    # -----------------------------------------------------------------------

    def get_has_workspace(self) -> bool:
        """Return whether a workspace holds the files to be treated.

        :return: (bool) False when there is none to use

        """
        return self.__has_workspace

    # -----------------------------------------------------------------------

    def set_has_workspace(self, has_workspace: bool) -> None:
        """Set whether a workspace holds the files to be treated.

        It is said by what reads the workspaces, and never by what shows
        them: a view which looked at a list to tell the two cases apart
        would be a view which decides.

        :param has_workspace: (bool) True when a workspace is there to be used
        :raises: sppasTypeError: The given value is not a boolean

        """
        if isinstance(has_workspace, bool) is False:
            raise sppasTypeError(has_workspace, "bool")

        self.__has_workspace = has_workspace

    # -----------------------------------------------------------------------

    def get_place(self) -> str:
        """Return the place the deposit API gave for what is sent.

        The contents travel in as many requests as there are files, so the
        place a deposit stands in is asked for once and carried from one
        request to the next: a second place would be a second deposit.

        :return: (str) Empty as long as no place was asked for

        """
        return self.__place

    # -----------------------------------------------------------------------

    def set_place(self, place: str) -> None:
        """Set the place the deposit API gave for what is sent.

        :param place: (str) Place of the deposit, as that API gave it
        :raises: sppasTypeError: The given place is not a string

        """
        if isinstance(place, str) is False:
            raise sppasTypeError(place, "str")

        self.__place = place.strip()

    # -----------------------------------------------------------------------

    def get_task(self) -> str:
        """Return the task the request asks for.

        :return: (str) Empty if the request asks for none

        """
        return self.__task

    # -----------------------------------------------------------------------

    def set_task(self, task: str) -> None:
        """Set the task the request asks for.

        :param task: (str) Name of the task
        :raises: sppasTypeError: The given task is not a string

        """
        if isinstance(task, str) is False:
            raise sppasTypeError(task, "str")

        self.__task = task.strip()

    # -----------------------------------------------------------------------

    def get_fed(self) -> list:
        """Return the fed files, in the order they were added.

        :return: (list of tuple) A name and a size each, can be empty

        """
        return self.__fed

    # -----------------------------------------------------------------------

    def set_fed(self, fed: list) -> None:
        """Set the fed files.

        :param fed: (list of tuple) A name and a size each
        :raises: sppasTypeError: The given files are not a list of two-value tuples
        :raises: sppasValueError: A name is empty or is a path, or a size is not whole
        :raises: NegativeValueError: A size is negative

        """
        if isinstance(fed, (list, tuple)) is False:
            raise sppasTypeError(fed, "list")

        self.__fed = list()
        for _one in fed:
            if isinstance(_one, (list, tuple)) is False or len(_one) != 2:
                raise sppasTypeError(_one, "tuple of a name and a size")
            self.feed(_one[0], _one[1])

    # -----------------------------------------------------------------------

    def get_treated(self) -> list:
        """Return the names of the files an app treated (list of str)."""
        return self.__treated

    # -----------------------------------------------------------------------

    def set_treated(self, names: list) -> None:
        """Set the names of the files an app treated.

        :param names: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list

        """
        if isinstance(names, list) is False:
            raise sppasTypeError(names, "list")
        self.__treated = list()
        for _name in names:
            self.__treated.append(str(_name))

    # -----------------------------------------------------------------------

    def get_to_be_shown(self) -> dict:
        """Return what is to be shown.

        :return: (dict) Empty if nothing is to be shown

        """
        return self.__to_be_shown

    # -----------------------------------------------------------------------

    def set_to_be_shown(self, to_be_shown: dict) -> None:
        """Set what is to be shown.

        :param to_be_shown: (dict) What a view is to show
        :raises: sppasTypeError: The given value is not a dictionary

        """
        if isinstance(to_be_shown, dict) is False:
            raise sppasTypeError(to_be_shown, "dict")

        self.__to_be_shown = to_be_shown

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __workspace_entry(data: dict):
        """Return the workspace a page sent.

        It is read by the domain of the workspaces, which wrote it: what is
        not a workspace it can read gives none, and nothing is guessed.

        :param data: (dict) What a page sent
        :return: (sppasWorkspace) None if the entry is absent or unreadable

        """
        if isinstance(data.get("workspace"), str) is False:
            return None

        try:
            _read = json.loads(data["workspace"])
            _wjson = sppasWJSON()
            _wjson.parse(_read)
        except Exception:
            return None

        return _wjson

    # -----------------------------------------------------------------------

    @staticmethod
    def __treated_entry(data: dict) -> list:
        """Return the names of the treated files a page sent.

        :param data: (dict) What a page sent
        :return: (list of str) Empty if the entry is absent or unreadable

        """
        if isinstance(data.get("treated"), str) is False:
            return list()
        try:
            _read = json.loads(data["treated"])
        except ValueError:
            return list()
        if isinstance(_read, list) is False:
            return list()
        _treated = list()
        for _one in _read:
            if isinstance(_one, str) is True:
                _treated.append(_one)
        return _treated

    # -----------------------------------------------------------------------

    @staticmethod
    def __fed_entry(data: dict) -> list:
        """Return the fed files a page sent, as pairs of two values.

        :param data: (dict) What a page sent
        :return: (list of list) Empty if the entry is absent or unreadable

        """
        if isinstance(data.get("fed"), str) is False:
            return list()

        try:
            _read = json.loads(data["fed"])
        except ValueError:
            return list()

        if isinstance(_read, list) is False:
            return list()

        _fed = list()
        for _one in _read:
            if isinstance(_one, list) is True and len(_one) == 2:
                _fed.append(_one)

        return _fed

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    task = property(get_task, set_task)
    reachable = property(get_reachable, set_reachable)
    has_workspace = property(get_has_workspace, set_has_workspace)
    place = property(get_place, set_place)
    fed = property(get_fed, set_fed)
    workspace = property(get_workspace, set_workspace)
    treated = property(get_treated, set_treated)
    to_be_shown = property(get_to_be_shown, set_to_be_shown)
