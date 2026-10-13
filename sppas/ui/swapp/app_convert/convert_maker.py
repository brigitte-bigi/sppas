"""
:filename: sppas.ui.swapp.app_convert.convert_maker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The response recipe of the Convert application.

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

from whakerpy.htmlmaker import HTMLTree

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_response import swappBaseResponse
from ..swapp_core.swappsg import swapp_serverstate
from ..swapp_core.swappsg import swapp_wkps
from ..swapp_core.swappsg import swapp_wxstate
from ..nodes.feedback.hstatus_node import swappHTMLTreeError410
from ..services.files import swappFilesManager
from ..services.files import swappWorkspaceFiles

from .convert_model import swappConvertModel
from .convert_view import swappConvertView
from .convert_controller import swappConvertController
from .convert_record import EVENT_TASK
from .convert_record import TASK_RESET
from .convert_record import TASK_UPDATE
from .convert_record import EVENT_NAME

# ---------------------------------------------------------------------------

MSG_TITLE = f"SPPAS {sg.__release__} " + _("Convert")

# The names of what is answered to a request asking for data, and not for a page.
DATA_CONVERT = "convert"
DATA_CONTAINER = "container"
DATA_INFO = "info"

# ---------------------------------------------------------------------------


class swappConvertResponseRecipe(swappBaseResponse):
    """The convert.html HTTPD response bakery.

    It holds the manager of the provision of files, which that service
    requires an app to hold between two requests. It answers the tasks of
    Convert first, and offers what it does not recognise to the manager. The
    operations on files are handed to the model, which gives them to the
    only class of Convert calling that service on files.

    """

    def __init__(self, name: str = "Convert",
                 tree: HTMLTree | None = None,
                 title: str = MSG_TITLE):
        """Create the ResponseRecipe for the Convert application.

        :param name: (str) Name of the body main content
        :param tree: (HTMLTree) The tree of the page, None for a new one
        :param title: (str) Title of the page

        """
        self.__manager = None
        self.__view = None
        self.__controller = None
        super(swappConvertResponseRecipe, self).__init__(name, tree, title)

    # -----------------------------------------------------------------------

    @classmethod
    def help_page(cls) -> str:
        """Return the name of the page serving the document of this app."""
        return "app_convert.html"

    # -----------------------------------------------------------------------

    @classmethod
    def help_document(cls) -> str:
        """Return the path of the document of this app, relative to swapp."""
        return "app_convert/app_convert.htm"

    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return "convert.html"

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the nodes that can't be invalidated
        by _bake(): head, body_header, body_nav, body_footer, body_script.

        """
        super().create()
        self.__view = swappConvertView(self._htree, swappConvertResponseRecipe.help_page())

        # The case the service is entered in: files stand already where SPPAS
        # reads them when the server is the local one -- the person designates
        # them with the file chooser of the machine. The wsgi service has the
        # files brought to it, and the workspace it gives is a new one.
        _workspace = swappConvertResponseRecipe.__workspace()
        _local = swapp_serverstate.local is True

        self.__manager = swappFilesManager(self._htree.body_main.identifier,
                                           _workspace,
                                           reachable=_local,
                                           has_workspace=len(_workspace.name()) > 0)
        self.__controller = swappConvertController(swappConvertModel(self.__manager), self.__view)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        The tasks of Convert are answered first; the other events are offered
        to the provision of files.

        :param events: (dict) key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f" >>>>> Page Application Convert -- Process events: {events} <<<<<< ")
        self._data = dict()
        self._status.code = 200

        # The record is rebuilt at every request from what was transmitted.
        self.__controller.handle(events)
        # Where the conversion stands is answered alone: the page is not rebuilt.
        if events.get(EVENT_NAME) == TASK_UPDATE:
            self._data["percent"], self._data["header"], self._data["text"] = self.__controller.progress()
            self._status.code = 202
            if self._data["percent"] >= 100:
                self._status.code = 200
            return False
        if swappConvertController.is_a_task(events) is True:
            if events.get(EVENT_TASK) == TASK_RESET:
                self.__manager.start_over()
            return True

        if self.__manager.consumes(events) is False and len(events) > 0:
            logging.error(f"Unknown events={events}")
            self._status.code = 205
        elif self.__manager.is_ready() is True:
            self.__controller.say_what_is_missing()

        return True

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Create the dynamic page content in HTML.

        The container of the provision of files is appended first, then the
        section of the conversion. Both are answered alone as well, to
        whoever asks for data rather than for a page.

        """
        self.comment("Body content")
        self.__view.update_accessibility()

        if self._status.code == 410:
            self._htree = swappHTMLTreeError410()
            return

        self._htree.body_main.clear_children()
        self.__view.populate_introduction()
        self.__manager.populate_view()
        _container = self.__manager.container()
        self._htree.body_main.append_child(_container)
        self.__controller.populate_view()

        self._data[DATA_CONTAINER] = _container.serialize()
        self._data[DATA_CONVERT] = self.__view.section.serialize()
        if len(self.__view.info) > 0:
            self._data[DATA_INFO] = self.__view.info

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __workspace() -> swappWorkspaceFiles:
        """Return the workspace of the moment, and the name it is known under.

        The workspace a reader declared is on the machine of the local
        server: the wsgi service exposes it to readers it knows nothing
        about, and the files of one are not the files of another.

        :return: (swappWorkspaceFiles) One with no file in it when none is to be used

        """
        if swapp_serverstate.local is True:
            _name = swapp_wxstate.workspace_name
            if len(_name) > 0:
                return swappWorkspaceFiles(swapp_wkps.data, _name)

        return swappWorkspaceFiles()
