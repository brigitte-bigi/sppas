"""
:filename: sppas.ui.swapp.app_annotate.annotate_maker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The bakery of the page of Annotate.

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

from .annotate_model import swappAnnotateModel
from .annotate_view import swappAnnotateView
from .annotate_controller import swappAnnotateController

# ---------------------------------------------------------------------------

MSG_TITLE = f"SPPAS {sg.__release__} " + _("Annotate")

# ---------------------------------------------------------------------------


class swappAnnotateResponseRecipe(swappBaseResponse):
    """The annotate.html HTTPD response bakery.

    It receives the events of a request, has the controller answer them,
    and bakes the tree the view built.

    """

    def __init__(self, name: str = "Annotate",
                 tree: HTMLTree | None = None,
                 title: str = MSG_TITLE):
        """Create the ResponseRecipe for the Annotate application.

        :param name: (str) Name of the body main content
        :param tree: (HTMLTree) The tree of the page, None for a new one
        :param title: (str) Title of the page

        """
        self.__manager = None
        self.__model = None
        self.__view = None
        self.__controller = None
        super(swappAnnotateResponseRecipe, self).__init__(name, tree, title)

    # -----------------------------------------------------------------------

    @classmethod
    def help_page(cls) -> str:
        """Return the name of the page serving the document of this app."""
        return "app_annotate.html"

    # -----------------------------------------------------------------------

    @classmethod
    def help_document(cls) -> str:
        """Return the path of the document of this app, relative to swapp."""
        return "app_annotate/app_annotate.htm"

    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return "annotate.html"

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the nodes that can't be invalidated
        by _bake(): head, body_header, body_nav, body_footer, body_script.

        """
        super().create()
        self.__view = swappAnnotateView(self._htree, swappAnnotateResponseRecipe.help_page())

        # The case the service is entered in: files stand already where SPPAS
        # reads them when the server is the local one -- the person designates
        # them with the file chooser of the machine. The wsgi service has the
        # files brought to it, and the workspace it gives is a new one.
        _workspace = swappAnnotateResponseRecipe.__workspace()
        _local = swapp_serverstate.local is True

        # Its container is written in the panel of the files.
        self.__manager = swappFilesManager("annotate_files_panel",
                                           _workspace,
                                           reachable=_local,
                                           has_workspace=len(_workspace.name()) > 0)

        # The model is held by the response: a performance is longer than
        # the request which started it.
        self.__model = swappAnnotateModel(self.__manager)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f" >>>>> Page Application Annotate -- Process events: {events} <<<<<< ")
        self._data = dict()
        self._status.code = 200

        # The controller is built at every request and handed the model: it
        # is dropped once the request is answered, and nothing of what was
        # decided is kept.
        self.__controller = swappAnnotateController(self.__model, self.__view)

        # Received events from an HTTP Post.
        if "event_name" in events:
            e_name = events["event_name"]
            if e_name == "annotate_update":
                self.__process_update_event()
            else:
                self._status.code = 400
                self._data["error"] = f"The server received an unknown event name: {e_name}."
            self.__controller = None
            return False

        else:
            # Events are propagated to the controller, and offered to the
            # provision of files, which is asked to start over on a reset.
            self.__controller.handle(events)
            if events.get("annotate_task") == "reset":
                self.__manager.start_over()
            self.__manager.consumes(events)
            return True

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Create the dynamic page content in HTML.

        It replaces the current HTMLTree if status is 410 or update the
        content of the current HTMLTree.

        """
        self.comment("Body content")
        self.__view.update_accessibility()

        if self._status.code == 410:
            # The 410 is "Gone" response sent when the requested content has been
            # permanently deleted from server, with no forwarding address.
            self._htree = swappHTMLTreeError410()

        elif self._status.code == 200:
            # Fills-in the body_main node
            self._htree.body_main.clear_children()
            self.__controller.populate_view()
            # The container of the provision of files, in the panel of the
            # files when the view wrote it.
            if self.__view.files is not None:
                self.__manager.populate_view()
                self.__view.files.append_child(self.__manager.container())

        else:
            msg = f"Unexpected status '{self._status.code}' while baking the page content."
            logging.error(msg)
            p = self._htree.element("p")
            p.set_value(msg)

        self.__controller = None

    # -----------------------------------------------------------------------
    # PRIVATE
    # -----------------------------------------------------------------------

    def __process_update_event(self):
        """Process the given event coming from the POST of the progress.

        """
        logging.debug(" ******* Annotate update event ******* ")
        self._data["percent"], self._data["header"], self._data["text"] = (
            self.__controller.get_progress_values())

        self._status.code = 202
        if self._data["percent"] >= 100:
            self._status.code = 200

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
