"""
:filename: sppas.ui.swapp.swapp_core.swapp_dispatcher.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: This is the dispatcher of the apps and the pages of swapp.

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

    Copyright (C) 2011-2026 Brigitte Bigi
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

from whakerpy.httpd import BaseResponseRecipe

from sppas.core.coreutils import sppasKeyError
from sppas.core.coreutils import sppasEnableFeatureError

from ..pages import swappNotFoundResponseRecipe
from ..pages import swappPagesData
from .swapps import WEB_APPLICATIONS
from .swapps import WEB_PAGES

# ---------------------------------------------------------------------------


class swappDispatcher:
    """Serve the response of any app or page of swapp.

    The two registries of swapps.py are the only source of what swapp serves.
    A requested page is asked to the apps first, in the order of the
    WEB_APPLICATIONS registry, then to the single provider of the generic
    pages. The dispatcher is shared by the local HTTPD server and by the WSGI
    service, so that the very same response is served by both of them.

    """

    # Name of the application which is the entry point of swapp.
    DEFAULT_APP_NAME = "Dashboard"

    def __init__(self, app_name: str = "Dashboard") -> None:
        """Create a swappDispatcher instance.

        :param app_name: (str) One of the WEB_APPLICATIONS app name
        :raises: sppasKeyError: The given name is not a declared web application

        """
        self.__app = None
        names = list()
        for web_app in WEB_APPLICATIONS:
            names.append(web_app.name)
            if web_app.name == app_name:
                self.__app = web_app

        if self.__app is None:
            raise sppasKeyError(names, app_name)

        # The single provider of the generic pages, asked after the apps.
        self.__pages = swappPagesData(WEB_PAGES)

    # -----------------------------------------------------------------------

    def get_default_page(self) -> str:
        """Return the name of the default page of the served app.

        :return: (str) Name of the page the served app is entered by

        """
        bakery = self.__app.bakery()
        return bakery.get_default_page()

    # -----------------------------------------------------------------------

    def is_page(self, page_name: str) -> bool:
        """Return true if the given page name can be baked.

        :param page_name: (str) Name of the page to check
        :return: (bool) True if an app or the provider of the pages bakes it

        """
        if self.__bakery_of(page_name) is not None:
            return True

        return self.__pages.is_page(page_name)

    # -----------------------------------------------------------------------

    def bake_response(self, page_name: str, default: str = "") -> BaseResponseRecipe:
        """Return the bakery system to create the requested page dynamically.

        A name neither an app nor a page bakes is answered by the "Page not
        found" page of swapp, which carries the 404 status. Both servers are
        then answering the very same page, translated and themed like any
        other one.

        :param page_name: (str) Name of the page to bake
        :param default: (str) Default value for the page name if the page does not exist
        :return: (BaseResponseRecipe)

        """
        bakery = self.__bakery_of(page_name)
        if bakery is not None:
            response = bakery.bake_response(page_name, default)
            if self.__is_dashboard_default(page_name, bakery) is True:
                self.__add_dashboard_links(response)
            return response

        if self.__pages.is_page(page_name) is True:
            return self.__pages.bake_response(page_name, default)

        return swappNotFoundResponseRecipe()

    # -----------------------------------------------------------------------

    def create_pages(self) -> dict:
        """Return the baked responses the server starts with.

        The served app is the entry point. When it is the one swapp is entered
        by, all the other apps are baked too, and not only the ones the UI is
        showing: each of them is then reachable by its own URL, as a known web
        app.

        :return: (dict) key=page name, value=BaseResponseRecipe

        """
        responses = dict()
        page = self.get_default_page()
        responses[page] = self.bake_response(page)

        if self.__app.name != swappDispatcher.DEFAULT_APP_NAME:
            return responses

        for web_app in WEB_APPLICATIONS:
            if web_app.name == self.__app.name:
                continue
            try:
                bakery = web_app.bakery()
            except sppasEnableFeatureError as e:
                logging.info(f"Application {web_app.name} disabled: {e}.")
            else:
                other_page = bakery.get_default_page()
                responses[other_page] = bakery.bake_response(other_page)

        return responses

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __bakery_of(self, page_name: str):
        """Return the bakery of the app which bakes the given page name.

        A disabled app bakes nothing: its feature is not enabled, and the
        requested page is left to the next app of the registry.

        :param page_name: (str) Name of the page to bake
        :return: (swappWebData|None) None if no app bakes this page name

        """
        for web_app in WEB_APPLICATIONS:
            try:
                bakery = web_app.bakery()
            except sppasEnableFeatureError as e:
                logging.info(f"Application {web_app.name} disabled: {e}.")
            else:
                if bakery.is_page(page_name) is True:
                    return bakery

        return None

    # -----------------------------------------------------------------------

    def __is_dashboard_default(self, page_name: str, bakery) -> bool:
        """Return true if the given page name is the one of the Dashboard.

        The help page of the Dashboard is baked by the same bakery and it
        shows no card: only the page swapp is entered by is concerned.

        :param page_name: (str) Name of the baked page
        :param bakery: (swappWebData) The bakery which baked the page
        :return: (bool)

        """
        if bakery.get_default_page() != page_name:
            return False

        for web_app in WEB_APPLICATIONS:
            if web_app.name == swappDispatcher.DEFAULT_APP_NAME:
                return isinstance(bakery, web_app.bakery) is True

        return False

    # -----------------------------------------------------------------------

    def __add_dashboard_links(self, response) -> None:
        """Add the apps and the pages the Dashboard gives access to.

        Adding all the other applications to the dashboard response allows
        their cards to be displayed in the interface. Adding the page
        providers allows the link buttons of their pages to be displayed.

        :param response: (BaseResponseRecipe) The baked response of the Dashboard

        """
        apps = list()
        for web_app in WEB_APPLICATIONS:
            if web_app.name != swappDispatcher.DEFAULT_APP_NAME:
                apps.append(web_app)

        response.add_apps(apps)
        response.add_pages(WEB_PAGES)
