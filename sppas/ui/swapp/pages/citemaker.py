# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.pages.citemaker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The web page "How to cite" of SPPAS.

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

from ..wappbase.wappresponse import swappBaseResponse

from .cite_view import CiteView

# ---------------------------------------------------------------------------


MSG_TITLE = f"SPPAS {sg.__release__} How to cite"
MSG_CITE = _("How to cite")

# ---------------------------------------------------------------------------


class CiteResponseRecipe(swappBaseResponse):
    """The cite.html HTTPD response bakery.

    Displays the reference to be cited when SPPAS is used, and a link to
    the list of all specific publications.

    """

    def __init__(self, name: str = "Cite",
                 tree: HTMLTree | None = None,
                 title: str = MSG_TITLE):
        """Create the ResponseRecipe for the "How to cite" page.

        """
        self.__view = None

        super(CiteResponseRecipe, self).__init__(name, tree, title)

    # -----------------------------------------------------------------------
    # OVERRIDE METHODS FROM Whakerpy -- Create the UI
    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return "cite.html"

    # -----------------------------------------------------------------------

    @classmethod
    def name(cls) -> str:
        """Return the short name of the page, displayed in link buttons."""
        return MSG_CITE

    # -----------------------------------------------------------------------

    @classmethod
    def icon(cls) -> str:
        """Return the name of the image representing the page."""
        return "link_publis"

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the nodes that can't be invalidated
        by _bake(): head, body_header, body_nav, body_footer, body_script.

        """
        super().create()
        self.__view = CiteView(self._htree)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f" >>>>> Page How to cite -- Process events: {events} <<<<<< ")
        self._data = dict()
        self._status.code = 200

        # This page defines no event of its own.
        if len(events) > 0:
            logging.error(f"Unknown events={events}")
            self._status.code = 205  # Reset Content

        return True

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Create the dynamic page content in HTML.

        """
        self.comment("Body content")
        self.__view.update_accessibility()
        self.__view.populate_tree_content()
