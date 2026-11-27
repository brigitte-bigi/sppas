"""
:filename: sppas.ui.swapp.swapp_base.swapp_bakery.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Bakery for any SPPAS web-based application.

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
import secrets

from whakerpy.webapp import WebSiteData
from sppas.ui.swapp import swappImagesAccess

from ..swapp_core.swappsg import swapp_settings
from .swapp_redirect import swappRedirectResponse

# ---------------------------------------------------------------------------

# Online, an application is reached at its default page followed by this
# separator and a secret: as many bytes drawn at random, written in hexadecimal.
SECRET_SEPARATOR = "_"
SECRET_BYTES = 16

# ---------------------------------------------------------------------------


class swappWebData(WebSiteData):
    """Parse the JSON file, store data and create the bakery system.

    """

    def __init__(self, json_filename: str | None = None):
        """Create a swappWebData instance.

        """
        super(swappWebData, self).__init__(json_filename)

    # -----------------------------------------------------------------------

    @staticmethod
    def icon() -> str:
        """Return the page icon name."""
        return swappImagesAccess.get_logo_filename("sppas-logo-v5")

    @staticmethod
    def description() -> str:
        """Return a short description of the application."""
        return "No description available."

    @staticmethod
    def name() -> str:
        """Return a short name of the application."""
        return "Undefined"

    @staticmethod
    def id() -> str:
        """Return an identifier of the application."""
        return "Undefined"

    @staticmethod
    def local_only() -> bool:
        """Return True if the application is served by a local server only.

        An application says it itself, and it says it once: what it does
        decides, not what happens to be installed where it is served. One
        which installs packages on the machine, or opens a window on it,
        is of the machine of its reader and not of a service a crowd
        reaches. Its card is still shown, and disabled, so that a reader
        of the web service sees what SPPAS holds.

        """
        return False

    @staticmethod
    def theme_name() -> str:
        """Return the name of the theme the application brings, if any.

        An application bringing its own theme is shown with it, whatever
        the theme in force where it was launched from: the theme is its
        identity. An empty name means the application takes the theme of
        the page it was launched from.

        """
        return ""

    # -----------------------------------------------------------------------
    # Online, what an application does is reached at a secret name
    # -----------------------------------------------------------------------

    def _is_app_page(self, page_name: str) -> bool:
        """Return True if the given name is a page of the application.

        :param page_name: (str) Name of the requested page
        :return: (bool) The default page; online, a secret name of it as well

        """
        if page_name == self.get_default_page():
            return True
        if swapp_settings.served_locally is True or self.__is_protected() is False:
            return False

        return self.__is_secret_page(page_name)

    # -----------------------------------------------------------------------

    def _is_welcome_page(self, page_name: str) -> bool:
        """Return True if the given name is the welcome page of the application.

        Online, the default page is the welcome page, and what the application
        does is reached at a secret name only. Locally, and for an application
        in development, there is no welcome page: the default page is the
        application.

        :param page_name: (str) Name of the requested page
        :return: (bool)

        """
        if swapp_settings.served_locally is True or self.__is_protected() is False:
            return False

        return page_name == self.get_default_page()

    # -----------------------------------------------------------------------

    def _welcome_response(self):
        """Return what answers the welcome page of the application.

        An application with a welcome page of its own -- what it does, and in
        which context -- overrides it. Without one, the page leads at once to
        a secret name of the application.

        :return: (BaseResponseRecipe)

        """
        return swappRedirectResponse(self.name(), self._secret_page)

    # -----------------------------------------------------------------------

    def _secret_page(self) -> str:
        """Return a secret name the application is reached at online.

        A reader reaches it from the welcome page; whoever knows the default
        page only never reaches what the application does.

        :return: (str) The default page followed by a secret drawn at random

        """
        return self.__stem() + SECRET_SEPARATOR + secrets.token_hex(SECRET_BYTES) + ".html"

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __is_protected(self) -> bool:
        """Return True if the application is reached at a secret name online.

        Every application is, but the ones in development: the list of the
        applications declares them with "show" set to False.

        :return: (bool)

        """
        # The list imports every application, and this module with them: it
        # is read when it is asked for, and not when this module is imported.
        from ..swapp_core.swapps import WEB_APPLICATIONS

        for _web_app in WEB_APPLICATIONS:
            if _web_app.bakery is type(self):
                return _web_app.show

        return True

    # -----------------------------------------------------------------------

    def __is_secret_page(self, page_name: str) -> bool:
        """Return True if the given name is a secret name of the application.

        :param page_name: (str) Name of the requested page
        :return: (bool)

        """
        _prefix = self.__stem() + SECRET_SEPARATOR
        if page_name.startswith(_prefix) is False or page_name.endswith(".html") is False:
            return False

        _secret = page_name[len(_prefix):len(page_name) - len(".html")]
        if len(_secret) != 2 * SECRET_BYTES:
            return False
        for _character in _secret:
            if _character not in "0123456789abcdef":
                return False

        return True

    # -----------------------------------------------------------------------

    def __stem(self) -> str:
        """Return the name of the default page, without its extension."""
        return os.path.splitext(self.get_default_page())[0]
