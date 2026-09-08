# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_dashboard.dashboard_controller.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Manages the application logic.

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
import sys
import os

from sppas.core.config import sppasExecProcess
from sppas.core.config import cfg
from sppas.core.config import paths
from sppas.core.preinstall.installer import quote
from sppas.ui.swapp.wappcore.wappsg import wapp_settings
from sppas.ui.swapp.wappcore.wappsg import wapp_trace
from sppas.ui.swapp.wappcore.wappsg import wapp_wkps
from sppas.ui.swapp.wappcore.wappsg import wapp_wxstate
from sppas.ui.swapp.wappcore.wappsg import wx_is_running

# ---------------------------------------------------------------------------


class DashboardController:
    """Controller for the SPPAS Dashboard application.

    This class represents the *Controller* component in the MVC pattern.
    It coordinates interactions between the model (list of applications)
    and the view (HTML representation). It also maintains internal state,
    such as whether the user has accepted the licence agreement.

    """

    def __init__(self, model, view):
        """Initialize the controller with a model and a view.

        :param model: (DashboardModel) The model managing the applications.
        :param view: (DashboardView) The view managing the HTML structure.

        """
        self.__model = model
        self.__view = view
        # True while the wx interface is running: only one instance is allowed.
        self.__wx_running = False

    # -----------------------------------------------------------------------

    def has_agreed(self) -> bool:
        """Return the licence agreement state.

        :return: (bool) True if the licence agreement is accepted, False otherwise.

        """
        return wapp_settings.license_agreement

    # -----------------------------------------------------------------------

    def append_app(self, app) -> None:
        """Append a single web application to the model.

        :param app: (WebApplicationInfo) The application descriptor to append.

        """
        self.__model.append(app)

    # -----------------------------------------------------------------------

    def append_apps(self, apps: list) -> None:
        """Append a list of web applications to the model.

        :param apps: (list) List of WebApplicationInfo objects to append.

        """
        self.__model.append_all(apps)

    # -----------------------------------------------------------------------

    def append_pages(self, pages: list) -> None:
        """Append a list of web pages to the model.

        :param pages: (list) List of WebPageInfo objects.

        """
        self.__model.append_pages(pages)

    # -----------------------------------------------------------------------

    def handle_licence_agreement(self) -> bool:
        """Process the licence agreement acceptance.

        This method updates the internal agreement state and logs the event.
        :return: (bool) True if the page has to be refreshed.

        """
        wapp_settings.license_agreement = True
        logging.info("Licence agreement is satisfied.")
        return False

    # -----------------------------------------------------------------------

    def handle_start_sppas(self) -> str:
        """Launch the classic SPPAS wx interface.

        This method executes the main entry point of the wx application
        as a subprocess. It uses the same Python interpreter as the server.
        Only one instance is allowed: the method blocks the running state
        until the subprocess ends, whatever the exit path.

        :return: (str) Error message if any.

        """
        # Only the answer of the interface can forbid a new launch: the
        # flag of the subprocess belongs to the request which launched it,
        # and that request may never come back -- a killed process leaves
        # its blocking call waiting.
        if wx_is_running() is True:
            logging.warning("SPPAS wx interface is already running.")
            return "SPPAS is already running."

        program = paths.ui + os.sep + os.path.join("wxapp", "__main__.py")
        command = quote(sys.executable) + " " + quote(program)
        pyprocess = sppasExecProcess()
        self.__wx_running = True
        try:
            # IMPORTANT: timeout=None means NO timeout.
            pyprocess.run(command, timeout=None)
            pyprocess.out()
        except Exception as e:
            logging.error(str(e))
            return str(e)
        finally:
            self.__wx_running = False
            # The process this dashboard launched is over, whatever the exit
            # path: a crash sends no BYE, so the shared state would keep
            # saying that wx is running and the launch button would stay
            # disabled until the web server itself is restarted.
            wapp_wxstate.running = False

        return ""

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Populate the dashboard view with data from the model.

        The method instructs the view to create the page content according
        to the model data and the current agreement state. Only the Launch
        button of the wx card is disabled while the wx interface is
        running: only one instance is allowed, and the rest of the card
        stays exactly as it was right after the click that launched it.

        """
        wx_enabled = cfg.feature_installed("wxpython")
        # Two sources are needed: the subprocess flag covers the launches of
        # this dashboard, including the delay before the HELLO of wx arrives;
        # the socket state covers a wx launched elsewhere, and its Close.
        # The interface is asked directly: a user in front of the button
        # does not wait for the periodic sign of life to fade away.
        wx_busy = self.__wx_running is True or wx_is_running() is True
        logging.debug(f"Dashboard wx card state: feature={wx_enabled}, "
                      f"subprocess_running={self.__wx_running}, "
                      f"socket_running={wapp_wxstate.running}")
        # The Journal tab sends a heartbeat: absent, the view bakes the
        # dialog inviting the user to open it.
        trace_alive = wapp_trace.viewer_alive()

        # The current workspace. The wx interlocutor, when connected, is
        # the source of truth: its WKP_CHANGED messages report the name of
        # its current workspace, not an identifier -- swapp does not try
        # to resolve it against its own local workspace list. Before any
        # wx connected, the local state is displayed instead.
        wkp_name = wapp_wxstate.workspace_name
        wkp_path = ""
        if len(wkp_name) == 0:
            wkp_name = wapp_wkps.get_wkp_name()
            try:
                wkp_path = wapp_wkps.get_wkp_filename()
            except Exception:
                wkp_path = ""

        self.__view.populate_tree_content(wapp_settings.license_agreement,
                                          wx_enabled, wx_busy, trace_alive,
                                          wkp_name, wkp_path)

        for app_name in self.__model.get_names(visible_only=True):
            app_info = self.__model.get_bakery_by_name(app_name)
            if app_info is None:
                continue
            try:
                bakery = app_info.bakery()
                enabled = True
                if hasattr(bakery, 'get_fids') is True:
                    fids = bakery.get_fids() or []
                    # All requested features must be enabled
                    enabled = all(cfg.feature_installed(item) for item in fids)
                self.__view.append_app_card(
                    app_name,
                    bakery.name(),
                    bakery.icon(),
                    bakery.description(),
                    bakery.get_default_page(),
                    enabled,
                    theme_name=bakery.theme_name()
                )
            except Exception as e:
                logging.error(f"Failed to create app card for {app_name}: {str(e)}")

            # list of devel apps section:
            # h2 = HTMLNode(self._htree.body_main.identifier, None, "h2", value=MSG_APPS_DEVEL)
            # self._htree.body_main.append_child(h2)
            # ln = AppsNode(self._htree.body_main.identifier)
            # self._htree.body_main.append_child(ln)

        for recipe in self.__model.get_page_recipes():
            try:
                self.__view.append_page_link(recipe.name(), recipe.icon(), recipe.page())
            except Exception as e:
                logging.error(f"Failed to create page link for {recipe}: {str(e)}")
