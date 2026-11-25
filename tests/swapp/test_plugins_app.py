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

    The app is one of the apps of swapp, and its page shows the plugins
    which are installed. Its help is tested with the help of every app. The
    plugins are installed for the tests, in a folder of their own.

"""

import json
import os
import re
import shutil
import tempfile
import unittest
from unittest import mock

import sppas.src.plugins.manager

from sppas.ui.swapp.swapp_core.swappsg import swapp_serverstate
from sppas.ui.swapp.swapp_core.swapps import WEB_APPLICATIONS
from sppas.ui.swapp.app_plugins import swappPluginsWebData
from sppas.ui.swapp.app_plugins import swappPluginsResponseRecipe

from tests.swapp.page_requests import main_of

# ---------------------------------------------------------------------------


class PathsForTests:
    """The paths of SPPAS, where the folder of the plugins is the one of a test."""

    plugins = ""

# ---------------------------------------------------------------------------


def install_for_tests(folder: str, identifier: str, name: str, descr: str, icon: str) -> None:
    """Write a plugin in the folder of the plugins of a test: its folder and its configuration.

    Its command is the interpreter which runs the tests, on every system.

    """
    _plugin = os.path.join(folder, identifier)
    os.mkdir(_plugin)
    _config = {"id": identifier, "name": name, "descr": descr, "icon": icon,
               "commands": {"windows": "$PY", "macos": "$PY", "linux": "$PY"},
               "options": []}
    with open(os.path.join(_plugin, identifier + ".json"), "w", encoding="utf-8") as fp:
        json.dump(_config, fp)

# ---------------------------------------------------------------------------


def cards_of(page: str) -> list:
    """Return the cards of the plugins of a page."""
    return re.findall(r'<li class="card app">(.*?)</li>', page, re.S)

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

    def test_te20_installing_and_deleting_in_the_menu(self):
        """TE20. On the machine of the person, the menu carries installing and deleting; on a server, neither. [025], RO1"""
        with mock.patch.object(swapp_serverstate, "local", True):
            page = swappPluginsResponseRecipe().bake({})
        nav = page[page.find("<nav"):page.find("</nav>")]
        self.assertIn('id="plugins_install"', nav)
        self.assertIn('id="plugins_delete"', nav)

        with mock.patch.object(swapp_serverstate, "local", False):
            page = swappPluginsResponseRecipe().bake({})
        nav = page[page.find("<nav"):page.find("</nav>")]
        self.assertNotIn('id="plugins_install"', nav)
        self.assertNotIn('id="plugins_delete"', nav)

# ---------------------------------------------------------------------------


class TestInstalledPlugins(unittest.TestCase):
    """TE1, TE2. The plugins which are installed, as the page shows them."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_plugins_app_")
        PathsForTests.plugins = self.folder
        self.paths = mock.patch.object(sppas.src.plugins.manager, "paths", PathsForTests)
        self.paths.start()

    def tearDown(self):
        self.paths.stop()
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te1_every_plugin_which_is_installed(self):
        """TE1. Every plugin the domain of the plugins holds is given, and no other. [011]"""
        page = swappPluginsResponseRecipe().bake({})
        self.assertEqual(0, len(cards_of(main_of(page))))

        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "")
        install_for_tests(self.folder, "markers", "Markers", "Adds a tier of markers.", "")
        page = swappPluginsResponseRecipe().bake({})
        cards = cards_of(main_of(page))
        self.assertEqual(2, len(cards))
        names = list()
        for card in cards:
            names.append(re.search(r'<h2 class="app-title">\s*(.*?)\s*</h2>', card, re.S).group(1))
        self.assertEqual(["Hello", "Markers"], sorted(names))

    # -----------------------------------------------------------------------

    def test_te2_what_a_plugin_declares_of_itself(self):
        """TE2. What is given of a plugin is what it declares: its name, what it says of itself, its icon. [012], [013]"""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "hello.png")
        install_for_tests(self.folder, "markers", "Markers", "Adds a tier of markers.", "")
        page = swappPluginsResponseRecipe().bake({})
        cards = dict()
        for card in cards_of(main_of(page)):
            name = re.search(r'<h2 class="app-title">\s*(.*?)\s*</h2>', card, re.S).group(1)
            cards[name] = card

        self.assertIn("Writes a file of greetings.", cards["Hello"])
        self.assertIsNotNone(re.search(r'<button type="button" class="action-button app-button">\s*hello\s*</button>',
                                       cards["Hello"]))
        icon = re.search(r'<img [^>]*src="([^"]*)"', cards["Hello"]).group(1)
        self.assertEqual(os.path.relpath(os.path.join(self.folder, "hello", "hello.png")), icon)
        self.assertIn("Adds a tier of markers.", cards["Markers"])
        self.assertNotIn("<img", cards["Markers"])

    # -----------------------------------------------------------------------

    def test_the_about_of_a_plugin(self):
        """Each card holds the dialog of its About, which its button opens: the name, the icon and the README."""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "hello.png")
        install_for_tests(self.folder, "markers", "Markers", "Adds a tier of markers.", "")
        with open(os.path.join(self.folder, "hello", "README.txt"), "w") as fp:
            fp.write("<b>Hello</b> & more")

        page = main_of(swappPluginsResponseRecipe().bake({}))
        abouts = re.findall(r'<button [^>]*aria-haspopup="dialog" aria-controls="([^"]*)">', page)
        self.assertEqual(["plugin_about_hello", "plugin_about_markers"], sorted(abouts))

        hello = re.search(r'<dialog id="plugin_about_hello"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIsNotNone(re.search(r'<h4 id="plugin_about_hello_h">\s*About hello...\s*</h4>', hello))
        self.assertIn("Hello", hello)
        self.assertIn('src="' + os.path.relpath(os.path.join(self.folder, "hello", "hello.png")) + '"', hello)
        self.assertIn("&lt;b&gt;Hello&lt;/b&gt; &amp; more", hello)

        markers = re.search(r'<dialog id="plugin_about_markers"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIn("Markers", markers)
        self.assertNotIn("<pre", markers)
        self.assertNotIn("<img", markers)

if __name__ == "__main__":
    unittest.main()
