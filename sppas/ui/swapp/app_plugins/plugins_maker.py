"""
:filename: sppas.ui.swapp.app_plugins.plugins_maker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The response recipe of the Plugins application.

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
from ..swapp_core.swappsg import swapp_settings
from ..swapp_core.swappsg import swapp_wkps
from ..swapp_core.swappsg import swapp_wxstate
from ..nodes.feedback.hstatus_node import swappHTMLTreeError410
from ..services.files import swappFilesManager
from ..services.files import swappWorkspaceFiles

from .plugins_model import swappPluginsModel
from .plugins_view import swappPluginsView
from .plugins_controller import swappPluginsController

# ---------------------------------------------------------------------------

MSG_TITLE = f"SPPAS {sg.__release__} " + _("Plugins")

# ---------------------------------------------------------------------------


class swappPluginsResponseRecipe(swappBaseResponse):
    """The plugins.html HTTPD response bakery.

    It receives the events of a request, has the controller answer them,
    and bakes the tree the view built.

    """

    def __init__(self, name: str = "Plugins",
                 tree: HTMLTree | None = None,
                 title: str = MSG_TITLE):
        """Create the ResponseRecipe for the Plugins application.

        :param name: (str) Name of the body main content
        :param tree: (HTMLTree) The tree of the page, None for a new one
        :param title: (str) Title of the page

        """
        self.__manager = None
        self.__model = None
        # A start which was refused changed nothing of the files: the page
        # keeps the container it shows.
        self.__refused = False
        # A plugin which was installed changed the section of the plugins:
        # the page replaces its own with it.
        self.__installed = False
        self.__view = None
        self.__controller = None
        super(swappPluginsResponseRecipe, self).__init__(name, tree, title)

    # -----------------------------------------------------------------------

    @classmethod
    def help_document(cls) -> str:
        """Override. Return the path of the document of this app, relative to swapp."""
        return "app_plugins/app_plugins.htm"

    # -----------------------------------------------------------------------

    @classmethod
    def form_id(cls) -> str:
        """Override. Return the identifier of the form carrying the record of the app."""
        return "plugins_form"

    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return "plugins.html"

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the nodes that can't be invalidated
        by _bake(): head, body_header, body_nav, body_footer, body_script.

        """
        super().create()
        self.__view = swappPluginsView(self._htree, swappPluginsResponseRecipe.form_id())

        # The case the service is entered in: files stand already where SPPAS
        # reads them when the server is the local one -- the person designates
        # them with the file chooser of the machine. The wsgi service has the
        # files brought to it, and the workspace it gives is a new one.
        _workspace = swappPluginsResponseRecipe.__workspace()
        _local = swapp_settings.served_locally is True

        # Its container is written in the section of the files.
        self.__manager = swappFilesManager("plugins_files_section",
                                           _workspace,
                                           reachable=_local,
                                           has_workspace=len(_workspace.name()) > 0)

        # The model is held by the response: what is installed is read in
        # the domain of the plugins it holds. A domain which cannot be
        # created is written in the log, and the page says that no plugin
        # can be listed.
        try:
            self.__model = swappPluginsModel(self.__manager)
        except Exception as e:
            logging.error("No plugin can be listed: {}".format(e))
            self.__model = None

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        :param events: (dict) key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        self._data = dict()
        self._status.code = 200
        self.__refused = False
        self.__installed = False

        # No plugin can be listed: nothing can be asked.
        if self.__model is None:
            return True

        # The controller is built at every request: it is dropped once the
        # request is answered, and nothing of what was decided is kept.
        self.__controller = swappPluginsController(self.__model, self.__view)

        # The record is rebuilt at every request from what was transmitted,
        # and the controller does the task it carries. What is raised is
        # caught here, and by nothing below but what the error policy names:
        # whoever runs the machine reads it in the log, and the person is
        # told that the plugins could not be run.
        try:
            self.__controller.handle(events)
        except Exception as e:
            logging.error("The plugins could not be run: {}".format(e))
            self.__controller.say_not_performed()

        if "event_bake" in events:

            # --- Action event to start over: the files go with the decisions ---
            if events["event_bake"] == "plugins_reset":
                self.__manager.start_over()

            # --- Action event to start the runs ---
            elif events["event_bake"] == "plugins_run":
                self.__refused = self.__controller.is_running() is False

            # --- Action event to install a plugin ---
            elif events["event_bake"] == "plugins_install":
                self.__installed = self.__controller.has_installed()

        # Received events of the provision of files.
        elif self.__manager.consumes(events) is False and len(events) > 0:
            logging.error(f"Unknown events={events}")
            self._status.code = 205  # Reset Content

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

        elif self._status.code == 200 and self.__model is None:
            # No plugin can be listed: the page says so, in the dialog of
            # the errors.
            self._htree.body_main.clear_children()
            self.__view.populate_unavailable()
            self._data["error"] = self.__view.error

        elif self._status.code == 200:
            # Fills-in the body_main node
            self._htree.body_main.clear_children()
            self.__controller.populate_view()
            # The container of the provision of files, in the section of the
            # files. It is answered alone as well, to the requests of that
            # service: what is done in it replaces it, and the page stays the
            # one it is.
            self.__manager.populate_view()
            _container = self.__manager.container()
            if self.__view.files is not None:
                self.__view.files.append_child(_container)
            if self.__refused is False:
                self._data["container"] = _container.serialize()
            # The container of the options of a plugin, and what the page
            # writes of that plugin, answered alone as well to whoever asks
            # for data rather than for a page.
            if self.__view.options is not None:
                self._data["options"] = self.__view.options.serialize()
            if len(self.__view.values) > 0:
                self._data["values"] = self.__view.values
            # The section of the runs, the one of the plugins when a plugin
            # was installed, and what is said, answered alone as well to
            # whoever asks for data rather than for a page.
            if self.__view.run is not None:
                self._data["run"] = self.__view.run.serialize()
            if self.__installed is True:
                self._data["plugins"] = self.__view.plugins.serialize()
            if len(self.__view.error) > 0:
                self._data["error"] = self.__view.error
            if len(self.__view.info) > 0:
                self._data["info"] = self.__view.info

        else:
            msg = f"Unexpected status '{self._status.code}' while baking the page content."
            logging.error(msg)
            p = self._htree.element("p")
            p.set_value(msg)

        self.__controller = None

    # -----------------------------------------------------------------------
    # PRIVATE
    # -----------------------------------------------------------------------

    @staticmethod
    def __workspace() -> swappWorkspaceFiles:
        """Return the workspace of the moment, and the name it is known under.

        The workspace a reader declared is on the machine of the local
        server: the wsgi service exposes it to readers it knows nothing
        about, and the files of one are not the files of another.

        :return: (swappWorkspaceFiles) One with no file in it when none is to be used

        """
        if swapp_settings.served_locally is True:
            _name = swapp_wxstate.workspace_name
            if len(_name) > 0:
                return swappWorkspaceFiles(swapp_wkps.data, _name)

        return swappWorkspaceFiles()
