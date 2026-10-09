"""
:filename: sppas.ui.swapp.services.files.files_controller.py
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

import base64
import logging
import os

from sppas.core.coreutils import sppasTypeError

from .files_provision import swappFileProvision
from .files_record import swappFilesRecord
from .files_record import TASK_DESIGNATE
from .files_record import TASK_FINISHED
from .files_record import TASK_PRODUCED
from .files_record import TASK_SEND
from .files_record import TASK_TAKE_BACK
from .files_record import TASKS
from .files_feeding import swappDataFiles
from .files_view import swappDeliveryView
from .files_view import swappDepositView
from .files_workspace import swappWorkspaceFiles

# ---------------------------------------------------------------------------

MSG_FAILED = "What you asked could not be done. Nothing has changed."
MSG_NO_FILE = "No file was obtained."

# ---------------------------------------------------------------------------


class swappFilesController:
    """Read the task a request carries, and answer it.

    It is called once per request: the record is rebuilt from what the page
    transmitted, one task is done, and what is to be shown is put in the
    record. Nothing is held after the request has been answered, and nothing
    is raised: what goes wrong is put in the record and written where whoever
    runs the machine reads it.

    """

    def __init__(self, model: swappFileProvision, deposit_view: swappDepositView,
                 delivery_view: swappDeliveryView, reachable: bool = True,
                 has_workspace: bool = False):
        """Create the controller with what it is given.

        It assembles nothing: the manager builds the model and the views, and
        hands them over.

        The case is assigned here, when an app is entered, and the record
        carries it from one request to the next. It is not read again: a
        workspace exists in the three cases -- one is composed when none is
        given -- so nothing of what it holds tells them apart.

        :param model: (swappFileProvision) The provision of files
        :param deposit_view: (swappDepositView) The container of what is fed
        :param delivery_view: (swappDeliveryView) The container of what was produced
        :param reachable: (bool) True when the person designates files which stand already
        :param has_workspace: (bool) True when the app was given a workspace which is declared
        :raises: sppasTypeError: One of the given objects is of a wrong type

        """
        if isinstance(model, swappFileProvision) is False:
            raise sppasTypeError(model, "swappFileProvision")
        if isinstance(deposit_view, swappDepositView) is False:
            raise sppasTypeError(deposit_view, "swappDepositView")
        if isinstance(delivery_view, swappDeliveryView) is False:
            raise sppasTypeError(delivery_view, "swappDeliveryView")

        if isinstance(reachable, bool) is False:
            raise sppasTypeError(reachable, "bool")
        if isinstance(has_workspace, bool) is False:
            raise sppasTypeError(has_workspace, "bool")

        self.__model = model
        self.__deposit_view = deposit_view
        self.__delivery_view = delivery_view
        self.__reachable = reachable
        self.__has_workspace = has_workspace
        self.__record = swappFilesRecord()
        self.__record.reachable = reachable
        self.__record.has_workspace = has_workspace
        self.__produced = dict()

    # -----------------------------------------------------------------------

    @staticmethod
    def is_a_task(data: dict) -> bool:
        """Return True if the given data carries a task of this service.

        :param data: (dict) What a page sent
        :return: (bool)

        """
        return swappFilesController.task_of(data) in TASKS

    # -----------------------------------------------------------------------

    @staticmethod
    def task_of(data: dict) -> str:
        """Return the task the given data carries.

        The control the person pressed carries it: a button is named after
        its task, and what it holds is what that task needs -- the file to
        be taken back, or nothing. A caller which asks without a page says
        it under the name of a task.

        :param data: (dict) What a page sent
        :return: (str) Empty when no task of this service is carried

        """
        if isinstance(data, dict) is False:
            return ""

        for _task in TASKS:
            if _task in data:
                return _task

        _said = data.get("task", "")
        if _said in TASKS:
            return _said

        return ""

    # -----------------------------------------------------------------------

    def handle(self, data: dict) -> None:
        """Rebuild the record from what a page sent, and do the task it asks.

        What carries no task of this service leaves the record at its default
        values, which is a first request.

        :param data: (dict) What a page sent

        """
        self.__record = swappFilesRecord()
        self.__record.reachable = self.__reachable
        self.__record.has_workspace = self.__has_workspace
        if isinstance(data, dict) is False:
            return

        self.__record.parse(data)
        self.__record.reachable = self.__reachable
        self.__record.has_workspace = self.__has_workspace
        if self.__record.workspace is not None:
            self.__model.works_on(self.__record.workspace)

        _task = swappFilesController.task_of(data)
        if _task not in TASKS:
            self.__record.workspace = self.__model.workspace()
            return

        self.__record.task = _task

        try:
            self.__do(_task, data)
        except Exception as e:
            logging.error(e)
            self.__to_be_shown("failed", MSG_FAILED)

        self.__record.workspace = self.__model.workspace()

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view the record names build its tree.

        A request which asked for no task of this service is a first request,
        and what it shows is the state: the workspace the files are known to,
        as it stands now.

        What an app gave back is shown here and once: it was given in this
        request, and the request which follows is another state.

        """
        if len(self.__produced) > 0:
            self.__to_be_shown("produced", self.__shown_produced())
            self.__produced = dict()

        if self.__record.workspace is None:
            self.__record.workspace = self.__model.workspace()
        if self.__record.has_workspace is True:
            self.__to_be_shown("workspace_name", self.__model.workspace_name())

        self.view().populate_tree_content(self.__record)

    # -----------------------------------------------------------------------

    def start_over(self) -> None:
        """Show the deposit again, with a new workspace holding no file.

        What was produced and that an app has finished are no longer shown.
        The workspace the files were known to is left as it is: a new one is
        worked on.

        """
        self.__produced = dict()
        self.__model.works_on(swappWorkspaceFiles.make_workspace())
        self.__record = swappFilesRecord()
        self.__record.reachable = self.__reachable
        self.__record.has_workspace = self.__has_workspace
        self.__record.workspace = self.__model.workspace()

    # -----------------------------------------------------------------------

    def shows_produced(self, produced: dict) -> None:
        """Keep what an app gave back, to be shown when the view is built.

        It is kept until it is shown, and no longer: what an app gives back is
        shown by the request it was given in.

        :param produced: (dict) Names of the produced files, with their path, by root
        :raises: sppasTypeError: The given files are not a dictionary

        """
        if isinstance(produced, dict) is False:
            raise sppasTypeError(produced, "dict")

        self.__produced = produced

    # -----------------------------------------------------------------------

    def view(self):
        """Return the view the record names.

        What has been fed and not yet sent is shown as a deposit; what an app
        produced is shown as a delivery.

        :return: (swappDepositView|swappDeliveryView)

        """
        _shown = self.__record.to_be_shown
        if "produced" in _shown or "finished" in _shown:
            return self.__delivery_view

        return self.__deposit_view

    # -----------------------------------------------------------------------

    def get_record(self) -> swappFilesRecord:
        """Return what the request holds.

        :return: (swappFilesRecord)

        """
        return self.__record

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __shown_produced(self) -> dict:
        """Return what an app gave back, as it is to be shown.

        A produced file is shown by its name, and the path it stands under
        comes with it: where it is read is the view's, and what is cut from
        a name is decided here.

        :return: (dict) A name and a path for every produced file, by root

        """
        _shown = dict()
        for _root in self.__produced:
            _of_root = list()
            for _filename in self.__produced[_root]:
                _of_root.append((os.path.basename(_filename), _filename))
            _shown[_root] = _of_root

        return _shown

    # -----------------------------------------------------------------------

    def __do(self, task: str, data: dict) -> None:
        """Do the given task, and put in the record what is to be shown.

        :param task: (str) Task the request carries
        :param data: (dict) What a page sent

        """
        if task == TASK_DESIGNATE:
            self.__designate(data)

        elif task == TASK_TAKE_BACK:
            self.__take_back(data)

        elif task == TASK_SEND:
            self.__send(data)

        elif task == TASK_PRODUCED:
            self.__to_be_shown("produced", dict())

        elif task == TASK_FINISHED:
            self.__model.finished()
            self.__to_be_shown("finished", True)

        if self.__reachable is False:
            self.__to_be_shown("accepted", self.__accepted())

    # -----------------------------------------------------------------------

    def __designate(self, data: dict) -> None:
        """Take a file into what is to be sent, and say what is refused.

        :param data: (dict) What a page sent

        """
        _path = data.get(TASK_DESIGNATE, "")
        if isinstance(_path, str) is False:
            _path = ""
        if len(_path) == 0:
            _path = data.get("path", "")
        if len(_path) > 0:
            self.__model.make_known([_path])
            return

        if self.__record.reachable is True:
            if len(self.__model.ask_for_files()) == 0:
                _why = self.__model.why_no_file()
                if len(_why) > 0:
                    self.__to_be_shown("failed", _why)
            return

        _name = data.get("name", "")
        _size = data.get("size", 0)
        _feeding = self.__feeding()
        _accepted, _reason = self.__model.feed(_feeding, _name, int(_size))
        if _accepted is False:
            self.__refused(_name, _reason)
            return

        self.__record.feed(_name, int(_size))

    # -----------------------------------------------------------------------

    def __take_back(self, data: dict) -> None:
        """Take a file back out of what is to be sent.

        :param data: (dict) What a page sent

        """
        _name = data.get(TASK_TAKE_BACK, "")
        if isinstance(_name, str) is False or len(_name) == 0:
            _name = data.get("name", "")
        if len(_name) == 0:
            return

        self.__model.take_out([_name])

        _fed = list()
        for _one_name, _one_size in self.__record.fed:
            if _one_name != _name:
                _fed.append((_one_name, _one_size))

        self.__record.fed = _fed

    # -----------------------------------------------------------------------

    def __send(self, data: dict) -> None:
        """Write what came in a place, and make it known and checked.

        The contents travel one file per request, each of them carrying the
        record: what is written is what came with this request, and the place
        the deposit stands in is carried back for the next one.

        :param data: (dict) What a page sent, holding the bytes of one file

        """
        _contents = swappFilesController.__contents_of(data)
        _feeding = self.__feeding()
        _feeding.place = self.__record.place

        _refused = self.__model.send(_feeding, _contents)
        self.__record.place = _feeding.place
        for _name in _refused:
            if len(_name) == 0:
                self.__to_be_shown("no_place", _refused[_name])
            else:
                self.__refused(_name, _refused[_name])

    # -----------------------------------------------------------------------

    @staticmethod
    def __contents_of(data: dict) -> dict:
        """Return the bytes a page sent, by name of file.

        A page sends one file and its content, encoded, the bytes of a file
        not being text. A caller which is no page gives them as they are.

        :param data: (dict) What a page sent
        :return: (dict) Empty when no content came

        """
        _contents = data.get("contents", dict())
        if isinstance(_contents, dict) is True and len(_contents) > 0:
            return _contents

        _name = data.get("name", "")
        _content = data.get("content", "")
        if isinstance(_name, str) is False or len(_name) == 0:
            return dict()
        if isinstance(_content, bytes) is True:
            return {_name: _content}
        if isinstance(_content, str) is False or len(_content) == 0:
            return dict()

        try:
            return {_name: base64.b64decode(_content, validate=True)}
        except (ValueError, TypeError):
            logging.error("The content of {} could not be read.".format(_name))
            return dict()

    # -----------------------------------------------------------------------

    def __feeding(self) -> swappDataFiles:
        """Return the files fed so far, rebuilt from the record.

        :return: (swappDataFiles)

        """
        _feeding = swappDataFiles()
        for _name, _size in self.__record.fed:
            _feeding.feed(_name, _size)

        return _feeding

    # -----------------------------------------------------------------------

    def __accepted(self) -> str:
        """Return what is accepted, said in a few words.

        :return: (str) Empty when the deposit API answers nothing

        """
        try:
            _accepted = self.__model.what_is_accepted()
        except NotImplementedError:
            return ""

        return "{:d} of {:d} bytes accepted here. Up to {:d} bytes per file.".format(
            self.__record_volume(), _accepted["volume"], _accepted["size"])

    # -----------------------------------------------------------------------

    def __record_volume(self) -> int:
        """Return the volume of what was fed, in bytes.

        :return: (int)

        """
        _volume = 0
        for _name, _size in self.__record.fed:
            _volume += _size

        return _volume

    # -----------------------------------------------------------------------

    def __refused(self, name: str, reason: str) -> None:
        """Put a refusal in the record, beside the file it is about.

        :param name: (str) Name of the refused file
        :param reason: (str) Why it is refused

        """
        _shown = self.__record.to_be_shown
        _refused = _shown.get("refused", dict())
        _refused[name] = reason
        _shown["refused"] = _refused
        self.__record.to_be_shown = _shown

    # -----------------------------------------------------------------------

    def __to_be_shown(self, key: str, value) -> None:
        """Put one thing to be shown in the record.

        :param key: (str) What it is
        :param value: What is to be shown

        """
        _shown = self.__record.to_be_shown
        _shown[key] = value
        self.__record.to_be_shown = _shown

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    record = property(get_record, None)
