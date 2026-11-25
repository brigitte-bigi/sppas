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
from ..nodes.feedback.hstatus_node import swappHTMLTreeError410

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
        self.__view = swappPluginsView(self._htree)

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

        # The controller is built at every request: it is dropped once the
        # request is answered, and nothing of what was decided is kept.
        self.__controller = swappPluginsController(self.__view)

        if "event_bake" in events:
            self.__controller.handle(events)

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

        else:
            msg = f"Unexpected status '{self._status.code}' while baking the page content."
            logging.error(msg)
            p = self._htree.element("p")
            p.set_value(msg)

        self.__controller = None
