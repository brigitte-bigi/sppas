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
from ..nodes.feedback.hstatus_node import swappHTMLTreeError410

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
        self.__controller = swappAnnotateController(self.__view)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        :param events: (dict) key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f" >>>>> Page Application Annotate -- Process events: {events} <<<<<< ")
        self._data = dict()
        self._status.code = 200
        self.__controller.handle(events)

        return True

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Create the dynamic page content in HTML."""
        self.comment("Body content")
        self.__view.update_accessibility()

        if self._status.code == 410:
            self._htree = swappHTMLTreeError410()
            return

        self._htree.body_main.clear_children()
        self.__controller.populate_view()
