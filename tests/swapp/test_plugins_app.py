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
import platform
import re
import shutil
import tempfile
import threading
import time
import unittest
import zipfile
from unittest import mock

import sppas.src.plugins.manager
from sppas.src.plugins.pluginsexc import CommandSystemError
from sppas.src.structs import sppasOption
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.swapp_core.swapps import WEB_APPLICATIONS
from sppas.ui.swapp.app_plugins import swappPluginsWebData
from sppas.ui.swapp.app_plugins import swappPluginsResponseRecipe
from sppas.ui.swapp.app_plugins import plugins_model
from sppas.ui.swapp.app_plugins import plugins_run
from sppas.ui.swapp.app_plugins.plugins_model import swappPluginsModel
from sppas.ui.swapp.app_plugins.plugins_run import swappPluginRun
from sppas.ui.swapp.app_plugins.plugins_run import swappPluginsReport
from sppas.ui.swapp.app_plugins.plugins_run import REPORT_PREFIX
from sppas.ui.swapp.app_plugins.plugins_run import swappFileResult
from sppas.ui.swapp.app_plugins.plugins_view import MSG_NOT_PERFORMED
from sppas.ui.swapp.app_plugins.plugins_view import MSG_NO_DOMAIN
from sppas.ui.swapp.app_plugins.plugins_view import MSG_MISSING
from sppas.ui.swapp.swapp_base import swapp_process
from sppas.ui.swapp.swapp_base.swapp_process import swappProcess
from sppas.ui.swapp.swapp_base.swapp_process import PROCESS_FIELD
from sppas.ui.swapp.swapp_base.swapp_process import PROGRESS_EVENT
from sppas.ui.swapp.swapp_base.swapp_help import HELP_TASK
from sppas.ui.swapp.swapp_base.swapp_help import BACK_TASK
from sppas.ui.swapp.services.files.files_chooser import swappFileChooser
from sppas.ui.swapp.services.files.files_chooser import MSG_NO_CHOOSER

from tests.swapp.page_requests import main_of
from tests.swapp.page_requests import swappPageFields

# ---------------------------------------------------------------------------


class PathsForTests:
    """The paths of SPPAS, where the folders of the plugins and of the logs are the ones of a test."""

    plugins = ""
    logs = ""

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

        # Locally, the default page is the app: online, it leads to a secret name.
        data = swappPluginsWebData()
        with mock.patch.object(swapp_settings, "served_locally", True):
            self.assertTrue(data.is_page("plugins.html"))
            self.assertIsInstance(data.bake_response("plugins.html"), swappPluginsResponseRecipe)
            self.assertIsNone(data.bake_response("annotate.html"))

    # -----------------------------------------------------------------------

    def test_te20_installing_and_deleting_above_the_list(self):
        """TE20. On the machine of the person, the section of the plugins carries installing and deleting above the list; on a server, neither. [025], RO1"""
        with mock.patch.object(swapp_settings, "served_locally", True):
            page = main_of(swappPluginsResponseRecipe().bake({}))
        plugins = page[page.find('id="plugins_section"'):page.find('id="plugins_list"')]
        self.assertIn('id="plugins_install"', plugins)
        self.assertIn('id="plugins_delete"', plugins)
        # What says the server waits for the archive is hidden, with a progress which has no end.
        waiting = re.search(r'<div id="plugins_waiting"[^>]*>(.*?)</div>', plugins, re.S)
        self.assertIsNotNone(waiting)
        self.assertIn('role="status"', waiting.group(0))
        self.assertIn('hidden', waiting.group(0))
        self.assertIn('<progress aria-labelledby="plugins_waiting_text">', waiting.group(1))
        self.assertNotIn('value=', waiting.group(1))

        with mock.patch.object(swapp_settings, "served_locally", False):
            page = main_of(swappPluginsResponseRecipe().bake({}))
        self.assertNotIn('id="plugins_install"', page)
        self.assertNotIn('id="plugins_delete"', page)
        self.assertNotIn('id="plugins_waiting"', page)

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

    def test_no_plugin_can_be_listed(self):
        """The domain of the plugins cannot be created: it is said in the dialog of the errors. Level 4"""
        with mock.patch.object(plugins_model, "sppasPluginsManager", side_effect=OSError("no folder")):
            recipe = swappPluginsResponseRecipe()
            page = main_of(recipe.bake({}))
        errors = re.search(r'<dialog id="error_dialog"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIn(MSG_NO_DOMAIN, errors)
        self.assertEqual(MSG_NO_DOMAIN, recipe._data["error"])
        self.assertNotIn('id="plugins_section"', page)

        # Whatever is asked, it is said again.
        recipe.bake({"event_bake": "plugins_run"})
        self.assertEqual(MSG_NO_DOMAIN, recipe._data["error"])

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
        self.assertIsNotNone(re.search(r'<dialog id="plugin_about_hello" class="hidden-alert"', page))
        # The title, on one line: the icon, and About the name of the plugin.
        title = re.search(r'<h2 id="plugin_about_hello_h" class="flex-panel">(.*?)</h2>', hello, re.S).group(1)
        icon = os.path.relpath(os.path.join(self.folder, "hello", "hello.png"))
        self.assertIsNotNone(re.search(r'^\s*<img alt="Plugin logo" src="' + re.escape(icon) + r'" class="flex-item small-logo width_10" />'
                                       r'\s*<span class="flex-item width_80">\s*About Hello\s*</span>\s*$', title))
        self.assertNotIn("<section", hello)
        self.assertNotIn("<p>", hello)
        self.assertIn("&lt;b&gt;Hello&lt;/b&gt; &amp; more", hello)
        self.assertNotIn("<button", hello)

        markers = re.search(r'<dialog id="plugin_about_markers"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIsNotNone(re.search(r'<h2 id="plugin_about_markers_h" class="flex-panel">\s*<span class="flex-item width_80">\s*About Markers\s*</span>\s*</h2>', markers))
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

    def test_te20_installing_a_plugin(self):
        """TE20. The archive the person designates is installed in a folder named after it, and it is said. T02"""
        archive = os.path.join(tempfile.mkdtemp(prefix="test_plugins_archive_"), "my hello.zip")
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("hello.json", json.dumps({"id": "hello", "name": "Hello", "descr": "", "icon": "",
                                                 "commands": {"windows": "$PY", "macos": "$PY", "linux": "$PY"},
                                                 "options": []}))
        recipe = swappPluginsResponseRecipe()
        with mock.patch.object(swapp_settings, "served_locally", True), \
                mock.patch.object(swappPluginsModel, "choose_archive", return_value=archive):
            page = main_of(recipe.bake({"event_bake": "plugins_install"}))
        self.assertEqual(["Hello"], [name_of(line) for line in lines_of(page)])
        self.assertTrue(os.path.isdir(os.path.join(self.folder, "my_hello")))
        info = re.search(r'<dialog id="info_dialog"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIn("Plugin successfully installed in folder my_hello.", info)
        # Asked without leaving the page: the section of the plugins, with the one
        # which was installed, and what is said.
        self.assertIn("Plugin successfully installed in folder my_hello.", recipe._data["info"])
        self.assertNotIn("error", recipe._data)
        self.assertTrue(recipe._data["plugins"].strip().startswith('<section id="plugins_section"'))
        self.assertEqual(["Hello"], [name_of(line) for line in lines_of(recipe._data["plugins"])])

        # An archive which is not one: what the domain of the plugins refused is said.
        with open(archive, "w") as fp:
            fp.write("not a zip")
        with mock.patch.object(swapp_settings, "served_locally", True), \
                mock.patch.object(swappPluginsModel, "choose_archive", return_value=archive):
            page = main_of(recipe.bake({"event_bake": "plugins_install"}))
        errors = re.search(r'<dialog id="error_dialog"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIn("can't be installed", errors)
        self.assertIn("can't be installed", recipe._data["error"])
        # TE4: the plugins which are given are what they were.
        self.assertEqual(["Hello"], [name_of(line) for line in lines_of(page)])
        self.assertNotIn("info", recipe._data)
        self.assertNotIn("plugins", recipe._data)
        shutil.rmtree(os.path.dirname(archive), ignore_errors=True)

        # A selection window which could not be opened: it is said why.
        with mock.patch.object(swapp_settings, "served_locally", True), \
                mock.patch.object(swappFileChooser, "ask_for_files", return_value=list()), \
                mock.patch.object(swappFileChooser, "why_nothing", return_value=MSG_NO_CHOOSER):
            recipe.bake({"event_bake": "plugins_install"})
        self.assertEqual(MSG_NO_CHOOSER, recipe._data["error"])
        self.assertNotIn("plugins", recipe._data)

        # No archive chosen: nothing is said.
        with mock.patch.object(swapp_settings, "served_locally", True), \
                mock.patch.object(swappFileChooser, "ask_for_files", return_value=list()), \
                mock.patch.object(swappFileChooser, "why_nothing", return_value=""):
            recipe.bake({"event_bake": "plugins_install"})
        self.assertNotIn("error", recipe._data)
        self.assertNotIn("info", recipe._data)

    # -----------------------------------------------------------------------

    def test_te3_a_plugin_this_machine_cannot_run(self):
        """TE3. A plugin whose command this machine cannot run is refused at its installation, with its cause, and is not among the plugins which are given. [031], [032]"""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "")
        commands = {"amiga": "$PY"}
        archive = os.path.join(tempfile.mkdtemp(prefix="test_plugins_archive_"), "elsewhere.zip")
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("elsewhere.json", json.dumps({"id": "elsewhere", "name": "Elsewhere", "descr": "", "icon": "",
                                                     "commands": commands, "options": []}))
        recipe = swappPluginsResponseRecipe()
        with mock.patch.object(swapp_settings, "served_locally", True), \
                mock.patch.object(swappPluginsModel, "choose_archive", return_value=archive):
            page = main_of(recipe.bake({"event_bake": "plugins_install"}))
        cause = str(CommandSystemError(platform.system().lower(), commands.keys()))
        self.assertIn(cause, recipe._data["error"])
        self.assertEqual(["Hello"], [name_of(line) for line in lines_of(page)])
        self.assertFalse(os.path.exists(os.path.join(self.folder, "elsewhere")))
        shutil.rmtree(os.path.dirname(archive), ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te20_deleting_a_plugin(self):
        """TE20. The plugin is chosen among the installed ones, removed, and it is said; on a server, nothing is. T03"""
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "")
        install_for_tests(self.folder, "markers", "Markers", "Adds a tier of markers.", "")
        recipe = swappPluginsResponseRecipe()
        with mock.patch.object(swapp_settings, "served_locally", False):
            page = main_of(recipe.bake({"event_bake": "plugins_delete", "plugins_to_delete": "hello"}))
        self.assertEqual(["Hello", "Markers"], sorted([name_of(line) for line in lines_of(page)]))

        with mock.patch.object(swapp_settings, "served_locally", True):
            page = main_of(recipe.bake({}))
            self.assertIsNotNone(re.search(r'<dialog id="plugins_delete_dialog" class="hidden-alert"', page))
            dialog = re.search(r'<dialog id="plugins_delete_dialog"[^>]*>(.*?)</dialog>', page, re.S).group(1)
            self.assertIsNotNone(re.search(r'<h2 id="plugins_delete_dialog_h">', dialog))
            self.assertEqual(["hello", "markers"],
                             sorted(re.findall(r'name="plugins_to_delete" value="([^"]*)"', dialog)))
            page = main_of(recipe.bake({"event_bake": "plugins_delete", "plugins_to_delete": "hello"}))
        self.assertEqual(["Markers"], [name_of(line) for line in lines_of(page)])
        self.assertFalse(os.path.exists(os.path.join(self.folder, "hello")))
        info = re.search(r'<dialog id="info_dialog"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIn("Plugin hello was successfully deleted.", info)

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

# ---------------------------------------------------------------------------

# A plugin which writes a file beside the file it is given, named after it
# and after the value of its option, and says so.
WRITER = """import os
import sys
_input = sys.argv[1]
_suffix = sys.argv[sys.argv.index("-o") + 1]
with open(os.path.splitext(_input)[0] + _suffix + ".txt", "w") as fp:
    fp.write("written")
sys.stderr.write("written " + os.path.basename(_input))
"""

# A plugin which fails on every file, and says why.
FAILER = """import sys
sys.stderr.write("boom \u00e9")
sys.exit(1)
"""


def install_script_for_tests(folder: str, identifier: str, script: str, options: list) -> None:
    """Write a plugin whose command is a script of its folder, run by the interpreter which runs the tests."""
    _plugin = os.path.join(folder, identifier)
    os.mkdir(_plugin)
    with open(os.path.join(_plugin, "run.py"), "w", encoding="utf-8") as fp:
        fp.write(script)
    _command = "$PY PLUGIN_PATHrun.py"
    _config = {"id": identifier, "name": identifier.capitalize(), "descr": "", "icon": "",
               "commands": {"windows": _command, "macos": _command, "linux": _command},
               "options": [{"id": "input", "type": "file", "value": "input", "text": ""}] + options}
    with open(os.path.join(_plugin, identifier + ".json"), "w", encoding="utf-8") as fp:
        json.dump(_config, fp)

# ---------------------------------------------------------------------------


class TestPluginRun(unittest.TestCase):
    """TE7 to TE9. A run, its results and its record, without a plugin."""

    def setUp(self):
        self.files = ["/data/a.txt", "/data/b.txt"]
        self.first = swappFileResult(self.files[0], True, "written a.txt", ["/data/a-hello.txt"])
        self.second = swappFileResult(self.files[1], False, "boom", list())

    # -----------------------------------------------------------------------

    def test_te7_a_result_is_held_with_what_came_of_it(self):
        """TE7. After one result is added, the run holds it and what came of it; the results keep the order they were added in. T06"""
        run = swappPluginRun("writer", "now", {"-o": "-hello"}, self.files)
        run.add(self.first)
        self.assertEqual(1, len(run.results))
        self.assertEqual("/data/a.txt", run.results[0].file)
        self.assertTrue(run.results[0].done)
        self.assertEqual("written a.txt", run.results[0].said)
        self.assertEqual(["/data/a-hello.txt"], run.results[0].produced)

        run.add(self.second)
        self.assertEqual(self.files, [_result.file for _result in run.results])

    # -----------------------------------------------------------------------

    def test_te8_a_run_is_over_with_one_result_per_file(self):
        """TE8. A run which holds one result per file it was given is over; one which holds fewer is not. The states"""
        run = swappPluginRun("writer", "now", dict(), self.files)
        self.assertFalse(run.is_over())
        self.assertEqual(2, run.remaining())
        run.add(self.first)
        self.assertFalse(run.is_over())
        self.assertEqual(1, run.remaining())
        run.add(self.second)
        self.assertTrue(run.is_over())
        self.assertEqual(0, run.remaining())

    # -----------------------------------------------------------------------

    def test_te9_a_run_parsed_twice_is_the_same_run(self):
        """TE9. A run parsed twice gives the same run. The contract of the record"""
        run = swappPluginRun("writer", "2026-11-26T10:00:00", {"-o": "-hello"}, self.files)
        run.add(self.first)
        data = run.serialize()
        once = swappPluginRun.parse(data)
        twice = swappPluginRun.parse(once.serialize())
        self.assertEqual(data, once.serialize())
        self.assertEqual(data, twice.serialize())

# ---------------------------------------------------------------------------


class ProgressForTests:
    """A progress which keeps what it was told."""

    def __init__(self):
        self.headers = list()
        self.texts = list()

    def set_header(self, header: str) -> None:
        self.headers.append(header)

    def update(self, percent=None, message=None) -> None:
        self.texts.append(message)

# ---------------------------------------------------------------------------


class FilesForTests:
    """The provision of files, as the model of Plugins calls it: the batch, and what is given back."""

    def __init__(self, filenames: list):
        self.batch = sppasWorkspace()
        for _filename in filenames:
            self.batch.add_file(_filename)
            self.batch.set_object_state(States().CHECKED, self.batch.get_object(_filename))
        self.locked = list()
        self.released = list()
        self.given_back = 0
        self.finished = 0

    def files_for_app(self):
        return self.batch

    def lock(self, filenames: list) -> int:
        self.locked.extend(filenames)
        return len(filenames)

    def release(self, filenames: list) -> int:
        self.released.extend(filenames)
        return len(filenames)

    def produced(self, workspace) -> dict:
        self.given_back += 1
        return dict()

    def consumes(self, events: dict) -> bool:
        if events == {"task": "finished"}:
            self.finished += 1
        return True

    def address_of(self, filename: str) -> str:
        return ""

    def address_of_all(self, filenames: list) -> str:
        return ""

# ---------------------------------------------------------------------------


class TestRuns(unittest.TestCase):
    """TE10 to TE18, TE19, TE22 to TE24, TE26 to TE28. Runs which really happen, with plugins written for the tests."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_plugins_run_")
        PathsForTests.plugins = os.path.join(self.folder, "plugins")
        PathsForTests.logs = os.path.join(self.folder, "logs")
        os.mkdir(PathsForTests.plugins)
        os.mkdir(PathsForTests.logs)
        self.patchers = [mock.patch.object(sppas.src.plugins.manager, "paths", PathsForTests),
                         mock.patch.object(plugins_model, "paths", PathsForTests),
                         mock.patch.object(plugins_run, "paths", PathsForTests),
                         mock.patch.object(swapp_process, "paths", PathsForTests)]
        for _patcher in self.patchers:
            _patcher.start()
        install_script_for_tests(PathsForTests.plugins, "writer", WRITER,
                                 [{"id": "-o", "type": "str", "value": "-hello", "text": "Suffix"}])
        install_script_for_tests(PathsForTests.plugins, "failer", FAILER, [])

        # The files of the person, in a folder of their own.
        self.data = os.path.join(self.folder, "data")
        os.mkdir(self.data)
        self.filenames = list()
        for _name in ("a.txt", "b.txt"):
            self.filenames.append(os.path.join(self.data, _name))
            with open(self.filenames[-1], "w", encoding="utf-8") as fp:
                fp.write(_name)
        self.files = FilesForTests(self.filenames)
        self.model = swappPluginsModel(self.files)

    def tearDown(self):
        for _patcher in self.patchers:
            _patcher.stop()
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te26_te27_te28_two_plugins_one_after_the_other(self):
        """TE10 to TE13, TE19, TE26 to TE28. The runs of two plugins, in the order of the list, file by file. [302] to [306]"""
        runs = [swappPluginRun("failer", "now", dict(), self.filenames),
                swappPluginRun("writer", "now", {"-o": "-greet"}, self.filenames)]
        report = swappPluginsReport(REPORT_PREFIX + "test.json")
        self.model.run(runs, report)

        # The plugin which failed on every file did not keep the next one from running.
        self.assertEqual(["failer", "writer"], [_run.plugin for _run in report.read()])
        failed, written = report.read()
        self.assertTrue(failed.is_over())
        self.assertTrue(written.is_over())

        # One result per file, in the order of the files; what was said, as it was said.
        self.assertEqual(self.filenames, [_result.file for _result in failed.results])
        for _result in failed.results:
            self.assertFalse(_result.done)
            self.assertEqual("boom \u00e9", _result.said)
            self.assertEqual(list(), _result.produced)

        # The values the run was started with are the ones the plugin was started with;
        # what appeared for one file is in the result of that file, and in no other.
        for _result, _name in zip(written.results, ("a", "b")):
            self.assertTrue(_result.done)
            self.assertEqual("written " + _name + ".txt", _result.said)
            self.assertEqual([os.path.join(self.data, _name + "-greet.txt")], _result.produced)

        # The runs give nothing back: the request which asks for the results
        # releases the files, and gives back what appeared, once.
        self.assertEqual(list(), self.files.released)
        self.assertEqual(0, self.files.given_back)
        self.model.give_back(report.name)
        self.assertEqual(self.filenames, self.files.released)
        self.assertEqual(1, self.files.given_back)
        self.assertEqual(1, self.files.finished)

    # -----------------------------------------------------------------------

    def test_te16_a_process_which_has_ended(self):
        """TE16. Started as a process: once it has ended, the run is over and it is not said to be going."""
        option = sppasOption("-o")
        option.set_type("str")
        option.set_value("-hello")
        report, process = self.model.start(["writer"], {"writer": [option]})
        # The files are locked by the request which starts the runs.
        self.assertEqual(self.filenames, self.files.locked)

        _waited = 0.
        while self.model.is_running(process) is True and _waited < 10.:
            time.sleep(0.05)
            _waited += 0.05
        self.assertFalse(self.model.is_running(process))

        runs = self.model.the_run(report)
        self.assertEqual(1, len(runs))
        self.assertTrue(runs[0].is_over())
        self.assertEqual({"-o": "-hello"}, runs[0].values)
        self.assertEqual(os.path.join(self.data, "a-hello.txt"), runs[0].results[0].produced[0])

        # No process bears a name which is not the one of a process.
        self.assertFalse(self.model.is_running("nobody"))

    # -----------------------------------------------------------------------

    def test_te23_the_help_while_the_runs_go(self):
        """TE23. While the runs go, the page follows them by the same process, and asking for the help is coming back to their progress. RO2"""
        gate = threading.Event()
        process = swappProcess.start(TestRuns.waits, (gate,))
        try:
            recipe = swappPluginsResponseRecipe()
            for task in (HELP_TASK, BACK_TASK):
                page = main_of(recipe.bake({"event_bake": task, PROCESS_FIELD: process.name}))
                self.assertIn('id="progress_section"', page)
                # As the installation of Setup: the section names the runs, and the
                # header of the progress is the node the plugin which is running is written in.
                self.assertIsNotNone(re.search(r'<section id="plugins_run_section"[^>]*>\s*<h2>\s*Run of the plugins\s*</h2>', page))
                self.assertIn('<h3 id="progress_header">', page)
                self.assertIsNotNone(re.search(r'<input [^>]*name="' + PROCESS_FIELD + '" value="' + re.escape(process.name) + '"', page))
        finally:
            gate.set()

        # Once the process has ended, the help is the help.
        _waited = 0.
        while self.model.is_running(process.name) is True and _waited < 10.:
            time.sleep(0.05)
            _waited += 0.05
        page = main_of(swappPluginsResponseRecipe().bake({"event_bake": HELP_TASK, PROCESS_FIELD: process.name}))
        self.assertNotIn('id="progress_section"', page)

    # -----------------------------------------------------------------------

    def test_te17_a_run_which_stopped(self):
        """TE17. A run which holds fewer results than files, once its process has ended, stopped: it is said in the dialog of the errors, with the results it holds. The states"""
        stopped = swappPluginRun("writer", "now", dict(), self.filenames)
        stopped.add(swappFileResult(self.filenames[0], True, "written a.txt", list()))
        over = swappPluginRun("failer", "now", dict(), self.filenames[:1])
        over.add(swappFileResult(self.filenames[0], False, "boom", list()))
        report = swappPluginsReport(REPORT_PREFIX + "stopped.json")
        report.write([stopped, over])

        recipe = swappPluginsResponseRecipe()
        page = main_of(recipe.bake({"event_bake": "plugins_complete", "plugins_report": report.name}))
        self.assertEqual("These runs stopped before their last file: Writer", recipe._data["error"])
        errors = re.search(r'<dialog id="error_dialog"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIn("These runs stopped before their last file: Writer", errors)
        self.assertIn("written a.txt", recipe._data["run"])
        self.assertIsNotNone(re.search(r'<h2>\s*Run of the plugins\s*</h2>', recipe._data["run"]))

    # -----------------------------------------------------------------------

    def test_a_report_which_cannot_be_read(self):
        """A report which cannot be read is said in the dialog of the errors, with the reason."""
        recipe = swappPluginsResponseRecipe()
        recipe.bake({"event_bake": "plugins_complete", "plugins_report": "nobody"})
        self.assertIn("The report is not available...", recipe._data["error"])
        self.assertIn("Not the name of a report of the plugins: nobody", recipe._data["error"])

    # -----------------------------------------------------------------------

    def test_te14_where_the_run_stands(self):
        """TE14. While the run goes, what it says of itself names the file being treated and how many remain. [303]"""
        runs = [swappPluginRun("writer", "now", {"-o": "-greet"}, self.filenames)]
        progress = ProgressForTests()
        self.model.run(runs, swappPluginsReport(REPORT_PREFIX + "te14.json"), progress)
        self.assertEqual(["writer", "writer"], progress.headers)
        self.assertEqual(["a.txt (1/2)", "b.txt (2/2)"], progress.texts)

    # -----------------------------------------------------------------------

    def test_te15_a_second_start_while_the_runs_go(self):
        """TE15. A second start asked for while the runs go is refused, and the refusal says that they go. The contract of the model"""
        recipe = swappPluginsResponseRecipe()
        fields = swappPageFields(main_of(recipe.bake({}))).fields_of("plugins_form")
        fields["plugins_sel_writer"] = "True"
        fields["plugins_applied_writer"] = "True"
        fields["event_bake"] = "plugins_run"

        gate = threading.Event()
        process = swappProcess.start(TestRuns.waits, (gate,))
        fields[PROCESS_FIELD] = process.name
        try:
            with mock.patch.object(swappPluginsModel, "files_for", return_value=self.filenames), \
                    mock.patch.object(swappPluginsModel, "start") as start:
                recipe.bake(fields)
            start.assert_not_called()
            self.assertEqual(MSG_MISSING["running"], recipe._data["info"])
        finally:
            gate.set()

    # -----------------------------------------------------------------------

    def test_te18_the_values_are_read_once_when_the_run_starts(self):
        """TE18. The values a run was started with are the ones the plugin was started with, even if the options are set again while the run goes. RO5"""
        option = sppasOption("-o")
        option.set_type("str")
        option.set_value("-hello")
        report, process = self.model.start(["writer"], {"writer": [option]})
        option.set_value("-other")

        _waited = 0.
        while self.model.is_running(process) is True and _waited < 10.:
            time.sleep(0.05)
            _waited += 0.05
        runs = self.model.the_run(report)
        self.assertEqual({"-o": "-hello"}, runs[0].values)
        self.assertTrue(os.path.exists(os.path.join(self.data, "a-hello.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.data, "a-other.txt")))

    # -----------------------------------------------------------------------

    def test_te22_the_page_which_starts_the_runs_follows_them(self):
        """TE22. The page which starts the runs shows their progress and names their process; where they stand is answered from the file of the process, the plugin as its header and the file as its text; once it has ended, the results are asked with the form. RO2"""
        run = swappPluginRun("writer", "now", {"-o": "-hello"}, self.filenames[:1])
        run.add(swappFileResult(self.filenames[0], True, "written a.txt", list()))
        report = swappPluginsReport(REPORT_PREFIX + "te22.json")
        report.write([run])

        recipe = swappPluginsResponseRecipe()
        fields = swappPageFields(main_of(recipe.bake({}))).fields_of("plugins_form")
        fields["plugins_sel_writer"] = "True"
        fields["plugins_applied_writer"] = "True"
        fields["event_bake"] = "plugins_run"

        gate = threading.Event()
        process = swappProcess.start(TestRuns.says_and_waits, (gate,))
        try:
            with mock.patch.object(swappPluginsModel, "files_for", return_value=self.filenames), \
                    mock.patch.object(swappPluginsModel, "start", return_value=(report.name, process.name)):
                recipe.bake(fields)
            # The page shows the progress, and carries the names of the process and of the report.
            self.assertIn('id="progress_section"', recipe._data["run"])
            carried = swappPageFields(recipe._data["run"]).fields_of("plugins_form")
            self.assertEqual(process.name, carried[PROCESS_FIELD])
            self.assertEqual(report.name, carried["plugins_report"])

            # Where the runs stand is answered from the file of the process.
            _waited = 0.
            while swappProcess(process.name).read()[1] != "writer" and _waited < 10.:
                time.sleep(0.05)
                _waited += 0.05
            recipe.bake({"event_name": PROGRESS_EVENT, PROCESS_FIELD: process.name})
            self.assertEqual({"percent": 0, "header": "writer", "text": "a.txt (1/1)"}, recipe._data)
        finally:
            gate.set()

        # Once the process has ended, the results are asked with the form.
        _waited = 0.
        while self.model.is_running(process.name) is True and _waited < 10.:
            time.sleep(0.05)
            _waited += 0.05
        completed = dict(fields)
        completed.update(carried)
        completed["event_bake"] = "plugins_complete"
        recipe.bake(completed)
        self.assertIn("written a.txt", recipe._data["run"])
        self.assertNotIn('id="progress_section"', recipe._data["run"])

    # -----------------------------------------------------------------------

    def test_te24_the_values_of_a_run_are_shown_the_next_time(self):
        """TE24. The values a run was started with are the ones shown the next time that plugin is asked to run. [203]"""
        recipe = swappPluginsResponseRecipe()
        page = main_of(recipe.bake({}))
        recipe.bake(swappPageFields(page).submitted("event_bake", "plugins_options_writer"))
        fields = swappPageFields(page).fields_of("plugins_form")
        applied = dict(fields)
        applied.update(swappPageFields(recipe._data["options"]).fields_of("#form1"))
        applied["option_-o"] = "-greet"
        applied["options_validate"] = ""
        applied["event_bake"] = "plugins_options_writer"
        recipe.bake(applied)
        fields.update(recipe._data["values"])

        fields["event_bake"] = "plugins_run"
        with mock.patch.object(swappPluginsModel, "files_for", return_value=self.filenames), \
                mock.patch.object(swappPluginsModel, "start", return_value=("a_report", "a_process")) as start:
            recipe.bake(fields)
        self.assertEqual("-greet", start.call_args[0][1]["writer"][0].get_value())

        # The next time the plugin is asked to run, its options hold the values of the run.
        fields["event_bake"] = "plugins_options_writer"
        recipe.bake(fields)
        option = re.search(r'<input [^>]*id="option_-o"[^>]*>', recipe._data["options"]).group(0)
        self.assertIn('value="-greet"', option)

    # -----------------------------------------------------------------------

    @staticmethod
    def waits(gate: threading.Event, progress=None) -> None:
        """A process which goes until the gate is opened."""
        gate.wait(10.)

    # -----------------------------------------------------------------------

    @staticmethod
    def says_and_waits(gate: threading.Event, progress=None) -> None:
        """A process which says where it stands as the runs say it, and goes until the gate is opened."""
        progress.set_header("writer")
        progress.update(0, "a.txt (1/1)")
        gate.wait(10.)

# ---------------------------------------------------------------------------


class TestStartRefused(unittest.TestCase):
    """TE29. What stands in the way of a start is said, naming the plugins, and nothing starts. [205]"""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_plugins_app_")
        PathsForTests.plugins = self.folder
        self.paths = mock.patch.object(sppas.src.plugins.manager, "paths", PathsForTests)
        self.paths.start()
        install_for_tests(self.folder, "hello", "Hello", "Writes a file of greetings.", "")

    def tearDown(self):
        self.paths.stop()
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te29_a_selected_plugin_whose_options_were_not_applied(self):
        """TE29. The plugin is named, and that no file was chosen is said: nothing starts."""
        recipe = swappPluginsResponseRecipe()
        page = main_of(recipe.bake({}))
        fields = swappPageFields(page).fields_of("plugins_form")
        fields["plugins_sel_hello"] = "True"
        fields["event_bake"] = "plugins_run"
        recipe.bake(fields)
        self.assertIn("The options of these plugins were not applied: Hello", recipe._data["info"])
        self.assertIn("No file was chosen.", recipe._data["info"])
        self.assertNotIn("run", recipe._data)

        # Its options applied, only the files are missing.
        fields["plugins_applied_hello"] = "True"
        recipe.bake(fields)
        self.assertEqual("No file was chosen.", recipe._data["info"])
        self.assertNotIn("run", recipe._data)

    # -----------------------------------------------------------------------

    def test_runs_which_cannot_be_started(self):
        """What raised when the runs were started is said in the dialog of the errors, and nothing starts. Level 4"""
        recipe = swappPluginsResponseRecipe()
        page = main_of(recipe.bake({}))
        fields = swappPageFields(page).fields_of("plugins_form")
        fields["plugins_sel_hello"] = "True"
        fields["plugins_applied_hello"] = "True"
        fields["event_bake"] = "plugins_run"
        with mock.patch.object(swappPluginsModel, "files_for", return_value=["a.txt"]), \
                mock.patch.object(swappPluginsModel, "start", side_effect=OSError("no room")):
            page = main_of(recipe.bake(fields))
        self.assertEqual(MSG_NOT_PERFORMED, recipe._data["error"])
        errors = re.search(r'<dialog id="error_dialog"[^>]*>(.*?)</dialog>', page, re.S).group(1)
        self.assertIn(MSG_NOT_PERFORMED, errors)
        self.assertNotIn("run", recipe._data)


if __name__ == "__main__":
    unittest.main()
