"""
:filename: sppas.ui.swapp.services.files.files_manager.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The entry class an app holds of this service.

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
import logging
import os

from sppas.core.config import cfg
from sppas.core.coreutils import sppasTypeError
from sppas.ui import _

from .files_controller import swappFilesController
from .files_place import swappFilePlace
from .files_provision import swappFileProvision
from .files_record import TASK_READY
from .files_view import swappDepositView
from .files_workspace import swappWorkspaceFiles

# ---------------------------------------------------------------------------

MSG_NO_WINDOW = _("This computer cannot open the window to choose files. "
                  "Send them instead, as on a web service.")

# ---------------------------------------------------------------------------


class swappFilesManager:
    """Entry class of the provision of files: what an app holds of it.

    An app has a maker which builds the fixed part of its page, its view and
    its controller. This service has no page of its own, so it has this
    instead: it builds the model, the two views and the controller, and it is
    the only object of this service an app ever holds.

    """

    def __init__(self, parent: str, workspace: swappWorkspaceFiles | None = None,
                 place: swappFilePlace | None = None, reachable: bool = True,
                 has_workspace: bool = False):
        """Create what an app holds of this service.

        The case an app is in is said here, when it is entered, and the record
        carries it from one request to the next: whether the files stand
        already where SPPAS reads them, and whether the workspace it was given
        is one which is declared. A workspace exists in the three cases, so
        neither of these is read from it.

        :param parent: (str) Identifier of the node the container is appended to
        :param workspace: (swappWorkspaceFiles) The files of the workspace, None for a new one
        :param place: (swappFilePlace) The places of the deposit API, None for a new one where files are brought
        :param reachable: (bool) True when the person designates files which stand already
        :param has_workspace: (bool) True when the given workspace is one which is declared
        :raises: sppasTypeError: The given parent is not a string

        """
        if isinstance(parent, str) is False:
            raise sppasTypeError(parent, "str")

        # Designating a file of the machine opens a window, and that window
        # is tkinter. Without it, the person cannot say where her files are,
        # so she sends them instead: the deposit is the way in, exactly as on
        # a web service, and she is told why.
        _switched = False
        if reachable is True and cfg.feature_installed("tkinter") is False:
            logging.info("No tkinter on this machine: the files are deposited "
                         "instead of being designated.")
            reachable = False
            _switched = True

        self.__model = swappFileProvision(workspace, place, reachable=reachable)
        self.__deposit_view = swappDepositView(parent)
        self.__controller = swappFilesController(self.__model, self.__deposit_view, reachable, has_workspace)
        if _switched is True:
            self.__controller.say(MSG_NO_WINDOW)

    # -----------------------------------------------------------------------

    def consumes(self, events: dict) -> bool:
        """Answer whether the events of a request were for this service.

        An app offers what it did not recognize; nothing is changed when the
        answer is false, and what nobody consumed is the app's to answer.

        :param events: (dict) The events a request carries
        :return: (bool) True when they were treated here

        """
        if swappFilesController.is_a_task(events) is False:
            return False

        self.__controller.handle(events)

        return True

    # -----------------------------------------------------------------------

    def is_ready(self) -> bool:
        """Answer whether the person said the workspace is ready.

        It is read in the request this service consumed last: an app asks it
        after consumes(), and asks for the files when it is true.

        :return: (bool) True when that request carried the task ready

        """
        return self.__controller.record.task == TASK_READY

    # -----------------------------------------------------------------------

    def start_over(self) -> None:
        """Show the deposit again, the person starting over.

        The files are known to a new workspace, holding none, and nothing of
        what was produced or finished is shown.

        """
        self.__controller.start_over()

    # -----------------------------------------------------------------------

    def files_for_app(self):
        """Return a workspace with the files an app has to treat in it.

        :return: (sppasWorkspace) Can hold no file at all

        """
        return self.__model.files_for_app()

    # -----------------------------------------------------------------------

    def produced(self, workspace) -> dict:
        """Write what an app produced into the workspace, and check it.

        Nothing of it is shown by this service: the app shows it. An app
        gives back as often as it has something to give back.

        :param workspace: (sppasWorkspace) Workspace an app gives back
        :return: (dict) Names of the produced files, with their path, by root

        """
        _produced = self.__model.produced(workspace)

        return _produced

    # -----------------------------------------------------------------------

    def address_of(self, filename: str) -> str:
        """Return the address a produced file is reached at.

        Where the files stand already on the machine of the person, she
        reaches what was produced where it was written and no address is
        made: the answer is then empty, and the app says where the file
        stands instead of leading to it.

        :param filename: (str) Name of the file, with its path
        :return: (str) Empty when the file is reached at no address

        """
        _place = self.__controller.record.place
        if len(_place) == 0:
            return ""

        return self.__model.address_of(_place, os.path.basename(filename))

    # -----------------------------------------------------------------------

    def address_of_all(self, filenames: list) -> str:
        """Return the address of one archive holding the produced files.

        A batch of ten files is got back in one gesture and not in ten.
        Where the person reaches the files where they stand, nothing is
        archived and the answer is empty.

        :param filenames: (list of str) Names of the files, with their path
        :return: (str) Empty when no archive is to be made

        """
        _place = self.__controller.record.place
        if len(_place) == 0:
            return ""

        return self.__model.address_of_all(_place, filenames)

    # -----------------------------------------------------------------------

    def serve(self, address: str) -> bytes:
        """Return the bytes an address names.

        :param address: (str) Address to be served
        :return: (bytes) Empty when there is nothing to give

        """
        return self.__model.serve(address)

    # -----------------------------------------------------------------------

    def lock(self, filenames: list) -> int:
        """Say the app takes these files, and is treating them.

        A file it takes is no longer one to be treated, so a request which
        follows is not given it again.

        :param filenames: (list of str) Names of the files, with their path
        :return: (int) Number of locked files

        """
        return self.__model.lock(filenames)

    # -----------------------------------------------------------------------

    def release(self, filenames: list) -> int:
        """Say the app gives these files back: they were treated.

        :param filenames: (list of str) Names of the files, with their path
        :return: (int) Number of released files

        """
        self.__controller.treated(filenames)
        return self.__model.release(filenames)

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view the record names build its tree."""
        self.__controller.populate_view()

    # -----------------------------------------------------------------------

    def container(self):
        """Return the container an app appends in its page.

        The view it comes from is the one the record names, so it is read
        after the events of the request were offered.

        :return: (TagNode) The node of the view which was populated

        """
        return self.__deposit_view.node
