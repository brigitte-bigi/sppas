# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_plugins.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the app which runs the plugins.

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

    TE1 to TE19 of the dossier "Plugins - an app of SPPAS". Nine of them start
    no run at all. The ten others start plugins written here for the tests:
    one which writes a file, one which fails, one which says nothing, one
    which takes its time. No plugin of the person is ever started.

"""

from __future__ import annotations
import unittest
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile

from sppas.ui.swapp.app_plugins.plugins_installed import sppasInstalledPlugins
from sppas.ui.swapp.app_plugins.plugins_run import sppasPluginExecution
from sppas.ui.swapp.app_plugins.plugins_run import sppasPluginRun
from sppas.ui.swapp.app_plugins.plugins_exchange import sppasPluginExchange
from sppas.ui.swapp.app_plugins.plugins_record import sppasPluginsRecord

# ---------------------------------------------------------------------------

WRITES = """import sys, os
name = sys.argv[1]
with open(os.path.splitext(name)[0] + '-out.txt', 'w') as fp:
    fp.write('done')
print('wrote ' + os.path.splitext(name)[0] + '-out.txt')
"""

FAILS = """import sys
sys.stderr.write('this plugin refuses to treat ' + sys.argv[1])
sys.exit(1)
"""

SILENT = """import sys
"""

SLOW = """import sys, time
time.sleep(2.)
print('at last')
"""

# ---------------------------------------------------------------------------


def make_plugin(where: str, identifier: str, script: str,
                command: str | None = None) -> str:
    """Write a plugin in a folder of its own, and give its folder name.

    :param where: (str) The plugins directory.
    :param identifier: (str) Identifier and folder name of the plugin.
    :param script: (str) What the plugin does, as a python script.
    :param command: (str|None) The command to declare, to declare another one.

    """
    folder = os.path.join(where, identifier)
    os.makedirs(folder)
    with open(os.path.join(folder, "__init__.py"), "w") as fp:
        fp.write("")
    with open(os.path.join(folder, identifier + ".py"), "w") as fp:
        fp.write(script)

    runs = command if command is not None else \
        "$PY PLUGIN_PATH" + identifier + ".py"
    config = {
        "id": identifier,
        "name": "Plugin " + identifier,
        "descr": "What " + identifier + " says of itself.",
        "icon": identifier + ".png",
        "version": "1.0",
        "commands": {"windows": runs, "macos": runs, "linux": runs},
        "options": [{"id": "input", "type": "file", "value": "input"}]
    }
    with open(os.path.join(folder, identifier + ".json"), "w") as fp:
        json.dump(config, fp)

    return folder


def make_archive(folder: str, into: str) -> str:
    """Give a zip archive of a plugin folder, as one is handed over."""
    archive = os.path.join(into, os.path.basename(folder) + ".zip")
    with zipfile.ZipFile(archive, "w") as z:
        for name in os.listdir(folder):
            z.write(os.path.join(folder, name), name)
    return archive


def some_files(where: str, how_many: int) -> list:
    """Give files for a run to work on."""
    files = list()
    for i in range(how_many):
        path = os.path.join(where, "file%d.txt" % i)
        with open(path, "w") as fp:
            fp.write("something")
        files.append(path)
    return files


def until(what, seconds: float = 10.) -> bool:
    """Wait for a thing to become true, and say whether it did."""
    end = time.time() + seconds
    while time.time() < end:
        if what() is True:
            return True
        time.sleep(0.05)
    return False

# ---------------------------------------------------------------------------


class TestWithoutARun(unittest.TestCase):
    """TE1 to TE9. A plugin which is installed, and nothing is started."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test_plugins_")
        self.plugins_dir = os.path.join(self.root, "plugins")
        os.makedirs(self.plugins_dir)
        make_plugin(self.plugins_dir, "writes", WRITES)
        self.installed = sppasInstalledPlugins(self.plugins_dir)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te1_every_plugin_which_is_installed(self):
        """TE1. And no other. [011]"""
        self.assertEqual(["writes"], [p.get_key() for p in self.installed.all()])

        make_plugin(self.plugins_dir, "fails", FAILS)
        self.assertEqual(["fails", "writes"],
                         sorted(p.get_key() for p in
                                sppasInstalledPlugins(self.plugins_dir).all()))

    # -----------------------------------------------------------------------

    def test_te2_what_a_plugin_declares_of_itself(self):
        """TE2. Its name, what it says of itself, its version, its icon &mdash;
        and nothing this application wrote. [012], [013]

        """
        plugin = self.installed.one("writes")

        self.assertEqual("Plugin writes", plugin.get_name())
        self.assertEqual("What writes says of itself.", plugin.get_descr())
        self.assertTrue(plugin.get_icon().endswith("writes.png"))

    # -----------------------------------------------------------------------

    def test_te3_a_plugin_which_cannot_run_here(self):
        """TE3. Its command names something this machine does not have, and
        nothing is started to find out. [031], [032]

        """
        self.assertTrue(self.installed.can_run_here("writes"))

        make_plugin(self.plugins_dir, "absent", SILENT,
                    command="a-command-this-machine-does-not-have")
        installed = sppasInstalledPlugins(self.plugins_dir)

        self.assertFalse(installed.can_run_here("absent"))
        self.assertIn("absent", [p.get_key() for p in installed.all()])

    # -----------------------------------------------------------------------

    def test_te4_what_the_domain_refuses_is_relayed(self):
        """TE4. The plugins which are given are what they were, and what stood
        in the way is named. What an archive has to be is the other domain's to
        say, and it is tested there. [023]

        """
        before = [p.get_key() for p in self.installed.all()]
        not_an_archive = os.path.join(self.root, "not-an-archive.zip")
        with open(not_an_archive, "w") as fp:
            fp.write("this is not a zip file")

        installed, why = self.installed.install(not_an_archive)

        self.assertFalse(installed)
        self.assertTrue(len(why) > 0)
        self.assertEqual(before, [p.get_key() for p in self.installed.all()])

    # -----------------------------------------------------------------------

    def test_te5_what_the_domain_installed_is_relayed(self):
        """TE5. The plugin is among those which are given, with what it declares
        of itself. [021]

        """
        aside = os.path.join(self.root, "aside")
        os.makedirs(aside)
        archive = make_archive(make_plugin(aside, "another", SILENT), self.root)

        installed, why = self.installed.install(archive)

        self.assertTrue(installed)
        self.assertEqual("", why)
        given = {p.get_key(): p for p in self.installed.all()}
        self.assertIn("another", given)
        self.assertEqual("Plugin another", given["another"].get_name())

    # -----------------------------------------------------------------------

    def test_te6_what_the_domain_removed_is_relayed(self):
        """TE6. The plugin is no longer among those which are given, and nothing
        else went with it. [022], [024]

        """
        make_plugin(self.plugins_dir, "stays", SILENT)
        installed = sppasInstalledPlugins(self.plugins_dir)
        produced = os.path.join(self.root, "file0-out.txt")
        with open(produced, "w") as fp:
            fp.write("done")

        removed, why = installed.remove("writes")

        self.assertTrue(removed)
        self.assertEqual(["stays"], [p.get_key() for p in installed.all()])
        self.assertTrue(os.path.exists(produced))

    # -----------------------------------------------------------------------

    def test_te7_a_run_holds_the_results_it_is_given(self):
        """TE7. With what came of each file, and in the order they were added
        in. T06

        """
        run = sppasPluginRun("writes", some_files(self.root, 3), dict())

        run.add("file0.txt", True, "wrote it", ["file0-out.txt"])
        run.add("file1.txt", False, "refused", list())

        results = run.results
        self.assertEqual(["file0.txt", "file1.txt"], [r.file for r in results])
        self.assertEqual(["file0-out.txt"], results[0].produced)
        self.assertEqual(list(), results[1].produced)

    # -----------------------------------------------------------------------

    def test_te8_a_run_is_over_or_it_is_not(self):
        """TE8. One result per file it was given, and not one fewer."""
        files = some_files(self.root, 2)
        run = sppasPluginRun("writes", files, dict())

        self.assertFalse(run.is_over())
        self.assertEqual(2, run.remaining())

        run.add(files[0], True, "", list())
        self.assertFalse(run.is_over())
        self.assertEqual(1, run.remaining())

        run.add(files[1], True, "", list())
        self.assertTrue(run.is_over())
        self.assertEqual(0, run.remaining())

    # -----------------------------------------------------------------------

    def test_te9_a_run_parsed_twice(self):
        """TE9. It gives the same run. Without this, a page which is reloaded
        loses what it was following.

        """
        run = sppasPluginRun("writes", some_files(self.root, 2), dict())
        run.add("file0.txt", True, "wrote it", ["file0-out.txt"])

        record = sppasPluginsRecord()
        record.run = run
        transported = record.serialize()

        once = sppasPluginsRecord.parse(transported)
        twice = sppasPluginsRecord.parse(transported)

        self.assertEqual(once.run.serialize(), twice.run.serialize())
        self.assertEqual("wrote it", once.run.results[0].what_was_said)

# ---------------------------------------------------------------------------


class TestWithARun(unittest.TestCase):
    """TE10 to TE19. Plugins written here are started, and no other."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test_plugins_")
        self.plugins_dir = os.path.join(self.root, "plugins")
        self.work = os.path.join(self.root, "work")
        os.makedirs(self.plugins_dir)
        os.makedirs(self.work)
        for identifier, script in (("writes", WRITES), ("fails", FAILS),
                                   ("silent", SILENT), ("slow", SLOW)):
            make_plugin(self.plugins_dir, identifier, script)
        self.installed = sppasInstalledPlugins(self.plugins_dir)
        self.execution = sppasPluginExecution(self.installed)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def a_run(self, plugin: str, how_many: int = 3) -> list:
        """Start a run and give the files it was given."""
        files = some_files(self.work, how_many)
        self.execution.start(plugin, files, dict())
        return files

    # -----------------------------------------------------------------------

    def test_te10_the_plugin_is_started_once_per_file(self):
        """TE10. On the files it was given, and on no others. [102], [302]"""
        files = self.a_run("writes", 3)
        aside = os.path.join(self.root, "not-of-the-run.txt")
        with open(aside, "w") as fp:
            fp.write("something")

        self.assertTrue(until(self.execution.the_run().is_over))

        run = self.execution.the_run()
        self.assertEqual(files, [r.file for r in run.results])
        self.assertFalse(os.path.exists(
            os.path.join(self.root, "not-of-the-run-out.txt")))

    # -----------------------------------------------------------------------

    def test_te11_the_failure_of_one_file(self):
        """TE11. That file has a result, and the files after it have theirs.
        [304]

        """
        files = self.a_run("fails", 3)

        self.assertTrue(until(self.execution.the_run().is_over))

        run = self.execution.the_run()
        self.assertEqual(3, len(run.results))
        self.assertEqual(files, [r.file for r in run.results])

    # -----------------------------------------------------------------------

    def test_te12_what_the_plugin_said_is_held_as_it_said_it(self):
        """TE12. Byte for byte. The day this test changes, this application has
        started to interpret. [403], RO3

        """
        files = self.a_run("fails", 1)

        self.assertTrue(until(self.execution.the_run().is_over))

        said = self.execution.the_run().results[0].what_was_said
        self.assertEqual("this plugin refuses to treat " + files[0], said)

    # -----------------------------------------------------------------------

    def test_te12bis_a_plugin_which_says_nothing(self):
        """TE12. Nothing is what it said, and nothing is written in its place."""
        self.a_run("silent", 1)

        self.assertTrue(until(self.execution.the_run().is_over))

        self.assertEqual("", self.execution.the_run().results[0].what_was_said)

    # -----------------------------------------------------------------------

    def test_te13_what_appeared_is_held_in_the_result_of_its_file(self):
        """TE13. And in no other. [402]"""
        files = self.a_run("writes", 2)

        self.assertTrue(until(self.execution.the_run().is_over))

        for result, given in zip(self.execution.the_run().results, files):
            expected = os.path.splitext(given)[0] + "-out.txt"
            self.assertEqual([expected], result.produced)

    # -----------------------------------------------------------------------

    def test_te14_where_a_run_stands_while_it_goes(self):
        """TE14. Which file is being treated, and how many remain. [303]"""
        self.a_run("slow", 3)

        self.assertTrue(self.execution.is_running())
        being, remaining = self.execution.where_it_stands()
        self.assertTrue(len(being) > 0)
        self.assertEqual(3, remaining)

        self.assertTrue(until(self.execution.the_run().is_over, 30.))
        self.assertEqual(0, self.execution.where_it_stands()[1])

    # -----------------------------------------------------------------------

    def test_te15_a_second_run_while_one_is_going(self):
        """TE15. Refused, and the refusal says that one is going. RO7"""
        self.a_run("slow", 3)

        started, why = self.execution.start(
            "writes", some_files(self.work, 1), dict())

        self.assertFalse(started)
        self.assertTrue(len(why) > 0)

    # -----------------------------------------------------------------------

    def test_te16_a_run_which_is_over(self):
        """TE16. It is over, and it is not said to be going."""
        self.a_run("writes", 2)

        self.assertTrue(until(self.execution.the_run().is_over))
        self.assertTrue(until(lambda: self.execution.is_running() is False))

        self.assertTrue(self.execution.the_run().is_over())

    # -----------------------------------------------------------------------

    def test_te17_a_run_whose_thread_died(self):
        """TE17. Neither going nor over: it stopped, and it holds the results it
        had. It is the one test which needs a thread to die, and it exists
        because a run which stopped and a run which is slow hold the same data.

        """
        files = self.a_run("slow", 3)
        self.assertTrue(until(self.execution.is_running))

        self.execution.kill_for_the_test()

        self.assertTrue(until(lambda: self.execution.is_running() is False, 30.))
        run = self.execution.the_run()
        self.assertFalse(run.is_over())
        self.assertLess(len(run.results), len(files))

    # -----------------------------------------------------------------------

    def test_te18_the_values_a_run_was_started_with(self):
        """TE18. They are the ones the plugin is started with, even if the
        options are set again while the run goes. RO5

        """
        files = some_files(self.work, 2)
        values = {"input": "input"}
        self.execution.start("writes", files, values)

        values["input"] = "something else entirely"

        self.assertTrue(until(self.execution.the_run().is_over))
        self.assertEqual({"input": "input"}, self.execution.the_run().values)

    # -----------------------------------------------------------------------

    def test_te19_what_was_produced_is_given_once(self):
        """TE19. When the run is over, and not at every file. T07"""
        given = list()
        exchange = sppasPluginExchange(produced=given.extend)

        files = self.a_run("writes", 3)
        self.assertTrue(until(self.execution.the_run().is_over))
        exchange.produced_of(self.execution.the_run())

        self.assertEqual(3, len(given))
        for one in files:
            self.assertIn(os.path.splitext(one)[0] + "-out.txt", given)

# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
