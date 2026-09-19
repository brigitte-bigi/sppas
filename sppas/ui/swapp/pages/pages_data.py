"""
:filename: sppas.ui.swapp.pages.pages_data.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The provider of all the generic pages of swapp.

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

from ..swapp_base.swapp_bakery import swappWebData
from ..swapp_core.swapp_page_info import swappWebPageInfo

from .cite_maker import swappCiteResponseRecipe

# ---------------------------------------------------------------------------


class swappPagesData(swappWebData):
    """Serve all the generic pages of swapp.

    A page is a document with its own URL and without business logic: see
    the taxonomy in the README of swapp. This provider is the single one:
    it serves all the pages of the given WEB_PAGES registry, whatever
    their origin -- SPPAS itself or a spin-off. It owns no page list.

    """

    def __init__(self, pages: list, json_filename: str | None = None) -> None:
        """Create a swappPagesData instance.

        :param pages: (list) The swappWebPageInfo of all the pages to serve.

        """
        super(swappPagesData, self).__init__(json_filename)
        self.__pages = list()
        for page_info in pages:
            if isinstance(page_info, swappWebPageInfo) is True:
                self.__pages.append(page_info)
        self._default = swappCiteResponseRecipe.page()

    # -----------------------------------------------------------------------

    def is_page(self, page_name: str) -> bool:
        """Override. Return true if the given page name can be baked.

        :param page_name: The name of the page to check.
        :return: (bool) True if the given page name can be baked.

        """
        for page_info in self.__pages:
            if page_name == page_info.recipe.page():
                return True
        return False

    # -----------------------------------------------------------------------

    def bake_response(self, page_name: str, default: str = "") -> BaseResponseRecipe | None:
        """Return the bakery system to create the requested page dynamically.

        :param page_name: (str) Name of the page to bake.
        :param default: (str) Default value for the page name if the page does not exist.
        :return: (BaseResponseRecipe|None)

        """
        logging.info(f"Requested page name: {page_name}")

        for page_info in self.__pages:
            if page_name == page_info.recipe.page():
                return page_info.recipe()

        # Any other page name
        return None
