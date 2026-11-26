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
from tests.swapp.page_requests import swappPageFields

# ---------------------------------------------------------------------------


class PathsForTests:
    """The paths of SPPAS, where the folder of the plugins is the one of a test."""

    plugins = ""

# ---------------------------------------------------------------------------


def install_for_tests(folder: str, identifier: str, name: str, descr: str, icon: str,
                      options: list | None = None) -> None:
    """Write a plugin in the folder of the plugins of a test: its folder and its configuration.

    Its command is the interpreter which runs the tests, on every system.

    """
    if options is None:
        options = list()
    _plugin = os.path.join(folder, identifier)
    os.mkdir(_plugin)
    _config = {"id": identifier, "name": name, "descr": descr, "icon": icon,
               "commands": {"windows": "$PY", "macos": "$PY", "linux": "$PY"},
               "options": options}
    with open(os.path.join(_plugin, identifier + ".json"), "w", encoding="utf-8") as fp:
        json.dump(_config, fp)

# ---------------------------------------------------------------------------


def lines_of(page: str) -> list:
    """Return the lines of the plugins of a page, each one with its dialogs."""
    _list = re.search(r'<ul id="plugins_list">(.*?)</ul>', page, re.S).group(1)
    return re.findall(r'<li>(.*?)</li>', _list, re.S)

# ---------------------------------------------------------------------------


def name_of(line: str) -> str:
    """Return the name of the plugin of a line, the one its switch is labeled with."""
    return re.search(r'<label for="plugins_sel_[^"]*">\s*(.*?)\s*</label>', line, re.S).group(1)

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

    def test_te20_installing_and_deleting_above_the_list(self):
        """TE20. On the machine of the person, the section of the plugins carries installing and deleting above the list; on a server, neither. [025], RO1"""
        with mock.patch.object(swapp_serverstate, "local", True):
            page = main_of(swappPluginsResponseRecipe().bake({}))
        plugins = page[page.find('id="plugins_section"'):page.find('id="plugins_list"')]
        self.assertIn('id="plugins_install"', plugins)
        self.assertIn('id="plugins_delete"', plugins)

        with mock.patch.object(swapp_serverstate, "local", False):
            page = main_of(swappPluginsResponseRecipe().bake({}))
        self.assertNotIn('id="plugins_install"', page)
        self.assertNotIn('id="plugins_delete"', page)

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
        self.assertEqual(0, len(lines_of(main_of(page))))
        # The sections of the page, in their order: no results before a run.
        self.assertEqual(["plugins_files_section", "plugins_section"],
                         re.findall(r'<section id="([^"]*)" class="panel">', main_of(page)))
        # The section of the files holds the container of the provision of files.
        files = main_of(page)[main_of(page).find('id="plugins_files_section"'):main_of(page).find('id="plugins_section"')]
        self.assertIn('id="files_deposit"', files)
        # The section of the plugins ends with what runs them, and what resets the page.
        plugins = main_of(page)[main_of(page).find('id="plugins_section"'):]
        self.assertIn('value="plugins_run"', plugins)
        self.assertIn('value="plugins_reset"', plugins)

        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "")
        install_for_tests(self.folder, "markers", "Markers", "Adds a tier of markers.", "")
        page = swappPluginsResponseRecipe().bake({})
        lines = lines_of(main_of(page))
        self.assertEqual(2, len(lines))
        names = list()
        for line in lines:
            names.append(name_of(line))
        self.assertEqual(["Hello", "Markers"], sorted(names))

    # -----------------------------------------------------------------------

    def test_te2_what_a_plugin_declares_of_itself(self):
        """TE2. What is given of a plugin is what it declares: its name, what it says of itself, its icon. [012], [013]"""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "hello.png")
        install_for_tests(self.folder, "markers", "Markers", "Adds a tier of markers.", "")
        page = swappPluginsResponseRecipe().bake({})
        lines = dict()
        for line in lines_of(main_of(page)):
            lines[name_of(line)] = line

        self.assertIn("Writes a file of greetings.", lines["Hello"])
        self.assertIsNotNone(re.search(r'<button [^>]*value="plugins_options_hello"[^>]*>\s*<span>\s*Configure\.\.\.\s*</span>\s*</button>',
                                       lines["Hello"]))
        icon = re.search(r'<img [^>]*src="([^"]*)"', lines["Hello"]).group(1)
        self.assertEqual(os.path.relpath(os.path.join(self.folder, "hello", "hello.png")), icon)
        self.assertIn("Adds a tier of markers.", lines["Markers"])
        self.assertNotIn("<img", lines["Markers"])

    # -----------------------------------------------------------------------

    def test_the_about_of_a_plugin(self):
        """Each line holds the dialog of its About, which its button opens: the name, the icon and the README."""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "hello.png")
        install_for_tests(self.folder, "markers", "Markers", "Adds a tier of markers.", "")
        with open(os.path.join(self.folder, "hello", "README.txt"), "w") as fp:
            fp.write("<b>Hello</b> & more")

        page = main_of(swappPluginsResponseRecipe().bake({}))
        abouts = re.findall(r'<button [^>]*aria-haspopup="dialog" aria-controls="([^"]*)">', page)
        self.assertEqual(["plugin_about_hello", "plugin_about_markers"], sorted(abouts))
        # Its button stands alone in a column of the line.
        self.assertIsNotNone(re.search(r'<div class="flex-item width_10">\s*<button type="button" aria-haspopup="dialog" '
                                       r'aria-controls="plugin_about_hello">[^<]*</button>\s*</div>', page))

        hello = re.search(r'<dialog id="plugin_about_hello"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIsNotNone(re.search(r'<h4 id="plugin_about_hello_h">\s*About hello...\s*</h4>', hello))
        self.assertIn("Hello", hello)
        self.assertIn('src="' + os.path.relpath(os.path.join(self.folder, "hello", "hello.png")) + '"', hello)
        self.assertIn("&lt;b&gt;Hello&lt;/b&gt; &amp; more", hello)

        markers = re.search(r'<dialog id="plugin_about_markers"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIn("Markers", markers)
        self.assertNotIn("<pre", markers)
        self.assertNotIn("<img", markers)

    # -----------------------------------------------------------------------

    def test_lets_go_is_disabled_while_no_plugin_is_selected(self):
        """What starts the runs is disabled while no plugin is selected, and what says so is shown."""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "")
        recipe = swappPluginsResponseRecipe()
        page = main_of(recipe.bake({}))
        button = re.search(r'<button [^>]*value="plugins_run"[^>]*>', page).group(0)
        self.assertIn(" disabled", button)
        self.assertIn('aria-describedby="plugins_run_state"', button)
        self.assertIsNotNone(re.search(r'<p id="plugins_run_state" class="plugins-missing">', page))

        fields = swappPageFields(page).fields_of("plugins_form")
        fields["plugins_sel_hello"] = "True"
        fields["event_bake"] = "plugins_run"
        page = main_of(recipe.bake(fields))
        button = re.search(r'<button [^>]*value="plugins_run"[^>]*>', page).group(0)
        self.assertNotIn(" disabled", button)
        self.assertNotIn("aria-describedby", button)
        self.assertIsNotNone(re.search(r'<p id="plugins_run_state" class="plugins-missing hidden">', page))

    # -----------------------------------------------------------------------

    def test_te30_applying_and_closing_the_options_of_a_plugin(self):
        """TE30. Applying the options of a plugin validates it and selects it; closing them invalidates it and unselects it. [206], T04"""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "",
                          [{"id": "-o", "type": "str", "value": "-hello", "text": "Output pattern"},
                           {"id": "input", "type": "file", "value": "input", "text": "Input file"}])
        recipe = swappPluginsResponseRecipe()
        page = main_of(recipe.bake({}))

        # Nothing is selected nor applied; the selection is carried by the switch alone.
        fields = swappPageFields(page).fields_of("plugins_form")
        self.assertEqual("False", fields["plugins_applied_hello"])
        self.assertNotIn("plugins_sel_hello", fields)
        self.assertEqual(1, page.count('name="plugins_sel_hello"'))

        # Configure... answers the options of the plugin, but the input one,
        # with what the page writes of that plugin.
        recipe.bake(swappPageFields(page).submitted("event_bake", "plugins_options_hello"))
        container = recipe._data["options"]
        self.assertIn('id="option_-o"', container)
        self.assertNotIn('id="option_input"', container)
        self.assertEqual({"plugins_sel_hello": "False", "plugins_applied_hello": "False",
                          "plugins_opt_hello_-o": "-hello"}, recipe._data["values"])

        # A value is applied while the plugin is not selected: the plugin is
        # validated, and it is selected.
        applied = dict(fields)
        applied.update(swappPageFields(container).fields_of("#form1"))
        applied["option_-o"] = "-greet"
        applied["options_validate"] = ""
        applied["event_bake"] = "plugins_options_hello"
        recipe.bake(applied)
        self.assertEqual({"plugins_sel_hello": "True", "plugins_applied_hello": "True",
                          "plugins_opt_hello_-o": "-greet"}, recipe._data["values"])

        # The next page carries all of it, and its switch is checked.
        fields.update(recipe._data["values"])
        fields["event_bake"] = "plugins_run"
        page = main_of(recipe.bake(fields))
        carried = swappPageFields(page).fields_of("plugins_form")
        self.assertEqual("True", carried["plugins_sel_hello"])
        self.assertEqual("True", carried["plugins_applied_hello"])
        self.assertEqual("-greet", carried["plugins_opt_hello_-o"])

        # Closing the options without applying them invalidates the plugin:
        # they are no longer applied, it is not selected, and the values are
        # the ones they held.
        carried["event_bake"] = "plugins_options_hello"
        carried["options_close"] = ""
        recipe.bake(carried)
        self.assertEqual({"plugins_sel_hello": "False", "plugins_applied_hello": "False",
                          "plugins_opt_hello_-o": "-greet"}, recipe._data["values"])

    # -----------------------------------------------------------------------

    def test_te25_each_plugin_keeps_its_own_values(self):
        """TE25. Each plugin keeps its own values: applying values to one changes nothing of another. [204]"""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "",
                          [{"id": "-o", "type": "str", "value": "-hello", "text": "Output pattern"}])
        install_for_tests(self.folder, "markers", "Markers", "Adds a tier of markers.", "",
                          [{"id": "-o", "type": "str", "value": "-mark", "text": "Output pattern"}])
        recipe = swappPluginsResponseRecipe()
        page = main_of(recipe.bake({}))

        recipe.bake(swappPageFields(page).submitted("event_bake", "plugins_options_hello"))
        fields = swappPageFields(page).fields_of("plugins_form")
        applied = dict(fields)
        applied.update(swappPageFields(recipe._data["options"]).fields_of("#form1"))
        applied["option_-o"] = "-greet"
        applied["options_validate"] = ""
        applied["event_bake"] = "plugins_options_hello"
        recipe.bake(applied)

        fields.update(recipe._data["values"])
        fields["event_bake"] = "plugins_run"
        carried = swappPageFields(main_of(recipe.bake(fields))).fields_of("plugins_form")
        self.assertEqual("-greet", carried["plugins_opt_hello_-o"])
        self.assertEqual("True", carried["plugins_applied_hello"])
        self.assertEqual("-mark", carried["plugins_opt_markers_-o"])
        self.assertEqual("False", carried["plugins_applied_markers"])


if __name__ == "__main__":
    unittest.main()
