"""
:filename: sppas.ui.swapp.app_convert.app_convert.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The web data of the Convert application.

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
from sppas.ui.swapp import swappImagesAccess

from ..swapp_base.swapp_bakery import swappWebData
from ..pages import swappHelpResponseRecipe

from .convert_maker import swappConvertResponseRecipe

# ---------------------------------------------------------------------------

MSG_NAME = _("Convert")
MSG_DESCR = _("Writes annotated files into another format, and says what each format holds.")
MSG_HELP_TITLE = f"SPPAS {sg.__release__} » " + _("Convert") + " » " + _("Help")

# ---------------------------------------------------------------------------


class swappConvertWebData(swappWebData):
    """Parse the JSON file, store data and create the bakery system.

    """

    def __init__(self, json_filename: str | None = None) -> None:
        """Create a swappConvertWebData instance.

        :param json_filename: (str|None) Path of the JSON file to parse, or None

        """
        super(swappConvertWebData, self).__init__(json_filename)
        # Filename of the default page. The only one of the Convert application.
        self._default = swappConvertResponseRecipe.page()

    # -----------------------------------------------------------------------

    @staticmethod
    def id() -> str:
        """Override. Return an identifier of the application."""
        return "Convert"

    # -----------------------------------------------------------------------

    @staticmethod
    def name() -> str:
        """Override. Return a short name of the application."""
        return MSG_NAME

    # -----------------------------------------------------------------------

    @staticmethod
    def description() -> str:
        """Override. Return a short description of the application."""
        return MSG_DESCR

    # -----------------------------------------------------------------------

    @staticmethod
    def icon() -> str:
        """Return the page icon name."""
        return swappImagesAccess.get_image_filename("app_convert")

    # -----------------------------------------------------------------------

    def is_page(self, page_name: str) -> bool:
        """Override. Return true if the given page name can be baked.

        :param page_name: The name of the page to check.
        :return: (bool) True if the given page name can be baked.

        """
        return page_name in (swappConvertResponseRecipe.page(),
                             swappConvertResponseRecipe.help_page())

    # -----------------------------------------------------------------------

    def bake_response(self, page_name: str, default: str = "") -> BaseResponseRecipe | None:
        """Return the bakery system to create the requested page dynamically.

        :param page_name: (str) Name of the page to bake.
        :param default: (str) Default value for the page name if the page does not exist.
        :return: (BaseResponseRecipe|None)

        """
        logging.info(f"Requested page name: {page_name}")
        if page_name == swappConvertResponseRecipe.page():
            return swappConvertResponseRecipe()

        if page_name == swappConvertResponseRecipe.help_page():
            return swappHelpResponseRecipe(swappConvertResponseRecipe.help_document(),
                                           swappConvertResponseRecipe.help_page(),
                                           MSG_HELP_TITLE,
                                           "app_convert.css")

        return None
