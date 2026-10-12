# -*- coding: UTF-8 -*-
"""
:filename: tests.config.test_reports.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the logs of SPPAS runs.

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
import shutil
import tempfile
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from sppas.core.config.settings import sg
from sppas.core.coreutils.reports import sppasLogFile

# ---------------------------------------------------------------------------


class TestLogFile(unittest.TestCase):
    """The folder of the logs is a temporary one: nothing is written in the one of SPPAS."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test_reports_")
        self.logs = os.path.join(self.root, "logs")
        self.patcher = patch("sppas.core.coreutils.reports.paths", SimpleNamespace(logs=self.logs))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def expected(self, pattern, current, extension):
        """Return the filename a log is expected to have."""
        name = "{:s}_{:s}_{:s}_{:s}_{:04d}{:s}".format(
            sg.__name__, pattern, str(date.today()), str(os.getpid()), current, extension)
        return os.path.join(self.logs, name)

    # -----------------------------------------------------------------------

    def test_init_creates_the_folder_of_the_logs(self):
        self.assertFalse(os.path.exists(self.logs))
        sppasLogFile()
        self.assertTrue(os.path.isdir(self.logs))

    def test_init_creates_no_file(self):
        sppasLogFile()
        self.assertEqual(os.listdir(self.logs), [])

    def test_default_pattern_and_extension(self):
        log = sppasLogFile()
        self.assertEqual(log.get_filename(), self.expected("log", 1, ".txt"))

    def test_given_pattern(self):
        log = sppasLogFile(pattern="convert")
        self.assertEqual(log.get_filename(), self.expected("convert", 1, ".txt"))

    def test_given_extension(self):
        log = sppasLogFile(pattern="convert", extension=".json")
        self.assertEqual(log.get_filename(), self.expected("convert", 1, ".json"))

    def test_an_existing_log_is_not_overwritten(self):
        open(sppasLogFile().get_filename(), "w").close()
        open(sppasLogFile().get_filename(), "w").close()
        log = sppasLogFile()
        self.assertEqual(log.get_filename(), self.expected("log", 3, ".txt"))

    def test_a_log_of_another_extension_is_ignored(self):
        open(sppasLogFile().get_filename(), "w").close()
        log = sppasLogFile(extension=".json")
        self.assertEqual(log.get_filename(), self.expected("log", 1, ".json"))

    def test_a_log_of_another_pattern_is_ignored(self):
        open(sppasLogFile(pattern="convert").get_filename(), "w").close()
        log = sppasLogFile()
        self.assertEqual(log.get_filename(), self.expected("log", 1, ".txt"))

    def test_increment(self):
        log = sppasLogFile(extension=".json")
        log.increment()
        self.assertEqual(log.get_filename(), self.expected("log", 2, ".json"))
        log.increment()
        self.assertEqual(log.get_filename(), self.expected("log", 3, ".json"))

    def test_get_header(self):
        header = sppasLogFile.get_header()
        self.assertTrue(header.startswith("-" * 78))
        self.assertTrue(header.endswith("-" * 78 + "\n\n"))
        self.assertIn(" {:s} {:s}".format(sg.__name__, sg.__version__), header)
