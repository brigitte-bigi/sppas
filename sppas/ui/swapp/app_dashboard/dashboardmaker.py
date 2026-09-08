# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_dashboard.dashboardmaker.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: The web page of the "Dashboard" interface.

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

from ..wappbase.wappresponse import swappBaseResponse
from ..wappcore.wappinfo import WebApplicationInfo
from ..wappcore.wappsg import wapp_settings
from ..wappcore.wappsg import wapp_wkps
from ..wappcore.wappsg import wapp_wxstate
from ..wappcore.wappsg import wapp_trace
from ..nodes.feedback.hstatusnode import HTMLTreeError410

from .dashboard_view import DashboardView
from .dashboard_model import DashboardModel
from .dashboard_controller import DashboardController

# ---------------------------------------------------------------------------


MSG_TITLE = f"SPPAS {sg.__release__} Dashboard"

# -----------------------------------------------------------------------


class DashboardResponseRecipe(swappBaseResponse):
    """The sppas_dashboard.html HTTPD response bakery.

    Allows to launch a web application and the SPPAS wx app.
    Also includes useful links to get help, etc.

    """

    def __init__(self, name: str = "Dashboard",
                 tree: HTMLTree | None = None,
                 title: str = MSG_TITLE):
        """Create the ResponseRecipe for the Dashboard application.

        """
        self.__model = DashboardModel()
        self.__view = None
        self.__controller = None

        super(DashboardResponseRecipe, self).__init__(name, tree, title)

    # -----------------------------------------------------------------------
    # PUBLIC METHODS
    # -----------------------------------------------------------------------

    def add_app(self, application: WebApplicationInfo) -> bool:
        """Add an application into the dashboard.

        :param application: (WebApplicationInfo) The application to add.
        :return: (bool) True if the app was added, False otherwise.

        """
        return self.__controller.append_app(application)
        # All the reasons not to add the app:
        # bad instance, invisible app, already defined, invalid res

    # -----------------------------------------------------------------------

    def add_apps(self, applications: list) -> None:
        """Add a list of applications.

        :param applications: (list) The list of applications of type WebApplicationInfo.

        """
        self.__controller.append_apps(applications)

    # -----------------------------------------------------------------------

    def add_pages(self, pages: list) -> None:
        """Add a list of pages into the dashboard.

        :param pages: (list) The list of pages of type WebPageInfo.

        """
        self.__controller.append_pages(pages)

    # -----------------------------------------------------------------------
    # OVERRIDE METHODS FROM Whakerpy -- Create une UI
    # -----------------------------------------------------------------------

    @classmethod
    def help_page(cls) -> str:
        """Return the name of the page serving the document of this app."""
        return "app_dashboard.html"

    # -----------------------------------------------------------------------

    @classmethod
    def help_document(cls) -> str:
        """Return the path of the document of this app, relative to swapp."""
        return "app_dashboard/app_dashboard.htm"

    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return wapp_settings.default_page()

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the nodes that can't be invalidated
        by _bake(): head, body_header, body_nav, body_footer, body_script.

        """
        super().create()
        # self.enable_components(['Dialog'])
        self.__view = DashboardView(self._htree)
        self.__controller = DashboardController(self.__model, self.__view)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f" >>>>> Page Application Dashboard -- Process events: {events} <<<<<< ")
        self._data = dict()
        self._status.code = 200

        # The periodic request of the JS: the displayed workspace name and
        # the Journal dialog are updated without reloading the page. No
        # re-bake. See populate_view() for the source of the displayed name.
        if "workspace_name" in events:
            wkp_name = wapp_wxstate.workspace_name
            wkp_path = ""
            if len(wkp_name) == 0:
                wkp_name = wapp_wkps.get_wkp_name()
                try:
                    wkp_path = wapp_wkps.get_wkp_filename()
                except Exception:
                    wkp_path = ""
            self._data["workspace_name"] = wkp_name
            self._data["workspace_path"] = wkp_path
            self._data["trace_alive"] = wapp_trace.viewer_alive()
            return False

        # Received events from an HTTP Post.
        if "event_bake" in events:
            e = events["event_bake"]

            # --- Action events to got out ---
            if e == "close":
                self._status.code = 410

            # --- Information event of license agreed ---
            elif e == 'handle_licence_agreement':
                return self.__controller.handle_licence_agreement()

            # --- Information SPPAS app has to be launched ---
            elif e == 'handle_start_sppas':
                error = self.__controller.handle_start_sppas()
                if len(error) > 0:
                    self._data["error"] = str(error)
                    self._status.code = 401
                else:
                    self._data["launched"] = True
                    self._status.code = 200
                return False

            else:
                logging.error(f"Unknown event_bake={e}")
                self._status.code = 205  # Reset Content

        elif len(events) > 0:
            logging.error(f"Unknown events={events}")
            self._status.code = 205  # Reset Content

        return True

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Create the dynamic page content in HTML.

        It replaces the current HTMLTree if status is 410 or update the
        content of the current HTMLTree.

        """
        # Define this page content: a form with a header, apps and links.
        self.comment("Body content")
        self.__view.update_accessibility()

        if self._status.code == 410:
            # The 410 is "Gone" response sent when the requested content has been
            # permanently deleted from server, with no forwarding address.
            self._htree = HTMLTreeError410()

        elif self._status.code in (200, 205):
            # Fill-in the body_main node depending on the actual state of the model
            self.__controller.populate_view()

        else:
            msg = f"Unexpected status '{self._status.code}' while baking the page content."
            logging.error(msg)
            p = self._htree.element("p")
            p.set_value(msg)
