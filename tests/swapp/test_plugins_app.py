# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_plugins_app.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the shell of the Plugins application.

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

    The app is one of the apps of swapp, and its page shows nothing yet but
    its nav. Its help is tested with the help of every app.

"""

import unittest

from sppas.ui.swapp.swapp_core.swapps import WEB_APPLICATIONS
from sppas.ui.swapp.app_plugins import swappPluginsWebData
from sppas.ui.swapp.app_plugins import swappPluginsResponseRecipe

from tests.swapp.page_requests import main_of

# ---------------------------------------------------------------------------


class TestPluginsApp(unittest.TestCase):
    """The shell of the Plugins application."""

    def test_it_is_in_the_list_of_the_apps(self):
        """The app is declared, shown, and it answers its page."""
        declared = list()
        for app in WEB_APPLICATIONS:
            if app.name == "Plugins":
                declared.append(app)
        self.assertEqual(1, len(declared))
        self.assertIs(swappPluginsWebData, declared[0].bakery)
        self.assertTrue(declared[0].show)

        data = swappPluginsWebData()
        self.assertTrue(data.is_page("plugins.html"))
        self.assertIsInstance(data.bake_response("plugins.html"), swappPluginsResponseRecipe)
        self.assertIsNone(data.bake_response("annotate.html"))

    # -----------------------------------------------------------------------

    def test_the_page_shows_nothing_yet(self):
        """The main content of the page is empty, whatever the request."""
        recipe = swappPluginsResponseRecipe()
        self.assertEqual("", main_of(recipe.bake({})).strip())
        self.assertEqual("", main_of(recipe.bake({"event_bake": "anything"})).strip())


if __name__ == "__main__":
    unittest.main()
