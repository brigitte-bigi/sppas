# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.pages.helpmaker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application ResponseRecipe of the help page of an app.

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

from ..wappbase.wappresponse import swappBaseResponse

from .help_view import HelpView

# ---------------------------------------------------------------------------


class HelpResponseRecipe(swappBaseResponse):
    """The response bakery of the document of an app.

    One recipe for all of them: an app differs only by the document it
    declares. The document holds both the user manual and the conceptual
    folder of the app, written by hand and served as it is.

    """

    def __init__(self, document: str, page: str, title: str, css: str = "",
                 tree: HTMLTree | None = None):
        """Create the ResponseRecipe for the document of an app.

        :param document: (str) Path of the document, relative to swapp
        :param page: (str) Name of the page serving the document
        :param title: (str) Title of the documented app
        :param css: (str) Filename of the stylesheet of the documented app

        """
        self.__view = None
        self.__document = document
        self.__page = page
        self.__css = css

        super(HelpResponseRecipe, self).__init__(page, tree, title)

    # -----------------------------------------------------------------------
    # OVERRIDE METHODS FROM Whakerpy -- Create the UI
    # -----------------------------------------------------------------------

    def page(self) -> str:
        """Override. Return the HTML page name."""
        return self.__page

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the nodes that can't be invalidated
        by _bake(): head, body_header, body_nav, body_footer, body_script.

        """
        super().create()
        self.__view = HelpView(self._htree, self._title, self.__css)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f" >>>>> Page Help -- Process events: {events} <<<<<< ")
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

        self._status.code, msg = self.__view.populate_tree_content(self.__document)
        if self._status.code != 200:
            logging.error(msg)
            p = self._htree.element("p")
            p.set_value(msg)
