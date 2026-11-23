# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_annotate_provision.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the tie of the app of the annotations to the provision of files.

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

    TE30 and TE33 of the dossier "Annotate - an app of SPPAS": ModelProvision,
    against the neighbor. TE31 and TE32 are checked where the run calls the
    provision of files, in test_annotate_run.py.

"""

from __future__ import annotations
import unittest

from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from sppas.ui.swapp.services.files import swappFilesManager
from sppas.ui.swapp.services.files import swappWorkspaceFiles
from sppas.ui.swapp.app_annotate.annotate_provision import swappModelProvision

# ---------------------------------------------------------------------------


class TestModelProvision(unittest.TestCase):
    """TE30 and TE33. The provision of files, as the local server and the wsgi service give it."""

    def test_te30_the_batch_is_the_workspace_handed(self):
        """TE30. The workspace the provision of files hands, empty when nothing is checked. C11"""
        _workspace = swappWorkspaceFiles()
        _manager = swappFilesManager("annotate_files_panel", _workspace, reachable=True, has_workspace=False)
        _provision = swappModelProvision(_manager)

        _batch = _provision.batch()
        self.assertIsInstance(_batch, sppasWorkspace)
        self.assertEqual(0, len(_batch.get_filename_from_state(States().CHECKED)))

    # -----------------------------------------------------------------------

    @unittest.skip("Online only: it needs the wsgi service, the place it makes and its archive.")
    def test_te33_online_the_report_is_in_the_archive(self):
        """TE33. Online, the report is among what the archive holds. [803], C22"""


if __name__ == "__main__":
    unittest.main()
