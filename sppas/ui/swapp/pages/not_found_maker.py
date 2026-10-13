# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.pages.not_found_maker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The web page served when the requested page is not found.

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

from whakerpy.httpd import BaseResponseRecipe

from ..nodes.feedback.hstatus_node import swappHTMLTreeError404

# ---------------------------------------------------------------------------


class swappNotFoundResponseRecipe(BaseResponseRecipe):
    """The not_found.html HTTPD response bakery.

    Served for any page name neither an app nor a page of swapp bakes. Like
    the page of the ended session, this one is the error itself: its tree
    carries the style sheet of the error pages, and neither the nav nor the
    theme of the reader -- a page which is not there is not entered.

    """

    def __init__(self):
        """Create the ResponseRecipe for the "Page not found" page.

        """
        super(swappNotFoundResponseRecipe, self).__init__(
            swappNotFoundResponseRecipe.page(), swappHTMLTreeError404())

    # -----------------------------------------------------------------------
    # OVERRIDE METHODS FROM Whakerpy -- Create the UI
    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return "not_found.html"

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        The status is the one of the page, whatever is received: a name no
        app and no page bakes is not found, and an event is not a reason to
        answer anything else about it. The tree has no dynamic content, so
        it is never re-created.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) False, the page content never changes.

        """
        self._status.code = 404

        return False
