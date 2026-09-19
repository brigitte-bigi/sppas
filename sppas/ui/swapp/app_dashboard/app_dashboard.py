"""
:filename: sppas.ui.swapp.app_dashboard.app_dashboard.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Bakery for the web-based application for tests.

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

from whakerpy.httpd import BaseResponseRecipe

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_bakery import swappWebData
from ..pages import swappHelpResponseRecipe

from .dashboard_maker import swappDashboardResponseRecipe

# ---------------------------------------------------------------------------


MSG_HELP_TITLE = f"SPPAS {sg.__release__} » " + _("Dashboard") + " » " + _("Help")

# ---------------------------------------------------------------------------


class swappDashboardWebData(swappWebData):
    """Parse the JSON file, store data and create the bakery system.

    """

    def __init__(self, json_filename: str | None = None) -> None:
        """Create a swappDashboardWebData instance.

        """
        super(swappDashboardWebData, self).__init__(json_filename)
        # Filename of the default page. The only one of the Dashboard application.
        self._default = swappDashboardResponseRecipe.page()

    # -----------------------------------------------------------------------

    def is_page(self, page_name: str) -> bool:
        """Override. Return true if the given page name can be baked.

        :param page_name: The name of the page to check.
        :return: (bool) True if the given page name can be baked.

        """
        return page_name in (swappDashboardResponseRecipe.page(),
                             swappDashboardResponseRecipe.help_page())

    # -----------------------------------------------------------------------

    def bake_response(self, page_name: str, default: str = "") -> BaseResponseRecipe | None:
        """Return the bakery system to create the requested page dynamically.

        :param page_name: (str) Name of the page to bake.
        :param default: (str) Default value for the page name if the page does not exist.
        :return: (BaseResponseRecipe|None)

        """
        logging.info(f"Requested page name: {page_name}")

        if page_name == swappDashboardResponseRecipe.page():
            return swappDashboardResponseRecipe()

        if page_name == swappDashboardResponseRecipe.help_page():
            return swappHelpResponseRecipe(swappDashboardResponseRecipe.help_document(),
                                      swappDashboardResponseRecipe.help_page(),
                                      MSG_HELP_TITLE,
                                      "app_dashboard.css")

        # Any other page name
        return None
