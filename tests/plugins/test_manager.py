"""
:filename: sppas.src.plugins.test.test_manager.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test of the plugins manager.

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
import os
import json
import shutil
import tempfile
from unittest import mock

from sppas.core.config import paths
from sppas.core.coreutils import info

import sppas.src.plugins.manager
from sppas.src.plugins.manager import sppasPluginsManager
from sppas.src.plugins.pluginsexc import PluginIdError

# ---------------------------------------------------------------------------

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
soxplugin = os.path.join(DATA, "soxplugintest.zip")
sample = os.path.join(paths.samples, "samples-eng", "oriana1.wav")

# ---------------------------------------------------------------------------


class TestPluginsManager(unittest.TestCase):

    def setUp(self):
        self.manager = sppasPluginsManager()

    def test_all(self):

        # some plugins are already installed in the package of SPPAS
        plg = 2   # audioseg is now distributed with the release
        self.assertEqual(plg, len(self.manager.get_plugin_ids()))

        # Install a plugin
        soxid = self.manager.install(soxplugin, "SoX")
        self.assertEqual(plg+1, len(self.manager.get_plugin_ids()))

        # Use it!
        output = sample.replace('.wav', '-converted.wav')
        p = self.manager.get_plugin(soxid)
        message = self.manager.run_plugin(soxid, [sample])

        # Delete it...
        self.manager.delete(soxid)
        self.assertEqual(plg, len(self.manager.get_plugin_ids()))

        # Test result of the run
        self.assertGreater(len(message), 0)
        self.assertTrue(os.path.exists(output))
        os.remove(output)

# ---------------------------------------------------------------------------


class PathsForTests:
    """The paths of SPPAS, where the folder of the plugins is the one of a test."""

    plugins = ""

# ---------------------------------------------------------------------------


def write_script(folder: str, name: str, content: str) -> str:
    """Write a script in the folder of a test, and return its name."""
    script = os.path.join(folder, name)
    with open(script, "w", encoding="utf-8") as fp:
        fp.write(content)
    return script

# ---------------------------------------------------------------------------


class TestPluginOnFile(unittest.TestCase):
    """A plugin applied on one file.

    The plugin is installed in a folder of the test. Its command is the
    interpreter which runs the tests: the file it is applied on is a script.

    """

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_plugins_manager_")
        PathsForTests.plugins = self.folder
        self.paths = mock.patch.object(sppas.src.plugins.manager, "paths", PathsForTests)
        self.paths.start()
        os.mkdir(os.path.join(self.folder, "say"))
        config = {"id": "say", "name": "Say", "descr": "", "icon": "",
                  "commands": {"windows": "$PY", "macos": "$PY", "linux": "$PY"},
                  "options": [{"id": "input", "type": "file", "value": "input", "text": ""}]}
        with open(os.path.join(self.folder, "say", "say.json"), "w", encoding="utf-8") as fp:
            json.dump(config, fp)
        self.manager = sppasPluginsManager()

    def tearDown(self):
        self.paths.stop()
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_what_the_plugin_said_and_its_code(self):
        """What the plugin wrote on its error output, and the code it returned."""
        script = write_script(self.folder, "speaks.py", "import sys\nsys.stderr.write('hello')\nsys.exit(3)\n")
        self.assertEqual(("hello", 3), self.manager.run_plugin_on_file("say", script))

    # -----------------------------------------------------------------------

    def test_a_plugin_which_says_nothing(self):
        """A plugin which wrote nothing is said to have done its task."""
        script = write_script(self.folder, "silent.py", "pass\n")
        self.assertEqual((info(4015, "plugins"), 0), self.manager.run_plugin_on_file("say", script))

    # -----------------------------------------------------------------------

    def test_an_unknown_plugin(self):
        """No plugin has that identifier."""
        script = write_script(self.folder, "silent.py", "pass\n")
        with self.assertRaises(PluginIdError):
            self.manager.run_plugin_on_file("nobody", script)

    # -----------------------------------------------------------------------

    def test_a_list_of_files_is_applied_file_by_file(self):
        """Applied on a list of files, the plugin says, for each file, what it says applied on that file."""
        speaks = write_script(self.folder, "speaks.py", "import sys\nsys.stderr.write('hello')\nsys.exit(3)\n")
        silent = write_script(self.folder, "silent.py", "pass\n")
        expected = ""
        for script in (speaks, silent):
            expected += info(4010, "plugins").format(filename=script) + "\n"
            expected += self.manager.run_plugin_on_file("say", script)[0] + "\n"
        self.assertEqual(expected, self.manager.run_plugin("say", [speaks, silent]))
