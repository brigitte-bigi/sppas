# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_annotate_run.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the run of the annotations, and of its tie to the provision of files.

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

    TE18 to TE24, TE31, TE32 and TE39 of the dossier "Annotate - an app of SPPAS":
    ModelRun, and what it calls the provision of files on. What runs the
    annotations is written here, as a thread: it writes a report, takes its
    time, and refuses one annotation when it is told to. No annotation of
    SPPAS is ever run. The reports are written in a folder made for each test.

"""

from __future__ import annotations
import os
import shutil
import tempfile
import time
import unittest
from threading import Thread
from unittest.mock import patch

from sppas.src.annotations import sppasParam
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from sppas.ui.swapp.app_annotate import annotate_run
from sppas.ui.swapp.app_annotate.annotate_run import swappModelRun
from sppas.ui.swapp.swapp_base.swapp_process import swappProcess

# ---------------------------------------------------------------------------


class ManagerForTests(Thread):
    """What runs the annotations, written here: it runs no annotation of SPPAS.

    As the API does: created with parameters, its thread runs them; created
    with nothing, annotate() runs them in the thread of its caller. Running
    them writes one line per activated annotation in the report, takes its
    time for each, and sets on the progress which annotation it is running.
    It adds to the workspace the files it is told it writes, as the API does,
    and says it wrote them.

    """

    seconds = 0.
    fails = ""
    created = list()
    writes = list()

    def __init__(self, parameters=None, progress=None, do_merge=False):
        Thread.__init__(self)
        self.parameters = None
        self.progress = None
        self.do_merge = do_merge
        self.activated = list()
        self.reached_the_end = False
        self.out_files = list()
        self.__given_parameters = parameters
        self.__given_progress = progress
        ManagerForTests.created.append(self)
        self.start()

    def get_out_files(self) -> list:
        return list(self.out_files)

    def run(self):
        if self.__given_parameters is not None:
            self.annotate(self.__given_parameters, self.__given_progress)

    def annotate(self, parameters, progress=None):
        self.parameters = parameters
        self.progress = progress
        self.activated = list()
        for i in range(parameters.get_step_numbers()):
            if parameters.get_step_status(i) is True:
                self.activated.append(parameters.get_step_key(i))
        with open(self.parameters.get_report_filename(), "w") as fp:
            for _key in self.activated:
                if self.progress is not None:
                    self.progress.set_header(_key)
                    self.progress.update(0)
                time.sleep(ManagerForTests.seconds)
                if _key == ManagerForTests.fails:
                    fp.write(_key + ": refused\n")
                else:
                    fp.write(_key + ": done\n")
        self.parameters.add_to_workspace(list(ManagerForTests.writes))
        self.out_files = list(ManagerForTests.writes)
        self.reached_the_end = True

# ---------------------------------------------------------------------------


class LogFileForTests:
    """Names the reports in the folder of a test, a new name each time."""

    folder = ""

    def __init__(self, pattern: str = "report"):
        self.__pattern = pattern
        self.__number = 1

    def get_filename(self) -> str:
        return os.path.join(LogFileForTests.folder, "{:s}_{:04d}.txt".format(self.__pattern, self.__number))

    def increment(self) -> None:
        self.__number += 1

# ---------------------------------------------------------------------------


class ProvisionForTests:
    """The provision of files, as the run calls it: what is locked, and what is given back."""

    def __init__(self):
        self.locked = list()
        self.given_back = 0
        self.finished_said = 0

    def lock(self, filenames: list) -> int:
        self.locked = list(filenames)
        return len(filenames)

    def release(self, filenames: list) -> int:
        for _name in filenames:
            self.locked.remove(_name)
        return len(filenames)

    def produced(self, workspace) -> dict:
        self.given_back += 1
        return dict()

    def finished(self) -> None:
        self.finished_said += 1

# ---------------------------------------------------------------------------


class TestWithARun(unittest.TestCase):
    """A run started by ModelRun, with the manager written here."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_annotate_run_")
        LogFileForTests.folder = self.folder
        ManagerForTests.seconds = 0.
        ManagerForTests.fails = ""
        ManagerForTests.created = list()
        ManagerForTests.writes = list()
        self.patchers = [patch.object(annotate_run, "sppasAnnotationsManager", ManagerForTests),
                         patch.object(annotate_run, "sppasLogFile", LogFileForTests)]
        for _patcher in self.patchers:
            _patcher.start()
        self.provision = ProvisionForTests()
        self.run_model = swappModelRun(self.provision)

    def tearDown(self):
        for _manager in ManagerForTests.created:
            _manager.join(5)
        for _patcher in self.patchers:
            _patcher.stop()
        shutil.rmtree(self.folder, ignore_errors=True)

    def batch(self) -> sppasWorkspace:
        """Return a workspace of one checked file."""
        _filename = os.path.join(self.folder, "sample.txt")
        with open(_filename, "w") as fp:
            fp.write("")
        _batch = sppasWorkspace()
        _batch.add_file(_filename)
        _batch.set_object_state(States().CHECKED)
        return _batch

    @staticmethod
    def parameters(keys: list) -> sppasParam:
        """Return what was decided: the annotations of the given keys selected."""
        _parameters = sppasParam()
        for _key in keys:
            _parameters.activate_step(_parameters.get_step_idx(_key))
        return _parameters

    def wait(self) -> None:
        """Wait until the run has ended."""
        while self.run_model.is_running() is True:
            time.sleep(0.02)

    # -----------------------------------------------------------------------

    def test_te18_starting_does_not_wait(self):
        """TE18. Starting answers before the run has ended, and the run goes on after the answer. RO5"""
        ManagerForTests.seconds = 0.2
        self.run_model.start(self.batch(), self.parameters(["textnorm"]), False)
        self.assertTrue(self.run_model.is_running())
        self.assertFalse(ManagerForTests.created[-1].reached_the_end)

        self.wait()
        self.assertTrue(ManagerForTests.created[-1].reached_the_end)

    # -----------------------------------------------------------------------

    def test_te19_a_second_start_is_refused(self):
        """TE19. A second start while one is going is refused. C13"""
        ManagerForTests.seconds = 0.2
        self.run_model.start(self.batch(), self.parameters(["textnorm"]), False)
        with self.assertRaises(RuntimeError):
            self.run_model.start(self.batch(), self.parameters(["textnorm"]), False)
        self.assertEqual(1, len(ManagerForTests.created))

    # -----------------------------------------------------------------------

    def test_te20_what_is_handed_over(self):
        """TE20. Every selected annotation activated, and no other. C6, C14"""
        self.run_model.start(self.batch(), self.parameters(["phonetize", "textnorm"]), True)
        self.wait()

        _manager = ManagerForTests.created[-1]
        self.assertEqual(sorted(["phonetize", "textnorm"]), sorted(_manager.activated))
        self.assertTrue(_manager.do_merge)

    # -----------------------------------------------------------------------

    def test_te21_decided_after_the_start(self):
        """TE21. What is decided after the start does not change what that run is performed with. C14"""
        ManagerForTests.seconds = 0.2
        _parameters = self.parameters(["textnorm"])
        self.run_model.start(self.batch(), _parameters, False)

        # The next request rebuilds what was decided in another object.
        self.parameters(["phonetize"])
        self.wait()

        _manager = ManagerForTests.created[-1]
        self.assertIs(_parameters, _manager.parameters)
        self.assertEqual(["textnorm"], _manager.activated)

    # -----------------------------------------------------------------------

    def test_te22_an_annotation_which_fails(self):
        """TE22. It stops nothing: the run reaches its end, and the report holds both. C16"""
        ManagerForTests.fails = "textnorm"
        _name = self.run_model.start(self.batch(), self.parameters(["textnorm", "phonetize"]), False)
        self.wait()

        with open(os.path.join(self.folder, _name), "r") as fp:
            _content = fp.read()
        self.assertIn("textnorm: refused", _content)
        self.assertIn("phonetize: done", _content)
        self.assertTrue(ManagerForTests.created[-1].reached_the_end)

    # -----------------------------------------------------------------------

    def test_te23_where_a_run_stands(self):
        """TE23. While a run goes, where it stands is what the API set, read in the file of its process; once it has ended, the hundred. C18"""
        self.assertEqual("", self.run_model.process_name())

        ManagerForTests.seconds = 0.3
        self.run_model.start(self.batch(), self.parameters(["textnorm"]), False)
        _process = swappProcess(self.run_model.process_name())
        time.sleep(0.1)
        _percent, _header, _text, _finished = _process.read()
        self.assertEqual(0, _percent)
        self.assertEqual("textnorm", _header)
        self.assertFalse(_finished)

        self.wait()
        _percent, _header, _text, _finished = _process.read()
        self.assertEqual(100, _percent)
        self.assertTrue(_finished)

    # -----------------------------------------------------------------------

    def test_te24_two_runs_two_reports(self):
        """TE24. Two runs write two reports, and the second one replaces nothing of the first. C17"""
        _first = self.run_model.start(self.batch(), self.parameters(["textnorm"]), False)
        self.wait()
        with open(os.path.join(self.folder, _first), "r") as fp:
            _content = fp.read()

        _second = self.run_model.start(self.batch(), self.parameters(["phonetize"]), False)
        self.wait()

        self.assertNotEqual(_first, _second)
        with open(os.path.join(self.folder, _first), "r") as fp:
            self.assertEqual(_content, fp.read())
        self.assertTrue(os.path.exists(os.path.join(self.folder, _second)))

    # -----------------------------------------------------------------------

    def test_te31_the_batch_is_locked_while_the_run_goes(self):
        """TE31. The files of the batch are locked while the annotations are performed, and none afterward. T08"""
        ManagerForTests.seconds = 0.2
        self.run_model.start(self.batch(), self.parameters(["textnorm"]), False)
        self.assertEqual(1, len(self.provision.locked))

        self.wait()
        self.assertEqual(0, len(self.provision.locked))

    # -----------------------------------------------------------------------

    def test_te32_what_was_produced_is_given_back_once(self):
        """TE32. Once, when the annotations have been performed, and not at each of them. T09"""
        ManagerForTests.seconds = 0.1
        self.run_model.start(self.batch(), self.parameters(["textnorm", "phonetize"]), False)
        self.assertEqual(0, self.provision.given_back)

        self.wait()
        self.run_model.is_running()
        self.assertEqual(1, self.provision.given_back)
        self.assertEqual(1, self.provision.finished_said)

    # -----------------------------------------------------------------------

    def test_te39_one_result_per_root(self):
        """TE39. One result per root of the batch, in its order: written with what the API wrote under it, a file of the batch written again included, or refused. C25"""
        _batch = sppasWorkspace()
        for _name in ("first.txt", "first-token.xra", "second.wav", "second.txt", "third.txt"):
            _filename = os.path.join(self.folder, _name)
            with open(_filename, "w") as fp:
                fp.write("")
            _batch.add_file(_filename)
        _batch.set_object_state(States().CHECKED)
        _first = os.path.join(self.folder, "first")
        _second = os.path.join(self.folder, "second")
        _third = os.path.join(self.folder, "third")
        # What the run writes: a file the batch held already, and two new ones.
        ManagerForTests.writes = [_first + "-token.xra", _third + "-token.xra", _third + "-phon.xra"]
        for _name in ManagerForTests.writes:
            with open(_name, "w") as fp:
                fp.write("")

        ManagerForTests.seconds = 0.1
        self.run_model.start(_batch, self.parameters(["textnorm"]), False)
        self.assertEqual([], self.run_model.results())
        self.wait()

        _results = self.run_model.results()
        _roots = list()
        _statuses = list()
        for _result in _results:
            _roots.append(_result.root)
            _statuses.append(_result.status)
        self.assertEqual([_first, _second, _third], _roots)
        self.assertEqual(["written", "refused", "written"], _statuses)
        self.assertEqual([_first + "-token.xra"], _results[0].produced)
        self.assertEqual([], _results[1].produced)
        self.assertEqual(sorted([_third + "-token.xra", _third + "-phon.xra"]), sorted(_results[2].produced))


if __name__ == "__main__":
    unittest.main()
