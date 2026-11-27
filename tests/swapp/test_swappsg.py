"""
:filename: test_trace_store.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test the shared state and the notifications of swapp.

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

import json
import os
import tempfile
import unittest
from unittest import mock

from sppas.ui.agnostic import sppasCommKeys
from sppas.ui.swapp.main_settings import swappSettings

from sppas.ui.swapp.swapp_core.swappsg import swapp_notify
from sppas.ui.swapp.swapp_core.swappsg import notify_show_page

# ---------------------------------------------------------------------------


class TestNotifyShowPage(unittest.TestCase):
    """The request sent to the other UI to show one of its pages."""

    def setUp(self):
        self.received = list()
        swapp_notify.subscribe(self.__observer)

    def tearDown(self):
        swapp_notify.unsubscribe(self.__observer)

    def __observer(self, key, value):
        self.received.append((key, value))

    # -----------------------------------------------------------------------

    def test_notify(self):
        """The page name is published with the SHOW_PAGE key."""
        notify_show_page("page_annotate")
        self.assertEqual([(sppasCommKeys.SHOW_PAGE, "page_annotate")],
                         self.received)

    def test_notify_each_page(self):
        """Any page of the wx interface travels as it is."""
        pages = ("page_files", "page_annotate", "page_analyze",
                 "page_editor", "page_convert", "page_plugins")
        for page in pages:
            notify_show_page(page)
        self.assertEqual([(sppasCommKeys.SHOW_PAGE, p) for p in pages],
                         self.received)

    def test_notify_without_observer(self):
        """Without any observer, nothing happens and nothing raises."""
        swapp_notify.unsubscribe(self.__observer)
        notify_show_page("page_files")
        self.assertEqual(0, len(self.received))
        swapp_notify.subscribe(self.__observer)

# ---------------------------------------------------------------------------


class TestServedLocally(unittest.TestCase):
    """Whether swapp is served locally, read in the settings of swapp."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.filename = os.path.join(self.folder.name, ".webapp~")
        self.paths = mock.patch("sppas.ui.swapp.main_settings.paths")
        _paths = self.paths.start()
        _paths.ext_dir = self.folder.name

    def tearDown(self):
        self.paths.stop()
        self.folder.cleanup()

    # -----------------------------------------------------------------------

    def test_not_served_locally_by_default(self):
        """Without a file of settings, swapp is not served locally."""
        self.assertIs(False, swappSettings().served_locally)

    def test_not_served_locally_when_the_file_does_not_say_it(self):
        """A file of settings which does not hold the value leaves it False."""
        with open(self.filename, "w") as fd:
            json.dump({"license_agreement": True}, fd)
        self.assertIs(False, swappSettings().served_locally)

    def test_served_locally_when_the_file_says_it(self):
        """The value is the one of the file of settings."""
        with open(self.filename, "w") as fd:
            json.dump({"served_locally": True}, fd)
        self.assertIs(True, swappSettings().served_locally)

    def test_served_locally_is_saved(self):
        """The value is written in the file of settings, and read back."""
        settings = swappSettings()
        settings.served_locally = True
        settings.save()
        with open(self.filename, "r") as fd:
            self.assertIs(True, json.load(fd)["served_locally"])
        self.assertIs(True, swappSettings().served_locally)
