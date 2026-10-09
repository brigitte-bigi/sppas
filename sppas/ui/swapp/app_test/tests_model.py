# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_test.tests_model.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The tests this app knows, and the page each one is on.

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


"""

from .tests_page_swapp import swappTestSwappResponseRecipe
from .tests_page_files import swappTestFilesResponseRecipe

# ---------------------------------------------------------------------------


class swappTestsModel:
    """Represent the tests this app serves.

    A test is a page, and it describes itself: its name, what it is for, and
    the page it is on. Adding a test is adding it to the list below, and
    nothing else of this app is touched.

    """

    def __init__(self):
        """Create the model with the tests this app knows."""
        self.__recipes = [swappTestSwappResponseRecipe,
                          swappTestFilesResponseRecipe]

    # -----------------------------------------------------------------------

    def tests(self) -> list:
        """Return the recipe of every test, in the order they are declared.

        :return: (list) The classes which bake the pages of the tests

        """
        return self.__recipes

    # -----------------------------------------------------------------------

    def is_page(self, page_name: str) -> bool:
        """Return True if one of the tests is on the given page.

        :param page_name: (str) Name of a page
        :return: (bool)

        """
        return self.recipe_of(page_name) is not None

    # -----------------------------------------------------------------------

    def recipe_of(self, page_name: str):
        """Return what bakes the given page.

        :param page_name: (str) Name of a page
        :return: (class) None if no test is on that page

        """
        for _recipe in self.__recipes:
            if _recipe.page() == page_name:
                return _recipe

        return None

    # -----------------------------------------------------------------------

    def links(self) -> list:
        """Return the identifiers of the buttons which lead to the tests.

        :return: (list of str)

        """
        _links = list()
        for _recipe in self.__recipes:
            _links.append(swappTestsModel.button_of(_recipe))

        return _links

    # -----------------------------------------------------------------------

    @staticmethod
    def button_of(recipe) -> str:
        """Return the identifier of the button which leads to a test.

        :param recipe: (class) What bakes the page of the test
        :return: (str)

        """
        return recipe.page().replace(".html", "") + "_button"
