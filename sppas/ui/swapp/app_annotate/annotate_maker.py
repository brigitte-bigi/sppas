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
from ..swapp_core.swappsg import swapp_settings
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
    def help_document(cls) -> str:
        """Override. Return the path of the document of this app, relative to swapp."""
        return "app_annotate/app_annotate.htm"

    # -----------------------------------------------------------------------

    @classmethod
    def form_id(cls) -> str:
        """Override. Return the identifier of the form carrying the record of the app."""
        return "annotate_form"

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
        self.__view = swappAnnotateView(self._htree, swappAnnotateResponseRecipe.form_id())

        # The case the service is entered in: files stand already where SPPAS
        # reads them when the server is the local one -- the person designates
        # them with the file chooser of the machine. The wsgi service has the
        # files brought to it, and the workspace it gives is a new one.
        _workspace = swappAnnotateResponseRecipe.__workspace()
        _local = swapp_settings.served_locally is True

        # Its container is written in the panel of the files.
        self.__manager = swappFilesManager("annotate_files_panel",
                                           _workspace,
                                           reachable=_local,
                                           has_workspace=len(_workspace.name()) > 0,
                                           form_id=swappAnnotateResponseRecipe.form_id())

        # The model is given the manager of the provision of files the
        # response holds. It holds nothing of a run: the page transmits the
        # names of its report, of its results and of its process.
        self.__model = swappAnnotateModel(self.__manager)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        The tasks of Annotate are answered first; the other events are offered
        to the provision of files.

        :param events: (dict) key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f" >>>>> Page Application Annotate -- Process events: {events} <<<<<< ")
        self._data = dict()
        self._status.code = 200

        # The controller is built at every request and handed the model: it
        # is dropped once the request is answered, and nothing of what was
        # decided is kept.
        self.__controller = swappAnnotateController(self.__model, self.__view)

        # The page transmits the record of the provision of files at every
        # request: the copy the annotations work on is rebuilt from it,
        # before anything of Annotate is answered.
        _consumed = self.__manager.consumes(events)

        # Received events from an HTTP Post.
        if "event_bake" in events:
            # What is raised is caught here, and by nothing below: the
            # annotations cannot be read, or a run cannot be started.
            # Whoever runs the machine reads it in the log, and the person is
            # told that the annotations could not be performed.
            try:
                self.__controller.handle(events)
            except Exception as e:
                logging.error("The annotations could not be performed: {}".format(e))
                self.__controller.say_not_performed()

            # --- Action event to start over: a reset, or another batch ---
            if self.__controller.starts_over() is True:
                self.__manager.start_over()

        # Received events from a request manager, filled in self._data. Where
        # the run stands is not one of them: the base recipe answers it, as
        # for any process.
        elif "event_name" in events:

            # --- Report event: the report of the run the page follows, as
            # it is written, answered alone by its identifier ---
            if events["event_name"] == "annotate_report":
                self.__controller.handle(events)
                self._data["annotate_report"] = self.__view.report(self.__controller.followed_report())

            # --- Unknown event_name ---
            else:
                logging.error(f"Unknown event_name={events['event_name']}")
                self._status.code = 205  # Reset Content

            self.__controller = None
            return False

        # Received events of the provision of files.
        elif _consumed is False and len(events) > 0:
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

        elif self._status.code == 200:
            # Fills-in the body_main node
            self._htree.body_main.clear_children()
            self.__controller.populate_view()
            # The container of the provision of files, in the panel of the
            # files when the view wrote it. It is answered alone as well, to
            # the requests of that service: what is done in it replaces it,
            # and the page stays the one it is.
            self.__manager.populate_view()
            _container = self.__manager.container()
            if self.__view.files is not None:
                self.__view.files.append_child(_container)
            else:
                # Without the panel of the files, the page carries the record
                # of the provision of files all the same: the requests of
                # the form of the run hand it over.
                _main = self._htree.body_main
                _main.append_child(self.__manager.carried(_main.identifier))
            self._data["container"] = _container.serialize()
            # The container of the options, and the values the page carries
            # for them, answered alone as well to whoever asks for data
            # rather than for a page.
            if self.__view.options is not None:
                self._data["options"] = self.__view.options.serialize()
                self._data["values"] = self.__view.values
            # The main content of the page is answered as well, by its
            # identifier, to whoever asks for data rather than for a page: the
            # progress, then the report of a run, or what is missing.
            _main = self._htree.body_main
            self._data[_main.get_attribute_value("id")] = _main.serialize()

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
