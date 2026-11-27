# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.swapp_base.swapp_redirect.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application page leading to a secret name of an app.

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
import html
from urllib.parse import urlencode

from whakerpy.htmlmaker import HTMLNode
from whakerpy.httpd import BaseResponseRecipe

from sppas.core.config import get_language

# ---------------------------------------------------------------------------

# Identifier of the link which leads to the secret name.
REDIRECT_ID = "swapp_redirect"

# What follows the link once the page is loaded: the address WhakerPy wrote
# in it, signed when the secret names are protected.
FOLLOW_SCRIPT = (
    f"const link = document.getElementById('{REDIRECT_ID}');"
    "if (link === null) {"
    "    console.error('The link to the application was not found.');"
    "} else {"
    "    location.replace(link.href);"
    "}"
)

# ---------------------------------------------------------------------------


class swappRedirectResponse(BaseResponseRecipe):
    """The page of an app without a welcome page, when SPPAS is served online.

    It leads at once to a secret name of the app, drawn anew at each request,
    and does nothing else: nothing of the app is done at its default page.
    The page holds a link to the secret name, and a script which follows it:
    WhakerPy signs the address of a link, where the secret names are
    protected, and the script goes where it was signed. Without a script,
    the link is there to be followed.

    What the reader chose to be shown with -- the parameters whose name starts
    with "wexa_" -- is carried to the secret name; nothing else is.

    """

    def __init__(self, app_name: str, secret_page) -> None:
        """Create the page leading to a secret name of an app.

        :param app_name: (str) The name of the app, written in the page
        :param secret_page: (callable) What draws a secret name of the app

        """
        self.__app_name = app_name
        self.__secret_page = secret_page
        self.__parameters = list()
        super(swappRedirectResponse, self).__init__(name="swapp_redirect")

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed content: the language, the title and what leads on."""
        self._htree.add_html_attribute("lang", get_language().split('_')[0])
        self._htree.head.meta({"charset": "utf-8"})
        self._htree.head.append_child(HTMLNode(self._htree.head.identifier, "title", "title",
                                               value=html.escape(self.__app_name)))
        self._htree.body_script.set_value(FOLLOW_SCRIPT)

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Keep what the reader chose to be shown with.

        :param events: (dict) The requested events
        :return: (bool) True: a secret name is drawn at each request

        """
        self.__parameters = list()
        for _name in events:
            if _name.startswith("wexa_") is True:
                self.__parameters.append((_name, events[_name]))
        self._status.code = 200
        return True

    # -----------------------------------------------------------------------

    def _invalidate(self) -> None:
        """Override. Remove the link of the previous request."""
        self._htree.body_main.clear_children()

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Write the link to a secret name drawn for this request."""
        _address = self.__secret_page()
        if len(self.__parameters) > 0:
            _address = _address + "?" + urlencode(self.__parameters)

        # The address is written as it is: WhakerPy reads it in the page to
        # sign it, and an escaped "&" would be read as part of a name. What
        # it carries is already encoded by urlencode().
        _link = HTMLNode(self._htree.body_main.identifier, REDIRECT_ID, "a",
                         value=html.escape(self.__app_name),
                         attributes={"id": REDIRECT_ID, "href": _address})
        self._htree.body_main.append_child(_link)
