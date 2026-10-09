# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_test.tests_page_files.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The page which tests the provision of files.

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


"""

from __future__ import annotations
import logging
import os

from whakerpy.htmlmaker import HTMLNode

from sppas.core.config import sg
from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.swapp_core.swappsg import swapp_wkps
from sppas.ui.swapp.swapp_core.swappsg import swapp_wxstate
from sppas.ui.swapp.nodes import swappHTMLButton
from sppas.ui.swapp.swapp_base.swapp_response import swappBaseResponse
from sppas.ui.swapp.swapp_core.swapp_utils import swappImagesAccess
from sppas.ui.swapp.services.files import swappFilesManager
from sppas.ui.swapp.services.files import swappWorkspaceFiles

from .tests_view import swappTestsBaseView

# ---------------------------------------------------------------------------

MSG_TITLE = "Test of the provision of files"
MSG_APP_TITLE = "What an app does"
MSG_APP_TEXT = ("This page is an app which has no work of its own: it asks "
                "the service for the files to treat, writes one file beside "
                "the first of them, gives the workspace back and says it has "
                "finished. What the person sees above is the container of "
                "the service, and nothing of it is built here.")
MSG_NO_FILE = "No file is to be treated."

PRODUCED_EXTENSION = ".TextGrid"

JS_VALUE = (
    "import { OnLoadManager, LinkController } from "
    f"'/{swapp_settings.wexa_statics}js/wexa.js';"
    "\nimport SwappFiles from "
    f"'/{swapp_settings.js}swapp_files.js';"
    """

OnLoadManager.addLoadFunction(() => {
    new LinkController().handleLinksWithParameters(["home_button"]);
    new SwappFiles().handleSwappFilesOnLoad();
});

"""
)

# ---------------------------------------------------------------------------


class swappTestFilesResponseRecipe(swappBaseResponse):
    """Bake the page which tests the provision of files.

    The page holds what an app holds of the service -- its manager -- and
    does what an app does with it: it offers it the events, has it build,
    and appends its container. When the person said the workspace is ready,
    it plays the part of an app which treats files, so that what is given
    back has something to show.

    """

    def __init__(self, name="TestFiles", tree=None,
                 title=sg.__name__ + " Test of the files"):
        """Create the recipe of the page.

        :param name: (str) Name of the body main content

        """
        self.__manager = None
        super(swappTestFilesResponseRecipe, self).__init__(name, tree, title)

    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Return the name of the page."""
        return "test_files.html"

    # -----------------------------------------------------------------------

    @staticmethod
    def name() -> str:
        """Return the name of the test."""
        return "The provision of files"

    # -----------------------------------------------------------------------

    @staticmethod
    def description() -> str:
        """Return a short description of the test."""
        return ("What a person designates, what an app receives, and what it "
                "gives back.")

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed content of the page."""
        super().create()

        _view = swappTestsBaseView(self._htree, MSG_TITLE, JS_VALUE)
        _view.append_back_link_button(self._htree.body_nav)

        self.__manager = swappFilesManager(self._htree.body_main.identifier,
                                           swappTestFilesResponseRecipe.__workspace())

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Answer the events of a request.

        The events are offered to the service. When the person said the
        workspace is ready, the files are treated: it is the app which asks
        for them and gives back what it produced.

        :param events: (dict) key=event_name, value=event_value
        :return: (bool) True when the whole page has to be baked again

        """
        logging.debug(" >>>>> Page {} -- Process events: {} <<<<<< "
                      "".format(swappTestFilesResponseRecipe.page(), events))
        self._status.code = 200

        if self.__manager.consumes(events) is True:
            if self.__manager.is_ready() is True:
                self.__treat()
            return True

        return True

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Create the content of the page.

        The container of the service is asked for and appended; what this
        page adds is under it.

        """
        self.comment("Body content")
        self._htree.body_main.clear_children()

        self.__manager.populate_view()
        _container = self.__manager.container()
        self._htree.body_main.append_child(_container)
        # The container is answered alone to whoever asks for data: the person
        # composes what she sends without the page being reloaded, and a
        # browser gives no content back once its page is gone.
        self._data = {"container": _container.serialize()}

        _h2 = HTMLNode(self._htree.body_main.identifier, None, "h2",
                       value=MSG_APP_TITLE)
        self._htree.body_main.append_child(_h2)
        _p = HTMLNode(self._htree.body_main.identifier, None, "p",
                      value=MSG_APP_TEXT)
        self._htree.body_main.append_child(_p)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __workspace() -> swappWorkspaceFiles:
        """Return the workspace of the moment, and the name it is known under.

        What says whether there is one is the interface which declares it: the
        shared one holds the last it was given, and holds it still when that
        interface has gone.

        :return: (swappWorkspaceFiles) One with no file in it when none is declared

        """
        _name = swapp_wxstate.workspace_name
        if len(_name) == 0:
            return swappWorkspaceFiles()

        return swappWorkspaceFiles(swapp_wkps.data, _name)

    # -----------------------------------------------------------------------

    def __treat(self) -> None:
        """Do what an app does with the files it is given.

        The files are locked while they are treated: one file is written
        beside the first of them, the workspace is given back to the service,
        the files are released, and the treatment is said to be over.

        """
        _handed = self.__manager.files_for_app()
        _files = swappWorkspaceFiles.known_files(_handed)
        if len(_files) == 0:
            logging.info(MSG_NO_FILE)
            return

        _names = list()
        for _one in _files:
            _names.append(_one.get_id())
        self.__manager.lock(_names)

        _produced = os.path.splitext(_names[0])[0] + PRODUCED_EXTENSION
        with open(_produced, "w") as _fd:
            _fd.write("")
        _handed.add_file(_produced)

        self.__manager.produced(_handed)
        self.__manager.release(_names)
        self.__manager.consumes({"task": "finished"})
