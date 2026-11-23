# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_annotate_reports.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the reports of the app which runs the automatic annotations.

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

    TE25 to TE29 of the dossier "Annotate - an app of SPPAS": ModelReports,
    with a disk. The folder of the logs is a folder made for each test.

"""

from __future__ import annotations
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from sppas.ui.swapp.app_annotate import annotate_reports
from sppas.ui.swapp.app_annotate.annotate_reports import swappModelReports
from sppas.ui.swapp.app_annotate.annotate_reports import REPORT_STATES

# ---------------------------------------------------------------------------


class PathsForTests:
    """The paths of SPPAS, where the folder of the logs is the one of a test."""

    logs = ""

# ---------------------------------------------------------------------------


def write_file(folder: str, name: str, lines: list) -> None:
    """Write a file of the given lines in a folder."""
    with open(os.path.join(folder, name), "w") as fp:
        for _line in lines:
            fp.write(_line + "\n")

# ---------------------------------------------------------------------------


class TestModelReports(unittest.TestCase):
    """TE25 to TE29. The reports of a folder of logs made for each test."""

    def setUp(self):
        self.logs = tempfile.mkdtemp(prefix="test_annotate_reports_")
        PathsForTests.logs = self.logs
        self.patcher = patch.object(annotate_reports, "paths", PathsForTests)
        self.patcher.start()
        self.reports = swappModelReports()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.logs, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te25_the_reports_of_the_folder(self):
        """TE25. The text files whose name holds report, and no other file of the folder. [701]"""
        write_file(self.logs, "sppas_report_0001.txt", ["one"])
        write_file(self.logs, "report_of_a_run.txt", ["two"])
        write_file(self.logs, "something.txt", ["three"])
        write_file(self.logs, "report.log", ["four"])
        os.mkdir(os.path.join(self.logs, "report_folder.txt"))

        self.assertEqual(sorted(["sppas_report_0001.txt", "report_of_a_run.txt"]),
                         sorted(self.reports.reports()))

    # -----------------------------------------------------------------------

    def test_te26_the_state_of_a_line(self):
        """TE26. A line which states a result bears its state, for each of the five; another bears none. C19"""
        _lines = list()
        for _state, _word in REPORT_STATES:
            _lines.append("[ " + _word + " ] The result of a file.")
        _lines.append("A line which states no result.")
        write_file(self.logs, "sppas_report_0001.txt", _lines)

        _read = self.reports.read("sppas_report_0001.txt")
        self.assertEqual(len(_lines), len(_read))
        for i in range(len(REPORT_STATES)):
            self.assertEqual(REPORT_STATES[i][0], _read[i].state)
            self.assertEqual(_lines[i], _read[i].text)
        self.assertEqual("", _read[-1].state)

    # -----------------------------------------------------------------------

    def test_te27_a_report_which_is_not_there(self):
        """TE27. It is said so, and nothing is given in its place. [604]"""
        with self.assertRaises(ValueError):
            self.reports.read("sppas_report_0001.txt")

    # -----------------------------------------------------------------------

    def test_te28_deleting_reports(self):
        """TE28. Those which were named are deleted, and no other file. C21"""
        write_file(self.logs, "sppas_report_0001.txt", ["one"])
        write_file(self.logs, "sppas_report_0002.txt", ["two"])
        write_file(self.logs, "something.txt", ["three"])

        _left = self.reports.delete(["sppas_report_0001.txt"])

        self.assertEqual(0, len(_left))
        self.assertFalse(os.path.exists(os.path.join(self.logs, "sppas_report_0001.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.logs, "sppas_report_0002.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.logs, "something.txt")))

    # -----------------------------------------------------------------------

    def test_te29_a_report_which_cannot_be_deleted(self):
        """TE29. It does not keep the others from being, and its name is given back. T11"""
        write_file(self.logs, "sppas_report_0001.txt", ["one"])
        write_file(self.logs, "something.txt", ["three"])

        _left = self.reports.delete(["something.txt", "sppas_report_0001.txt"])

        self.assertEqual(["something.txt"], list(_left.keys()))
        self.assertFalse(os.path.exists(os.path.join(self.logs, "sppas_report_0001.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.logs, "something.txt")))


if __name__ == "__main__":
    unittest.main()
