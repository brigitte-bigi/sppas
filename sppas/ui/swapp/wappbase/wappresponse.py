# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.wappbase.wappresponse.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application ResponseRecipe.

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

import os
from whakerpy.htmlmaker import HTMLNode
from whakerpy.httpd import BaseResponseRecipe

from ..wappcore.wappsg import wapp_settings
from ..wappcore.wappsg import wapp_wxstate
from .wapphead import swappHeadNode
from .wapphead import THEME_NAMES
from .wapphead import COLOR_NAMES
from .wapphead import CONTRAST_NAMES
from ..nodes.feedback.hstatusnode import HTMLTreeError410
from ..nodes.feedback.exit_dialog import ExitWaitDialog

# ---------------------------------------------------------------------------


class swappBaseResponse(BaseResponseRecipe):
    """Create a Response system for dynamic pages.

    The page can or cannot have a static body->main content.

    """
    _name = ""

    def __init__(self,
                 name: str | None = None,
                 tree: HTMLNode | None = None,
                 title: str = "SPPAS"):
        """Create a HTTPD Response instance with a default response.

        :param name: (str) Filename of the body main content.

        """
        self._name = name
        if name is not None:
            self._page_name = os.path.basename(name)
        else:
            name = "undefined"
            self._page_name = ""

        # Inheritance with a given dynamic HTMLTree.
        super(swappBaseResponse, self).__init__(name=name, tree=tree, title=title)

    # ---------------------------------------------------------------------------
    # PUBLIC STATIC METHODS
    # ---------------------------------------------------------------------------

    @classmethod
    def page(cls):
        """Return the current HTML body->main filename or an empty string."""
        return cls._name

    # -----------------------------------------------------------------------

    def get_pagename(self) -> str:
        """Return the name of the HTML page as seen in the URL."""
        return self._page_name

    # -----------------------------------------------------------------------

    def set_pagename(self, page_name: str):
        """Set the name of this page as seen in the url.

        :param page_name: (str) Name of the HTML page.

        """
        self._page_name = page_name
        # Update current nav page
        self._htree.body_nav.set_nav_current(page_name)

    # -----------------------------------------------------------------------

    def __set_waiting(self, waiting: bool) -> None:
        """Mark the page as waiting for the exit, or not.

        :param waiting: (bool) True while the other interface has not answered

        """
        classes = self._htree.get_body_attribute_value("class")
        if classes is None:
            classes = ""
        names = [name for name in classes.split(" ") if len(name) > 0]

        if waiting is True and "exit-waiting" not in names:
            names.append("exit-waiting")
        elif waiting is False and "exit-waiting" in names:
            names.remove("exit-waiting")

        self._htree.set_body_attribute("class", " ".join(names))

    # -----------------------------------------------------------------------

    @staticmethod
    def asks_for_a_page(headers) -> bool:
        """Return True if the request asks for a page, and not for data.

        :param headers: (dict) The headers of the http request received
        :return: (bool) True when the answer is a page to be displayed

        """
        if headers is None:
            return True
        accepted = headers.get("Accept", "text/html")
        return "application/json" not in accepted

    # -----------------------------------------------------------------------

    def bake(self, events: dict, headers: dict = None) -> str:
        """Override. Translate the ambient state before processing the events.

        The Whakerexa client attaches its own parameters (`wexa_*`) to every
        navigation URL, and WhakerPy turns the query string of a GET into
        events. None of them is an application event: the color and contrast
        schemes are restored by the AccessibilityManager of the client, and
        every `wexa_*` parameter is removed here.

        Turning them into accessibility events left a page with no content:
        a recipe answers such an event with "nothing changed", which is true
        of the POST it was written for -- the page is already displayed --
        but not of a GET, which is a navigation and has a page to build.

        The three managers of the client announce what they applied: the
        theme, the color scheme and the contrast one. They are kept here, the
        only place every request goes through, so that SPPAS opens again the
        way its reader left it. An empty value is the way it is shown by
        default. The theme of an application is its identity and not a
        preference: a name SPPAS does not carry is not kept.

        :param events: (dict) The requested events to be processed
        :param headers: (dict) The headers of the http request received

        """
        # The state of an exit, asked for by the periodic call of any page:
        # an exit of SPPAS concerns them all, and not the Dashboard alone.
        if "exit_state" in events:
            self._data = {"exit_pending": wapp_wxstate.exit_pending,
                          "exit_granted": wapp_wxstate.exit_granted}
            self._status.code = 200
            return self._htree.serialize()

        # The exit was granted: whoever asks for a page gets the last one.
        # A request for data is answered as usual -- the server stops once
        # it has served the page, and data nobody displays would stop it
        # with no page shown at all.
        if wapp_wxstate.exit_granted is True:
            if swappBaseResponse.asks_for_a_page(headers) is True:
                self._status.code = 410
                return HTMLTreeError410().serialize()

        # The page is served blocked when an exit is waiting: it is written
        # open, and the boot of the page shows it before anything can be
        # clicked. The footer holding it is built once, so it is the answer
        # which says what it looks like, request after request.
        dialog = self._htree.body_footer.get_child(ExitWaitDialog.ID)
        if dialog is not None:
            if wapp_wxstate.exit_pending is True:
                dialog.set_attribute("class", "info")
            else:
                dialog.set_attribute("class", "hidden-alert info")

        # While the exit waits, the page is grey and answers nothing: the
        # dialog can be dismissed -- Escape closes any modal dialog -- and
        # a page which would then act on a click would be in a state its
        # reader decided nothing about.
        self.__set_waiting(wapp_wxstate.exit_pending)
        if wapp_wxstate.exit_pending is True:
            events.clear()

        for event_name in list(events.keys()):
            if event_name.startswith("wexa_") is True:
                events.pop(event_name)

        # The manager of the theme announces it under the name "theme",
        # without the prefix the two others carry.
        if "theme" in events:
            theme = events.pop("theme")
            if theme in THEME_NAMES:
                wapp_settings.accessibility_theme = theme

        if "accessibility_color" in events:
            color = events.pop("accessibility_color")
            if color in COLOR_NAMES:
                wapp_settings.accessibility_color = color

        if "accessibility_contrast" in events:
            contrast = events.pop("accessibility_contrast")
            if contrast in CONTRAST_NAMES:
                wapp_settings.accessibility_contrast = contrast

        return super(swappBaseResponse, self).bake(events, headers)

    # -----------------------------------------------------------------------
    # Construct the tree
    # -----------------------------------------------------------------------

    def create(self):
        """To be overridden. Create the page tree.

        Create the head of the dynamic tree.

        """
        self._htree.head = swappHeadNode(self._htree.identifier, title=self._title)
        self._htree.body_main.set_attribute("id", "main-content")

    # -----------------------------------------------------------------------
    # Override WhakerPy private methods
    # -----------------------------------------------------------------------

    def _invalidate(self):
        """Override. Remove children nodes of the body->main."""
        self._htree.body_main.clear_children()
