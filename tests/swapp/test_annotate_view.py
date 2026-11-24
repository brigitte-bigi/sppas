# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_annotate_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the page of the app of the annotations, as the server writes it.

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

    TE34 to TE38, TE40 to TE42 of the dossier "Annotate - an app of SPPAS": AnnotateView,
    the page as the server writes it. The page is the one the response bakes.

"""

from __future__ import annotations
import json
import os
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from sppas.core.config import annots
from sppas.src.annotations import sppasParam
from sppas.src.annotations.param import annotationParam

from sppas.ui.swapp.swapp_core.swappsg import swapp_serverstate
from sppas.ui.swapp.app_annotate.annotate_maker import swappAnnotateResponseRecipe
from sppas.ui.swapp.app_annotate.annotate_run import swappRootResult
from sppas.ui.swapp.app_annotate.annotate_record import swappAnnotateRecord

# ---------------------------------------------------------------------------


def tags_named(page: str, tag: str, prefix: str) -> list:
    """Return the tags of the page whose name begins with the given prefix."""
    return re.findall(r'<' + tag + r'\b[^>]*\bname="' + prefix + r'[^"]*"[^>]*>', page)


def keys_listed(page: str) -> list:
    """Return the keys of the annotations listed in a page of a type."""
    return re.findall(r'<input[^>]*\bname="annotate_ann_(\w+)"', page)


def errors_said(page: str) -> str:
    """Return what the dialog of the errors of the page holds."""
    _start = page.find('id="error_dialog"')
    return page[_start:page.find("</dialog>", _start)]

# ---------------------------------------------------------------------------


class TestAnnotateView(unittest.TestCase):
    """TE34 to TE38, TE40 to TE42. The page the response bakes."""

    def setUp(self):
        self.local = swapp_serverstate.local
        swapp_serverstate.local = True
        self.recipe = swappAnnotateResponseRecipe()
        self.folder = tempfile.mkdtemp(prefix="test_annotate_view_")

    def tearDown(self):
        swapp_serverstate.local = self.local
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te34_every_field_belongs_to_the_form(self):
        """TE34. The extensions, the languages, the selections, the merge option. C10"""
        _steps = self.recipe.bake(dict())
        _fields = tags_named(_steps, "select", "annotate_ext_")
        _fields.extend(tags_named(_steps, "select", "annotate_lang"))
        _fields.extend(tags_named(_steps, "input", "annotate_merge"))
        _list = self.recipe.bake({"event_bake": "annotate_annotations_STANDALONE"})
        _fields.extend(tags_named(_list, "input", "annotate_ann_"))
        _fields.extend(tags_named(_list, "select", "annotate_lang_"))

        self.assertGreater(len(_fields), 0)
        for _field in _fields:
            self.assertIn('form="annotate_form"', _field)

    # -----------------------------------------------------------------------

    def test_te35_one_list_per_type(self):
        """TE35. One list per type, and an annotation which has two types is in both. [301]"""
        _conf = {"id": "twotypes", "name": "Two types", "descr": "In two lists.", "api": "TestAnn",
                 "anntype": ["STANDALONE", "SPEAKER"], "options": [], "resources": []}
        _filename = os.path.join(self.folder, "twotypes.json")
        with open(_filename, "w") as fp:
            json.dump(_conf, fp)
        # The annotations the page lists are those of the model of the response.
        _model = self.recipe._swappAnnotateResponseRecipe__model
        _annotations = _model._swappAnnotateModel__annotations
        _annotations._swappModelAnnotations__parameters.annotations.append(annotationParam(_filename))

        _declared = sppasParam()
        for _type in annots.types:
            _expected = list()
            for i in range(_declared.get_step_numbers()):
                if _type in _declared.get_step(i).get_types():
                    _expected.append(_declared.get_step_key(i))
            if _type in ("STANDALONE", "SPEAKER"):
                _expected.append("twotypes")
            _page = self.recipe.bake({"event_bake": "annotate_annotations_" + _type})
            self.assertEqual(_expected, keys_listed(_page))

    # -----------------------------------------------------------------------

    def test_te36_an_annotation_which_is_not_installed(self):
        """TE36. It is in the page, disabled. C7"""
        def _test_step(parameters, step):
            return parameters.get_step_key(step) != "textnorm"

        with patch.object(sppasParam, "test_step", _test_step):
            _page = self.recipe.bake({"event_bake": "annotate_annotations_STANDALONE",
                                      "annotate_ann_textnorm": "True"})

        _switch = tags_named(_page, "input", "annotate_ann_textnorm")
        self.assertEqual(1, len(_switch))
        self.assertIn("disabled", _switch[0])
        self.assertNotIn("checked", _switch[0])

    # -----------------------------------------------------------------------

    def test_te37_online_the_reports_are_collapsed(self):
        """TE37. Online, the panel of the reports is collapsed and holds no report. C22"""
        swapp_serverstate.local = False
        _page = self.recipe.bake(dict())

        _panel = re.search(r'<section[^>]*id="annotate_reports_panel"[^>]*>', _page)
        self.assertIsNotNone(_panel)
        self.assertIn("hidden", _panel.group(0))
        self.assertEqual(0, len(tags_named(_page, "input", "annotate_report")))

    # -----------------------------------------------------------------------

    def test_te38_the_page_of_a_first_request(self):
        """TE38. No annotation selected, the button which performs disabled, the default extensions. [012]"""
        _page = self.recipe.bake(dict())

        self.assertEqual(0, len(re.findall(r'name="annotate_ann_\w+" value="True"', _page)))
        _perform = re.search(r'<button[^>]*value="annotate_perform"[^>]*>', _page)
        self.assertIn('aria-disabled="true"', _perform.group(0))

        _declared = sppasParam()
        _kinds = re.findall(r'<select[^>]*name="annotate_ext_(\w+)"[^>]*>(.*?)</select>', _page, re.S)
        self.assertGreater(len(_kinds), 0)
        for _kind, _options in _kinds:
            _selected = re.findall(r'<option value="([^"]*)" selected', _options)
            self.assertEqual([_declared.get_output_extension(_kind)], _selected)

    # -----------------------------------------------------------------------

    def test_te40_the_results_under_the_report(self):
        """TE40. The results under the report, one line per root, and no container of the provision of files. C25, T09"""
        _first = os.path.join(self.folder, "first")
        _second = os.path.join(self.folder, "second")
        # What came of the last run is what the run of the model of the response kept.
        _model = self.recipe._swappAnnotateResponseRecipe__model
        _run = _model._swappAnnotateModel__run
        _run._swappModelRun__results = [swappRootResult(_first, [_first + "-token.xra"]),
                                        swappRootResult(_second, list())]

        _page = self.recipe.bake({"event_bake": "annotate_complete", "annotate_followed": ""})

        _log = _page.find('id="annotate_log_panel"')
        _results = _page.find('id="annotate_results_h"')
        self.assertGreater(_log, -1)
        self.assertGreater(_results, _log)
        _body = re.search(r'<tbody>(.*?)</tbody>', _page[_results:], re.S).group(1)
        self.assertEqual(["first", "second"], re.findall(r'<th scope="row">\s*(\w+)\s*</th>', _body))
        self.assertIn("first-token.xra", _body)
        self.assertEqual(-1, _page.find('id="annotate_files_panel"'))

    # -----------------------------------------------------------------------

    def test_te41_a_report_which_cannot_be_read(self):
        """TE41. It is said in the dialog of the errors, with the reason. The error policy, level 3"""
        _page = self.recipe.bake({"event_bake": "annotate_show",
                                  "annotate_report": "no_report_bears_this_name.txt"})
        self.assertIn("The report is not available", errors_said(_page))

    # -----------------------------------------------------------------------

    def test_te42_a_run_which_cannot_be_started(self):
        """TE42. It is written in the log, and said in the dialog of the errors. The error policy, level 4"""
        _model = self.recipe._swappAnnotateResponseRecipe__model
        with patch.object(swappAnnotateRecord, "what_is_missing", return_value=list()), \
                patch.object(_model, "start", side_effect=OSError("The disk is full.")):
            with self.assertLogs(level="ERROR") as _logged:
                _page = self.recipe.bake({"event_bake": "annotate_perform", "annotate_ann_textnorm": "True"})

        self.assertIn("The disk is full.", " ".join(_logged.output))
        self.assertIn("The annotations could not be performed.", errors_said(_page))


if __name__ == "__main__":
    unittest.main()
