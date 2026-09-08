# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.pages.feedbackmaker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The web page "Feedback" of SPPAS.

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
from ..wappcore.wappsg import wapp_trace

from .feedback_view import FeedbackView

# ---------------------------------------------------------------------------


MSG_TITLE = f"SPPAS {sg.__release__} Feedback"
MSG_FEEDBACK = _("Feedback")

# ---------------------------------------------------------------------------


class FeedbackResponseRecipe(swappBaseResponse):
    """The feedback.html HTTPD response bakery.

    Allows the user to prepare a feedback message and to send it by e-mail
    from its own e-mail client: the message never leaves the application
    by itself.

    """

    def __init__(self, name: str = "Feedback",
                 tree: HTMLTree | None = None,
                 title: str = MSG_TITLE):
        """Create the ResponseRecipe for the "Feedback" page.

        """
        self.__view = None

        super(FeedbackResponseRecipe, self).__init__(name, tree, title)

    # -----------------------------------------------------------------------
    # OVERRIDE METHODS FROM Whakerpy -- Create the UI
    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return "feedback.html"

    # -----------------------------------------------------------------------

    @classmethod
    def name(cls) -> str:
        """Return the short name of the page, displayed in link buttons."""
        return MSG_FEEDBACK

    # -----------------------------------------------------------------------

    @classmethod
    def icon(cls) -> str:
        """Return the name of the image representing the page."""
        return "link_feedback"

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the nodes that can't be invalidated
        by _bake(): head, body_header, body_nav, body_footer, body_script.

        """
        super().create()
        self.__view = FeedbackView(self._htree)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f" >>>>> Page Feedback -- Process events: {events} <<<<<< ")
        self._data = dict()
        self._status.code = 200

        # The send action is handled in the browser: no event of its own.
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
        self.__view.populate_tree_content(wapp_trace.serialize())
