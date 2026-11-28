"""
:filename: test_swapp_dispatcher.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test what the dispatcher of swapp serves.

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

import unittest
from unittest import mock

from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.swapp_core.swapps import WEB_APPLICATIONS
from sppas.ui.swapp.swapp_core.swapp_dispatcher import swappDispatcher
from sppas.ui.swapp.app_test.app_test import swappTestsWebData
from sppas.ui.swapp.app_test.tests_maker import swappTestsResponseRecipe

# ---------------------------------------------------------------------------


class TestAppInDevelopment(unittest.TestCase):
    """An app the registry declares with show set to False does not work."""

    def setUp(self):
        self.entry = None
        for web_app in WEB_APPLICATIONS:
            if web_app.bakery is swappTestsWebData:
                self.entry = web_app
        self.assertIsNotNone(self.entry)

    def test_not_served_wherever_it_is(self):
        """Locally or online, none of its pages is served, and none is baked at start."""
        for local in (True, False):
            with self.subTest(served_locally=local):
                with mock.patch.object(swapp_settings, "served_locally", local), \
                        mock.patch.object(self.entry, "show", False):
                    dispatcher = swappDispatcher()
                    for page_name in ("test.html", "test_files.html", "test_options.html"):
                        self.assertFalse(dispatcher.is_page(page_name))
                        self.assertNotIsInstance(dispatcher.bake_response(page_name), swappTestsResponseRecipe)
                    self.assertNotIn("test.html", dispatcher.create_pages())

    def test_served_when_shown(self):
        """The same app, declared with show set to True, is served."""
        with mock.patch.object(swapp_settings, "served_locally", True), \
                mock.patch.object(self.entry, "show", True):
            dispatcher = swappDispatcher()
            self.assertTrue(dispatcher.is_page("test.html"))
            self.assertIsInstance(dispatcher.bake_response("test.html"), swappTestsResponseRecipe)


# ---------------------------------------------------------------------------


class TestPageOfTheMachine(unittest.TestCase):
    """The Journal is a page of the machine: a web service does not serve it."""

    def test_the_journal(self):
        """Online, journal.html is not served; locally, it is."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            self.assertFalse(swappDispatcher().is_page("journal.html"))
        with mock.patch.object(swapp_settings, "served_locally", True):
            self.assertTrue(swappDispatcher().is_page("journal.html"))


if __name__ == "__main__":
    unittest.main()
