# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_swapp_process.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the long process of the apps of swapp, as the page follows it.

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

    "How a long process of an app is followed" and "How a long process holds
    the page", in the README of swapp. The requests are the ones the page
    sends: a button sends the fields of its form, read in the page the server
    answered, and the progress is asked as swapp_process.js asks it. The
    files of the processes are written in the folder of the logs of SPPAS.

"""

import os
import shutil
import tempfile
import time
import unittest
from unittest import mock

from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from sppas.ui.swapp.swapp_core.swappsg import swapp_serverstate
from sppas.ui.swapp.swapp_base.swapp_process import swappProcess
from sppas.ui.swapp.swapp_base.swapp_process import PROGRESS_EVENT
from sppas.ui.swapp.swapp_base.swapp_process import PROCESS_FIELD
from sppas.ui.swapp.services.files import swappWorkspaceFiles
from sppas.ui.swapp.app_annotate import annotate_run
from sppas.ui.swapp.app_annotate.annotate_maker import swappAnnotateResponseRecipe
from sppas.ui.swapp.app_convert.convert_maker import swappConvertResponseRecipe
from sppas.ui.swapp.app_dashboard.dashboard_maker import swappDashboardResponseRecipe
from sppas.ui.swapp.app_setup.setup_maker import swappSetupResponseRecipe

from tests.swapp.page_requests import swappPageFields
from tests.swapp.page_requests import main_of
from tests.swapp.test_annotate_run import ManagerForTests

# ---------------------------------------------------------------------------

# A TextGrid of one tier and one interval: what Convert converts.
TEXTGRID = ('File type = "ooTextFile"\nObject class = "TextGrid"\n\nxmin = 0\nxmax = 1\ntiers? <exists>\n'
            'size = 1\nitem []:\n    item [1]:\n        class = "IntervalTier"\n        name = "words"\n'
            '        xmin = 0\n        xmax = 1\n        intervals: size = 1\n        intervals [1]:\n'
            '            xmin = 0\n            xmax = 1\n            text = "hello"\n')

# ---------------------------------------------------------------------------


def progress_of(recipe, name: str) -> tuple:
    """Ask where a process stands, as swapp_process.js asks it.

    :param recipe: The bakery of the page which follows the process
    :param name: (str) The name of the process, as the page holds it
    :return: (tuple) What is answered, and its status

    """
    recipe.bake({"event_name": PROGRESS_EVENT, PROCESS_FIELD: name})
    return dict(recipe._data), recipe._status.code

# ---------------------------------------------------------------------------


def follow(recipe, name: str, seconds: float = 10.) -> tuple:
    """Ask where a process stands until it has ended, as the bar does.

    :param recipe: The bakery of the page which follows the process
    :param name: (str) The name of the process
    :param seconds: (float) How long to wait at most
    :return: (tuple) The last answer, and its status

    """
    _answer, _status = progress_of(recipe, name)
    _waited = 0.
    while _status != 200 and _waited < seconds:
        time.sleep(0.05)
        _waited += 0.05
        _answer, _status = progress_of(recipe, name)

    return _answer, _status

# ---------------------------------------------------------------------------


class TestProcess(unittest.TestCase):
    """swappProcess, and the progress it is given."""

    @staticmethod
    def steps(seconds, progress=None):
        """What a process performs: it says where it stands as the API does."""
        progress.set_new()
        progress.set_header("Step")
        progress.set_text("a text")
        progress.set_fraction(0.5)
        time.sleep(seconds)
        progress.update(1, "Completed.")

    # -----------------------------------------------------------------------

    @staticmethod
    def fails(progress=None):
        """What a process performs: it raises."""
        progress.set_header("Failing")
        raise RuntimeError("on purpose")

    # -----------------------------------------------------------------------

    def test_a_name_which_is_not_the_one_of_a_process(self):
        """A name with a path, of another pattern or of another extension, is refused."""
        for name in ("", "/tmp/sppas_process_x.json", "sppas_convert_x.json", "sppas_process_x.txt",
                     "../sppas_process_x.json"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    swappProcess(name)

    # -----------------------------------------------------------------------

    def test_start_answers_at_once(self):
        """The process goes on after start() has answered, and says where it stands."""
        process = swappProcess.start(TestProcess.steps, (0.4,))
        time.sleep(0.15)
        self.assertEqual((0.5, "Step", "a text", False), process.read())

        time.sleep(0.5)
        self.assertEqual((100, "Step", "Completed.", True), process.read())

    # -----------------------------------------------------------------------

    def test_two_processes_two_names(self):
        """Two processes are two files."""
        first = swappProcess.start(TestProcess.steps, (0.,))
        second = swappProcess.start(TestProcess.steps, (0.,))
        self.assertNotEqual(first.name, second.name)

    # -----------------------------------------------------------------------

    def test_a_process_which_raises_ends(self):
        """What raises ends the process all the same: the page is told it has ended."""
        process = swappProcess.start(TestProcess.fails, ())
        time.sleep(0.2)
        percent, header, text, finished = process.read()
        self.assertTrue(finished)
        self.assertEqual(100, percent)
        self.assertEqual("Failing", header)

    # -----------------------------------------------------------------------

    def test_a_process_read_by_another_object(self):
        """Whatever reads the file by the name reads the same: nothing is held by the object which started it."""
        process = swappProcess.start(TestProcess.steps, (0.3,))
        time.sleep(0.1)
        self.assertEqual(process.read(), swappProcess(process.name).read())

    # -----------------------------------------------------------------------

    def test_a_name_no_file_was_written_for(self):
        """Nothing was written: nothing has started, and nothing has ended."""
        self.assertEqual((0, "", "", False), swappProcess("sppas_process_never_written.json").read())

# ---------------------------------------------------------------------------


class TestProgressAnswer(unittest.TestCase):
    """Where a process stands is answered by the base recipe, whatever the app."""

    @staticmethod
    def wait(seconds, progress=None):
        progress.update(40, "two of five")
        time.sleep(seconds)

    # -----------------------------------------------------------------------

    def test_any_app_answers_it(self):
        """202 and where it stands while it goes; 200 and the hundred once it has ended."""
        for recipe_class in (swappDashboardResponseRecipe, swappConvertResponseRecipe, swappAnnotateResponseRecipe):
            with self.subTest(app=recipe_class.__name__):
                recipe = recipe_class()
                recipe.bake({})
                process = swappProcess.start(TestProgressAnswer.wait, (0.4,))
                time.sleep(0.1)
                answer, status = progress_of(recipe, process.name)
                self.assertEqual(202, status)
                self.assertEqual({"percent": 40, "header": "", "text": "two of five"}, answer)

                answer, status = follow(recipe, process.name)
                self.assertEqual(200, status)
                self.assertEqual(100, answer["percent"])

    # -----------------------------------------------------------------------

    def test_a_name_which_is_no_process(self):
        """A name which is not the one of a process, or no name at all: it has ended."""
        recipe = swappDashboardResponseRecipe()
        recipe.bake({})
        for name in ("", "anything.json", "sppas_convert_2026.json"):
            with self.subTest(name=name):
                answer, status = progress_of(recipe, name)
                self.assertEqual(200, status)
                self.assertEqual(100, answer["percent"])

    # -----------------------------------------------------------------------

    def test_the_page_is_not_built_again(self):
        """The main content of the app is not touched by asking where a process stands."""
        recipe = swappConvertResponseRecipe()
        page = recipe.bake({})
        process = swappProcess.start(TestProgressAnswer.wait, (0.,))
        progress_of(recipe, process.name)
        self.assertEqual(main_of(page), main_of(recipe._htree.serialize()))

    # -----------------------------------------------------------------------

    def test_is_running_by_the_name_the_request_carries(self):
        """By default, a process goes when the request names one which has not ended."""
        recipe = swappDashboardResponseRecipe()
        recipe.bake({})
        self.assertFalse(recipe.is_running())

        process = swappProcess.start(TestProgressAnswer.wait, (0.4,))
        recipe.bake({PROCESS_FIELD: process.name})
        self.assertTrue(recipe.is_running())

        time.sleep(0.6)
        recipe.bake({PROCESS_FIELD: process.name})
        self.assertFalse(recipe.is_running())

        recipe.bake({})
        self.assertFalse(recipe.is_running())

# ---------------------------------------------------------------------------


class TestConvertIsAProcess(unittest.TestCase):
    """A conversion, as the page of Convert starts it and follows it."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_swapp_process_")
        self.source = os.path.join(self.folder, "sample.TextGrid")
        with open(self.source, "w", encoding="utf-8") as fp:
            fp.write(TEXTGRID)
        self.recipe = swappConvertResponseRecipe()
        self.recipe.bake({})
        # The files stand already where SPPAS reads them: the person chose this one.
        manager = self.recipe._swappConvertResponseRecipe__manager
        manager._swappFilesManager__model.works_on(swappWorkspaceFiles.make_workspace([self.source]))

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def convert(self) -> str:
        """Press Convert, the destination .eaf being chosen, as ConvertManager sends it."""
        page = self.recipe.bake({})
        events = swappPageFields(page).submitted("event_bake", "convert")
        events["convert_destination"] = ".eaf"
        self.recipe.bake(events)
        return self.recipe._data["convert"]

    # -----------------------------------------------------------------------

    def test_the_page_names_the_process_and_the_report(self):
        """The section of the conversion shows the progress, and carries both names in the form."""
        section = self.convert()
        self.assertIn('id="percent_progress"', section)
        hidden = swappPageFields(section).hidden()
        self.assertTrue(hidden[PROCESS_FIELD].endswith(".json"))
        self.assertTrue(len(hidden["convert_report"]) > 0)

    # -----------------------------------------------------------------------

    def test_followed_until_the_results(self):
        """Where it stands is answered from the process; once ended, the results are asked with the form."""
        section = self.convert()
        hidden = swappPageFields(section).hidden()
        answer, status = follow(self.recipe, hidden[PROCESS_FIELD])
        self.assertEqual(200, status)
        self.assertEqual("1 / 1", answer["text"])

        page = self.recipe._htree.serialize()
        events = swappPageFields(page).fields_of("convert_form")
        events["event_bake"] = "complete"
        self.recipe.bake(events)
        self.assertIn("sample.eaf", self.recipe._data["convert"])
        self.assertTrue(os.path.exists(os.path.join(self.folder, "sample.eaf")))

    # -----------------------------------------------------------------------

    def test_the_old_event_of_the_progress_is_unknown(self):
        """Convert has no event of its own for the progress any more."""
        self.recipe.bake({"event_name": "update"})
        self.assertEqual(205, self.recipe._status.code)

# ---------------------------------------------------------------------------


class TestAnnotateIsAProcess(unittest.TestCase):
    """A run, as the page of Annotate starts it and follows it; no annotation of SPPAS is run."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_swapp_process_")
        self.source = os.path.join(self.folder, "sample.TextGrid")
        with open(self.source, "w", encoding="utf-8") as fp:
            fp.write(TEXTGRID)
        ManagerForTests.seconds = 0.3
        ManagerForTests.fails = ""
        ManagerForTests.created = list()
        ManagerForTests.writes = list()
        self.patcher = mock.patch.object(annotate_run, "sppasAnnotationsManager", ManagerForTests)
        self.patcher.start()
        # The files stand already where SPPAS reads them: the server is the local one.
        self.local = mock.patch.object(swapp_serverstate, "local", True)
        self.local.start()
        self.recipe = swappAnnotateResponseRecipe()
        self.recipe.bake({})
        manager = self.recipe._swappAnnotateResponseRecipe__manager
        manager._swappFilesManager__model.works_on(swappWorkspaceFiles.make_workspace([self.source]))

    def tearDown(self):
        while self.recipe.is_running() is True:
            time.sleep(0.05)
        self.local.stop()
        self.patcher.stop()
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def perform(self) -> str:
        """Select an annotation in the panel of its type, come back, and press Let's go, as the page sends them."""
        page = self.recipe.bake({})
        annotations = self.recipe.bake(swappPageFields(page).submitted("event_bake", "annotate_annotations_STANDALONE"))
        events = swappPageFields(annotations).submitted("event_bake", "annotate_steps")
        events["annotate_ann_textnorm"] = "True"
        steps = self.recipe.bake(events)
        self.recipe.bake(swappPageFields(steps).submitted("event_bake", "annotate_perform"))
        return self.recipe._data["main-content"]

    # -----------------------------------------------------------------------

    def test_the_page_names_the_process(self):
        """The progress is shown, and the form carries the name of the process and of the report."""
        main = self.perform()
        self.assertIn('id="percent_progress"', main)
        fields = swappPageFields(main).fields_of("annotate_form")
        self.assertTrue(fields[PROCESS_FIELD].endswith(".json"))
        self.assertTrue(len(fields["annotate_followed"]) > 0)
        self.assertEqual(["textnorm"], ManagerForTests.created[-1].activated)

    # -----------------------------------------------------------------------

    def test_followed_until_the_results(self):
        """Where it stands is answered from the process; once ended, the results are asked with the form."""
        main = self.perform()
        fields = swappPageFields(main).fields_of("annotate_form")
        answer, status = progress_of(self.recipe, fields[PROCESS_FIELD])
        self.assertEqual(202, status)
        self.assertEqual("textnorm", answer["header"])

        answer, status = follow(self.recipe, fields[PROCESS_FIELD])
        self.assertEqual(200, status)
        self.assertFalse(self.recipe.is_running())

        events = swappPageFields(main).fields_of("annotate_form")
        events["event_bake"] = "annotate_complete"
        self.recipe.bake(events)
        done = self.recipe._data["main-content"]
        self.assertIn('id="annotate_results_h"', done)
        self.assertIn("textnorm: done", done)

    # -----------------------------------------------------------------------

    def test_a_page_asked_for_while_it_goes(self):
        """A page loaded again while the run goes follows that run: the same process, the same report."""
        main = self.perform()
        fields = swappPageFields(main).fields_of("annotate_form")
        again = main_of(self.recipe.bake({}))
        refields = swappPageFields(again).fields_of("annotate_form")
        self.assertIn('id="percent_progress"', again)
        self.assertEqual(fields[PROCESS_FIELD], refields[PROCESS_FIELD])
        self.assertEqual(fields["annotate_followed"], refields["annotate_followed"])

    # -----------------------------------------------------------------------

    def test_the_help_while_it_goes(self):
        """The help is not shown while the run goes: the progress is."""
        main = self.perform()
        events = swappPageFields(main).fields_of("annotate_form")
        events["event_bake"] = "swapp_help"
        helped = main_of(self.recipe.bake(events))
        self.assertNotIn('id="swapp_help"', helped)
        self.assertIn('id="percent_progress"', helped)

    # -----------------------------------------------------------------------

    def test_nothing_else_starts_while_it_goes(self):
        """Let's go, Reset and another batch start nothing while a run goes, and it is said."""
        main = self.perform()
        for task in ("annotate_perform", "annotate_reset", "annotate_steps"):
            with self.subTest(task=task):
                events = swappPageFields(main).fields_of("annotate_form")
                events["event_bake"] = task
                self.recipe.bake(events)
                self.assertEqual(1, len(ManagerForTests.created))
                self.assertIn("nothing else can be started", self.recipe._data["main-content"])

    # -----------------------------------------------------------------------

    def test_the_old_event_of_the_progress_is_unknown(self):
        """Annotate has no event of its own for the progress any more."""
        self.recipe.bake({"event_name": "annotate_update"})
        self.assertEqual(205, self.recipe._status.code)

# ---------------------------------------------------------------------------


class TestSetupWhileItInstalls(unittest.TestCase):
    """The installation is modal: a page asked for while it goes has no action available."""

    def test_no_action_while_it_installs(self):
        """The actions are disabled, and the help is the way back."""
        recipe = swappSetupResponseRecipe()
        controller = recipe._swappSetupResponseRecipe__controller
        with mock.patch.object(controller, "is_installation_running", return_value=True):
            page = recipe.bake({})
            section = page[page.find('id="actions_section"'):]
            section = section[:section.find("</section>")]
            self.assertTrue(section.count("<button") > 0)
            self.assertEqual(section.count("<button"), section.count("disabled"))

            helped = recipe.bake({"event_bake": "swapp_help"})
            self.assertNotIn('id="swapp_help"', main_of(helped))

        page = recipe.bake({})
        section = page[page.find('id="actions_section"'):]
        section = section[:section.find("</section>")]
        self.assertTrue(section.count("<button") > section.count("disabled"))


if __name__ == "__main__":
    unittest.main()
