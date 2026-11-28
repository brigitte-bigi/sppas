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

import json
import os
import re
import shutil
import tempfile
import time
import base64
import unittest
from unittest import mock

from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.services.deposit.deposit_settings import swappDepositSettings
from sppas.ui.swapp.services.deposit.deposit_space import swappDepositSpace
from sppas.ui.swapp.swapp_base.swapp_process import swappProcess
from sppas.ui.swapp.swapp_base.swapp_process import PROGRESS_EVENT
from sppas.ui.swapp.swapp_base.swapp_process import PROCESS_FIELD
from sppas.ui.swapp.app_annotate import annotate_run
from sppas.ui.swapp.app_annotate.annotate_maker import swappAnnotateResponseRecipe
from sppas.ui.swapp.app_annotate.annotate_panels import MSG_STEP_RUN
from sppas.ui.swapp.app_convert.convert_maker import swappConvertResponseRecipe
from sppas.ui.swapp.app_convert.convert_view import MSG_PROGRESS as MSG_CONVERSION
from sppas.ui.swapp.app_convert.convert_view import MSG_MISSING
from sppas.ui.swapp.app_dashboard.dashboard_maker import swappDashboardResponseRecipe
from sppas.ui.swapp.app_setup import setup_maker
from sppas.ui.swapp.app_setup import setup_model
from sppas.ui.swapp.app_setup.setup_maker import swappSetupResponseRecipe
from sppas.ui.swapp.app_setup.fieldset_install import INFO_INSTALL_FINISHED
from sppas.ui.swapp.app_setup.fieldset_install import MSG_COMPLETED

from tests.swapp.page_requests import swappPageFields
from tests.swapp.page_requests import main_of
from tests.swapp.page_requests import files_request
from tests.swapp.page_requests import with_container
from tests.swapp.test_annotate_run import ManagerForTests

# ---------------------------------------------------------------------------

# A TextGrid of one tier and one interval: what Convert converts.
TEXTGRID = ('File type = "ooTextFile"\nObject class = "TextGrid"\n\nxmin = 0\nxmax = 1\ntiers? <exists>\n'
            'size = 1\nitem []:\n    item [1]:\n        class = "IntervalTier"\n        name = "words"\n'
            '        xmin = 0\n        xmax = 1\n        intervals: size = 1\n        intervals [1]:\n'
            '            xmin = 0\n            xmax = 1\n            text = "hello"\n')

# ---------------------------------------------------------------------------


class InstallerForTests:
    """The installer, as Setup calls it, written here: it installs nothing.

    Installing sets on the progress it was given the feature it is
    installing, takes its time, and gives back the errors it is told.

    """

    seconds = 0.
    errors = list()

    def __init__(self):
        self.__enabled = dict()
        self.__progress = None

    def features_ids(self, feature_type: str) -> list:
        return ["feature_" + feature_type]

    def enable(self, feature_id: str, value=None) -> bool:
        if value is not None:
            self.__enabled[feature_id] = bool(value)
        return self.__enabled.get(feature_id, False)

    def brief(self, feature_id: str) -> str:
        return feature_id

    def description(self, feature_id: str) -> str:
        return feature_id

    def set_progress(self, progress) -> None:
        self.__progress = progress

    def install(self) -> list:
        self.__progress.set_header("feature_lang")
        self.__progress.update(50, "")
        time.sleep(InstallerForTests.seconds)
        return list(InstallerForTests.errors)

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

    def test_what_it_stands_at_is_written_in_the_log(self):
        """The header and the text it is given are written in the log, as a progress bar writes them."""
        with self.assertLogs(level="INFO") as logged:
            process = swappProcess.start(TestProcess.steps, (0.,))
            waited = 0.
            while process.read()[3] is False and waited < 2.:
                time.sleep(0.05)
                waited += 0.05
        self.assertIn("INFO:root:Step", logged.output)
        self.assertIn("INFO:root:  => Completed.", logged.output)

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
        self.page = self.recipe.bake({})
        # The files stand already where SPPAS reads them: the person designates
        # this one, as the page sends it.
        self.recipe.bake(files_request(self.recipe._data["container"], "designate", {"designate": self.source}))

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def convert(self) -> str:
        """Press Convert, the destination .eaf being chosen, as ConvertManager sends it."""
        events = with_container(swappPageFields(self.page).submitted("event_bake", "convert"),
                                self.recipe._data["container"])
        events["convert_destination"] = ".eaf"
        self.recipe.bake(events)
        return self.recipe._data["convert"]

    # -----------------------------------------------------------------------

    def test_the_page_names_the_process_and_the_report(self):
        """The section of the conversion shows the progress, and carries both names in the form."""
        section = self.convert()
        self.assertIn('id="percent_progress"', section)
        # The bar is named by what it measures, for a screen reader only.
        self.assertNotIn('for="percent_progress"', section)
        progress = re.search(r'<progress[^>]*>', section).group(0)
        self.assertIn('aria-label="' + MSG_CONVERSION + '"', progress)
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


class DepositSpaceForTests(swappDepositSpace):
    """The deposit space the provision of files creates, in the folder of a test."""

    settings = None

    def __init__(self):
        super(DepositSpaceForTests, self).__init__(DepositSpaceForTests.settings)

# ---------------------------------------------------------------------------


class TestConvertOnline(unittest.TestCase):
    """A conversion on the web service, as the page of Convert starts it, follows it and asks for its results."""

    def setUp(self):
        self.local = mock.patch.object(swapp_settings, "served_locally", False)
        self.local.start()
        DepositSpaceForTests.settings = swappDepositSettings()
        DepositSpaceForTests.settings.space = tempfile.mkdtemp(prefix="test_swapp_process_")
        self.space = mock.patch("sppas.ui.swapp.services.files.files_place.swappDepositSpace", DepositSpaceForTests)
        self.space.start()
        self.recipe = swappConvertResponseRecipe()

    def tearDown(self):
        self.space.stop()
        self.local.stop()
        shutil.rmtree(DepositSpaceForTests.settings.space, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_lets_go_without_any_file(self):
        """Without any file sent, Let's go starts nothing, and the answer says that the files are missing."""
        page = self.recipe.bake({})
        events = with_container(swappPageFields(page).submitted("event_bake", "convert"),
                                self.recipe._data["container"])
        self.recipe.bake(events)
        self.assertEqual(200, self.recipe._status.code)
        self.assertEqual(MSG_MISSING["batch"], self.recipe._data["info"])
        self.assertNotIn('id="percent_progress"', self.recipe._data["convert"])

    # -----------------------------------------------------------------------

    def test_the_results_of_a_conversion(self):
        """The file sent is converted, and the results are shown with the address of what was produced."""
        page = self.recipe.bake({})
        content = TEXTGRID.encode("utf-8")
        self.recipe.bake(files_request(self.recipe._data["container"], "designate",
                                       {"name": "sample.TextGrid", "size": str(len(content))}))
        self.recipe.bake(files_request(self.recipe._data["container"], "send",
                                       {"name": "sample.TextGrid",
                                        "content": base64.b64encode(content).decode("ascii")}))

        events = with_container(swappPageFields(page).submitted("event_bake", "convert"),
                                self.recipe._data["container"])
        events["convert_destination"] = ".eaf"
        self.recipe.bake(events)
        section = self.recipe._data["convert"]
        hidden = swappPageFields(section).hidden()
        answer, status = follow(self.recipe, hidden[PROCESS_FIELD])
        self.assertEqual(200, status)

        page = self.recipe._htree.serialize()
        events = swappPageFields(page).fields_of("convert_form")
        events["event_bake"] = "complete"
        self.recipe.bake(events)
        self.assertEqual(200, self.recipe._status.code)
        self.assertIn("sample.eaf", self.recipe._data["convert"])

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
        self.local = mock.patch.object(swapp_settings, "served_locally", True)
        self.local.start()
        self.recipe = swappAnnotateResponseRecipe()
        # The person designates the file in the panel of the files, as the page sends it.
        page = self.recipe.bake({})
        self.files = self.recipe.bake(swappPageFields(page).submitted("event_bake", "annotate_files"))
        self.recipe.bake(files_request(self.recipe._data["container"], "designate", {"designate": self.source}))

    def tearDown(self):
        while self.recipe.is_running() is True:
            time.sleep(0.05)
        self.local.stop()
        self.patcher.stop()
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def perform(self) -> str:
        """Select an annotation in the panel of its type, come back, and press Let's go, as the page sends them."""
        page = self.recipe.bake(with_container(swappPageFields(self.files).submitted("event_bake", "annotate_steps"),
                                               self.recipe._data["container"]))
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
        # The bar is named by what it measures, for a screen reader only.
        self.assertNotIn('for="percent_progress"', main)
        progress = re.search(r'<progress[^>]*>', main).group(0)
        self.assertIn('aria-label="' + MSG_STEP_RUN + '"', progress)
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


class TestSetupIsAProcess(unittest.TestCase):
    """An installation, as the page of Setup starts it and follows it; nothing is installed."""

    def setUp(self):
        InstallerForTests.seconds = 0.3
        InstallerForTests.errors = list()
        self.patchers = [mock.patch.object(setup_model, "sppasInstallerDeps", InstallerForTests),
                         mock.patch.object(setup_maker, "lgs")]
        for _patcher in self.patchers:
            _patcher.start()
        self.recipe = swappSetupResponseRecipe()
        self.recipe.bake({})
        self.model = self.recipe._swappSetupResponseRecipe__model

    def tearDown(self):
        while self.recipe.is_running() is True:
            time.sleep(0.05)
        for _patcher in self.patchers:
            _patcher.stop()

    # -----------------------------------------------------------------------

    def install(self) -> str:
        """Accept, then go forward as the page does until the installation starts.

        :return: (str) The fieldset of the installation the server answered

        """
        # The checkbox of what is accepted is clicked, as the page sends it.
        for _name in ("check_ref", "check_prod", "check_license"):
            if self.model.is_accepted(_name) is False:
                self.recipe.bake({"check_name": _name + "_input"})

        _index = 0
        while _index < 10:
            self.recipe.bake({"event_name": "next_fieldset", "event_value": str(_index)})
            for _written in json.loads(self.recipe.get_data()).values():
                if 'id="install_field"' in str(_written):
                    self.assertEqual(202, self.recipe._status.code)
                    return str(_written)
            _index += 1
        self.fail("The fieldset of the installation was never answered.")

    # -----------------------------------------------------------------------

    def test_the_fieldset_names_the_process(self):
        """The progress is shown, and the fieldset holds the name of the process."""
        installing = self.install()
        self.assertIn('id="percent_progress"', installing)
        self.assertIn('id="progress_header"', installing)
        self.assertIn('id="progress_text"', installing)
        # The bar is named by what it measures, for a screen reader only.
        self.assertNotIn("<label", installing)
        progress = re.search(r'<progress[^>]*>', installing).group(0)
        self.assertIn('aria-label="' + MSG_COMPLETED + '"', progress)
        self.assertTrue(swappPageFields(installing).hidden()[PROCESS_FIELD].endswith(".json"))
        self.assertTrue(self.recipe.is_running())

    # -----------------------------------------------------------------------

    def test_followed_until_the_completed_installation(self):
        """Where it stands is answered from the process; once ended, the completed installation is asked."""
        name = swappPageFields(self.install()).hidden()[PROCESS_FIELD]
        # The page asks again until the installer has set what it installs.
        answer, status = progress_of(self.recipe, name)
        waited = 0.
        while answer["header"] != "feature_lang" and waited < 2.:
            time.sleep(0.05)
            waited += 0.05
            answer, status = progress_of(self.recipe, name)
        self.assertEqual(202, status)
        self.assertEqual("feature_lang", answer["header"])

        answer, status = follow(self.recipe, name)
        self.assertEqual(200, status)
        self.assertFalse(self.recipe.is_running())

        # What the page submits once the process has ended.
        page = self.recipe.bake({"event_bake": "complete"})
        self.assertIn(INFO_INSTALL_FINISHED, page)
        self.assertNotIn('id="percent_progress"', page)
        self.assertNotIn('name="' + PROCESS_FIELD + '"', page)

    # -----------------------------------------------------------------------

    def test_a_page_asked_for_while_it_installs(self):
        """A page loaded again while the installation goes follows it: the same process."""
        name = swappPageFields(self.install()).hidden()[PROCESS_FIELD]
        again = self.recipe.bake({})
        self.assertIn('id="percent_progress"', again)
        self.assertEqual(name, swappPageFields(main_of(again)).hidden()[PROCESS_FIELD])

    # -----------------------------------------------------------------------

    def test_the_old_event_of_the_progress_is_unknown(self):
        """Setup has no event of its own for the progress any more."""
        self.recipe.bake({"event_name": "update"})
        self.assertEqual(401, self.recipe._status.code)

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
