# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_annotate_record.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of what one request of the app of the annotations holds.

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

    TE14 to TE17 of the dossier "Annotate - an app of SPPAS": what was decided.

"""

from __future__ import annotations
import os
import shutil
import tempfile
import unittest

from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from sppas.ui.swapp.app_annotate.annotate_record import swappAnnotateRecord

# ---------------------------------------------------------------------------


class TestWhatWasDecided(unittest.TestCase):
    """TE14 to TE17. A record parsed from what a page transmits."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_annotate_record_")

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def batch(self, checked: bool) -> sppasWorkspace:
        """Return a workspace of one file, checked or not."""
        _filename = os.path.join(self.folder, "sample.txt")
        with open(_filename, "w") as fp:
            fp.write("")
        _batch = sppasWorkspace()
        _batch.add_file(_filename)
        if checked is True:
            _batch.set_object_state(States().CHECKED)
        return _batch

    # -----------------------------------------------------------------------

    def test_te14_what_is_missing(self):
        """TE14. An annotation when none is selected, the batch when it is empty, and nothing otherwise. C12"""
        _record = swappAnnotateRecord()
        _record.parse(dict())
        self.assertEqual(["annotation", "batch"], _record.what_is_missing(self.batch(False)))
        self.assertEqual(["annotation"], _record.what_is_missing(self.batch(True)))

        _record.parse({"annotate_ann_textnorm": "True"})
        self.assertEqual(["batch"], _record.what_is_missing(self.batch(False)))
        self.assertEqual([], _record.what_is_missing(self.batch(True)))

    # -----------------------------------------------------------------------

    def test_te15_parsed_twice(self):
        """TE15. A record parsed twice gives the same decisions; nothing transmitted gives the defaults. C1, C24"""
        _first = swappAnnotateRecord()
        _first.parse({"annotate_ann_textnorm": "True", "annotate_merge": "True"})
        _second = swappAnnotateRecord()
        _second.parse(_first.serialize())
        self.assertEqual(_first.serialize(), _second.serialize())

        _empty = swappAnnotateRecord()
        _empty.parse(dict())
        self.assertEqual(swappAnnotateRecord().serialize(), _empty.serialize())
        self.assertEqual([], _empty.selected)

    # -----------------------------------------------------------------------

    def test_te16_selected_with_no_language(self):
        """TE16. An annotation transmitted as selected, with no language, is selected. C5"""
        _record = swappAnnotateRecord()
        _record.parse({"annotate_ann_textnorm": "True", "annotate_lang_textnorm": ""})
        self.assertEqual(["textnorm"], _record.selected)
        self.assertEqual("", _record.annotation_langs["textnorm"])

    # -----------------------------------------------------------------------

    def test_te17_selecting_selects_no_other(self):
        """TE17. Selecting an annotation which requires another selects that one only. C6"""
        _record = swappAnnotateRecord()
        _record.parse({"annotate_ann_alignment": "True"})
        self.assertEqual(["alignment"], _record.selected)


if __name__ == "__main__":
    unittest.main()
