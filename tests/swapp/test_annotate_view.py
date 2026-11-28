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

    TE34 to TE38, TE40 to TE42, TE44, TE46, TE48 to TE50 of the dossier "Annotate - an app of SPPAS":
    AnnotateView, the page as the server writes it. The page is the one the response bakes.

"""

from __future__ import annotations
import base64
import io
import json
import os
import re
import shutil
import tempfile
import time
import unittest
import zipfile
from unittest.mock import patch

import sppas.src.annotations
from sppas.core.config import annots
from sppas.core.coreutils import sppasEnableFeatureError
from sppas.src.annotations import sppasParam
from sppas.src.annotations.param import annotationParam

from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.swapp_base import swapp_process
from sppas.ui.swapp.swapp_base.swapp_process import PROCESS_FIELD
from sppas.ui.swapp.services.deposit.deposit_settings import swappDepositSettings
from sppas.ui.swapp.services.deposit.deposit_space import swappDepositSpace
from sppas.ui.swapp.app_annotate import annotate_model
from sppas.ui.swapp.app_annotate import annotate_reports
from sppas.ui.swapp.app_annotate import annotate_run
from sppas.ui.swapp.app_annotate.annotate_maker import swappAnnotateResponseRecipe
from sppas.ui.swapp.app_annotate.annotate_record import swappAnnotateRecord
from sppas.ui.swapp.app_annotate.annotate_view import MSG_GOING

from tests.swapp.page_requests import swappPageFields
from tests.swapp.page_requests import files_request
from tests.swapp.page_requests import with_container
from tests.swapp.test_annotate_run import ManagerForTests
from tests.swapp.test_annotate_run import LogFileForTests
from tests.swapp.test_annotate_reports import PathsForTests
from tests.swapp.test_swapp_process import TEXTGRID
from tests.swapp.test_swapp_process import follow

# ---------------------------------------------------------------------------


def tags_named(page: str, tag: str, prefix: str) -> list:
    """Return the tags of the page whose name begins with the given prefix."""
    return re.findall(r'<' + tag + r'\b[^>]*\bname="' + prefix + r'[^"]*"[^>]*>', page)


def keys_listed(page: str) -> list:
    """Return the keys of the annotations listed in a page of a type."""
    return re.findall(r'<input[^>]*\bname="annotate_ann_(\w+)"', page)


class NotEnabledForTests:
    """The class the package imports for an annotation whose feature is not enabled."""

    def __init__(self, *args, **kwargs):
        raise sppasEnableFeatureError("feature_for_tests")


class DepositSpaceForTests(swappDepositSpace):
    """The deposit space the provision of files creates, in the folder of a test."""

    settings = None

    def __init__(self):
        super(DepositSpaceForTests, self).__init__(DepositSpaceForTests.settings)

# ---------------------------------------------------------------------------


def item_of(page: str, key: str) -> str:
    """Return the item of the list of annotations which holds the annotation of that key."""
    _at = page.find('id="annotate_ann_' + key + '"')
    return page[page.rfind("<li", 0, _at):page.find("</li>", _at)]


def errors_said(page: str) -> str:
    """Return what the dialog of the errors of the page holds."""
    _start = page.find('id="error_dialog"')
    return page[_start:page.find("</dialog>", _start)]

# ---------------------------------------------------------------------------


class TestAnnotateView(unittest.TestCase):
    """TE34 to TE38, TE40 to TE42, TE44, TE46, TE48, TE50, TE51. The page the response bakes."""

    def setUp(self):
        self.local = swapp_settings.served_locally
        swapp_settings.served_locally = True
        # The reports are written and read in a folder of logs made for the test.
        self.logs = tempfile.mkdtemp(prefix="test_annotate_view_")
        PathsForTests.logs = self.logs
        LogFileForTests.folder = self.logs
        self.patchers = [patch.object(annotate_model, "paths", PathsForTests),
                         patch.object(annotate_reports, "paths", PathsForTests),
                         patch.object(annotate_run, "paths", PathsForTests),
                         patch.object(swapp_process, "paths", PathsForTests),
                         patch.object(annotate_run, "sppasLogFile", LogFileForTests),
                         patch.object(annotate_run, "sppasAnnotationsManager", ManagerForTests)]
        for _patcher in self.patchers:
            _patcher.start()
        ManagerForTests.seconds = 0.
        ManagerForTests.fails = ""
        ManagerForTests.created = list()
        ManagerForTests.writes = list()
        self.recipe = swappAnnotateResponseRecipe()
        self.folder = tempfile.mkdtemp(prefix="test_annotate_view_")

    def tearDown(self):
        while self.recipe.is_running() is True:
            time.sleep(0.05)
        for _patcher in self.patchers:
            _patcher.stop()
        swapp_settings.served_locally = self.local
        shutil.rmtree(self.folder, ignore_errors=True)
        shutil.rmtree(self.logs, ignore_errors=True)

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

    def test_te51_applying_and_closing_the_options_of_an_annotation(self):
        """TE51. Applying the options of an annotation selects it; closing them without applying unselects it,
        and its options hold what they held. [309]

        """
        _page = self.recipe.bake({"event_bake": "annotate_annotations_STANDALONE"})
        _fields = swappPageFields(_page).fields_of("annotate_form")
        self.assertNotIn("annotate_ann_textnorm", _fields)

        # Configure... answers the options of the annotation, with what the
        # page writes of it.
        self.recipe.bake(swappPageFields(_page).submitted("event_bake", "annotate_options_textnorm"))
        _container = self.recipe._data["options"]
        self.assertEqual("False", self.recipe._data["values"]["annotate_ann_textnorm"])

        # Applied while it is not selected: it is selected.
        _applied = dict(_fields)
        _applied.update(swappPageFields(_container).fields_of("#form1"))
        _applied["options_validate"] = ""
        _applied["event_bake"] = "annotate_options_textnorm"
        self.recipe.bake(_applied)
        _values = self.recipe._data["values"]
        self.assertEqual("True", _values["annotate_ann_textnorm"])

        # Given up while it is selected: it is not selected, and its options
        # hold what they held.
        _fields.update(_values)
        _fields["event_bake"] = "annotate_options_textnorm"
        _fields["options_close"] = ""
        self.recipe.bake(_fields)
        _closed = self.recipe._data["values"]
        self.assertEqual("False", _closed["annotate_ann_textnorm"])
        for _name in _values:
            if _name != "annotate_ann_textnorm":
                self.assertEqual(_values[_name], _closed[_name])

    # -----------------------------------------------------------------------

    def test_te36_an_annotation_which_is_not_installed(self):
        """TE36. It is in the page, disabled. C7"""
        _declared = sppasParam()
        _api = _declared.get_step(_declared.get_step_idx("textnorm")).get_api()
        with patch.object(sppas.src.annotations, _api, NotEnabledForTests):
            _page = self.recipe.bake({"event_bake": "annotate_annotations_STANDALONE",
                                      "annotate_ann_textnorm": "True"})

        _switch = tags_named(_page, "input", "annotate_ann_textnorm")
        self.assertEqual(1, len(_switch))
        self.assertIn("disabled", _switch[0])
        self.assertNotIn("checked", _switch[0])

    # -----------------------------------------------------------------------

    def test_te37_online_the_reports_are_collapsed(self):
        """TE37. Online, the panel of the reports is collapsed and holds no report. C22"""
        swapp_settings.served_locally = False
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
        self.assertIsNotNone(re.search(r'(?<![\w-])disabled\b', _perform.group(0)))
        self.assertNotIn("aria-disabled", _perform.group(0))

        _declared = sppasParam()
        _kinds = re.findall(r'<select[^>]*name="annotate_ext_(\w+)"[^>]*>(.*?)</select>', _page, re.S)
        self.assertGreater(len(_kinds), 0)
        for _kind, _options in _kinds:
            _selected = re.findall(r'<option value="([^"]*)" selected', _options)
            self.assertEqual([_declared.get_output_extension(_kind)], _selected)

    # -----------------------------------------------------------------------

    def designate(self, names: list) -> str:
        """Open the panel of the files, and designate the given files there, as the page sends them.

        :param names: (list of str) Names of the files, with their path
        :return: (str) The page of the panel of the files

        """
        _page = self.recipe.bake({})
        _files = self.recipe.bake(swappPageFields(_page).submitted("event_bake", "annotate_files"))
        for _name in names:
            self.recipe.bake(files_request(self.recipe._data["container"], "designate", {"designate": _name}))
        return _files

    # -----------------------------------------------------------------------

    def perform(self, files: str) -> str:
        """Come back to the six steps, select an annotation in the panel of its type, and press Let's go.

        The first request is sent from the panel of the files, whose container
        is the one the server answered last.

        :param files: (str) The page of the panel of the files
        :return: (str) The main content the server answered

        """
        _steps = self.recipe.bake(with_container(swappPageFields(files).submitted("event_bake", "annotate_steps"),
                                                 self.recipe._data["container"]))
        _annotations = self.recipe.bake(swappPageFields(_steps).submitted("event_bake",
                                                                          "annotate_annotations_STANDALONE"))
        _events = swappPageFields(_annotations).submitted("event_bake", "annotate_steps")
        _events["annotate_ann_textnorm"] = "True"
        _steps = self.recipe.bake(_events)
        self.recipe.bake(swappPageFields(_steps).submitted("event_bake", "annotate_perform"))
        return self.recipe._data["main-content"]

    # -----------------------------------------------------------------------

    def test_te40_the_results_under_the_report(self):
        """TE40. The results under the report, one line per root, and no container of the provision of files. C25, T09"""
        # A batch of two roots, and what the run writes under the first one.
        _names = list()
        for _name in ("first.txt", "second.txt", "first-token.xra"):
            _filename = os.path.join(self.folder, _name)
            with open(_filename, "w") as fp:
                fp.write("")
            _names.append(_filename)
        _files = self.designate(_names[:2])
        ManagerForTests.writes = [_names[2]]

        # The annotation is selected in the panel of its type, then Let's go is pressed.
        _main = self.perform(_files)

        # The run is followed until it has ended, then the results are asked with the form.
        _form = swappPageFields(_main).fields_of("annotate_form")
        _answer, _status = follow(self.recipe, _form[PROCESS_FIELD])
        self.assertEqual(200, _status)
        _events = swappPageFields(_main).fields_of("annotate_form")
        _events["event_bake"] = "annotate_complete"
        _page = self.recipe.bake(_events)

        _log = _page.find('id="annotate_log_panel"')
        _results = _page.find('id="annotate_results_h"')
        self.assertGreater(_log, -1)
        self.assertGreater(_results, _log)
        _body = re.search(r'<tbody>(.*?)</tbody>', _page[_results:], re.S).group(1)
        self.assertEqual(["first", "second"], re.findall(r'<th scope="row">\s*(\w+)\s*</th>', _body))
        self.assertIn("first-token.xra", _body)
        self.assertEqual(-1, _page.find('id="annotate_files_panel"'))

    # -----------------------------------------------------------------------

    def test_te53_whatever_the_process_which_answers(self):
        """TE53. The files designated with one process of the server are the batch another one runs, and the first one gives the results: the page transmits everything. RO9, C24"""
        _names = list()
        for _name in ("first.txt", "first-token.xra"):
            _filename = os.path.join(self.folder, _name)
            with open(_filename, "w") as fp:
                fp.write("")
            _names.append(_filename)
        _files = self.designate(_names[:1])
        _container = self.recipe._data["container"]
        ManagerForTests.writes = [_names[1]]

        # Another process of the server has its own recipe of the same page,
        # which answered nothing before: it answers Let's go.
        _other = swappAnnotateResponseRecipe()
        _steps = _other.bake(with_container(swappPageFields(_files).submitted("event_bake", "annotate_steps"),
                                            _container))
        _annotations = _other.bake(swappPageFields(_steps).submitted("event_bake",
                                                                     "annotate_annotations_STANDALONE"))
        _events = swappPageFields(_annotations).submitted("event_bake", "annotate_steps")
        _events["annotate_ann_textnorm"] = "True"
        _steps = _other.bake(_events)
        _other.bake(swappPageFields(_steps).submitted("event_bake", "annotate_perform"))
        _main = _other._data["main-content"]
        self.assertIn('id="percent_progress"', _main)
        self.assertEqual(1, len(ManagerForTests.created))

        # The first process follows the run, then answers the results.
        _form = swappPageFields(_main).fields_of("annotate_form")
        _answer, _status = follow(self.recipe, _form[PROCESS_FIELD])
        self.assertEqual(200, _status)
        _events = dict(_form)
        _events["event_bake"] = "annotate_complete"
        _page = self.recipe.bake(_events)

        _results = _page.find('id="annotate_results_h"')
        self.assertGreater(_results, -1)
        _body = re.search(r'<tbody>(.*?)</tbody>', _page[_results:], re.S).group(1)
        self.assertEqual(["first"], re.findall(r'<th scope="row">\s*(\w+)\s*</th>', _body))
        self.assertIn("first-token.xra", _body)

    # -----------------------------------------------------------------------

    def test_a_value_holding_quotes_is_carried_whole(self):
        """A value the form carries hidden comes back as it was given, its quotes and its ampersand included."""
        _given = 'Say "hello" & go'
        _page = self.recipe.bake({"event_bake": "annotate_steps", "annotate_opt_speechtotext_prompt": _given})

        _fields = swappPageFields(_page).fields_of("annotate_form")
        self.assertEqual(_given, _fields["annotate_opt_speechtotext_prompt"])

    # -----------------------------------------------------------------------

    def test_te19_a_second_start_is_refused(self):
        """TE19. A second start while one is going is refused, and it is said: the page transmits the process of the run it follows. C13"""
        _names = list()
        for _name in ("first.txt", "second.txt"):
            _filename = os.path.join(self.folder, _name)
            with open(_filename, "w") as fp:
                fp.write("")
            _names.append(_filename)
        _files = self.designate(_names)
        ManagerForTests.seconds = 0.3

        _main = self.perform(_files)
        _form = swappPageFields(_main).fields_of("annotate_form")

        # The same form, sent again while the run goes.
        _events = dict(_form)
        _events["event_bake"] = "annotate_perform"
        _again = self.recipe.bake(_events)
        self.assertEqual(1, len(ManagerForTests.created))
        self.assertIn(MSG_GOING, _again)

        _answer, _status = follow(self.recipe, _form[PROCESS_FIELD])
        self.assertEqual(200, _status)

    # -----------------------------------------------------------------------

    def test_te41_a_report_which_cannot_be_read(self):
        """TE41. It is said in the dialog of the errors, with the reason. The error policy, level 3"""
        _name = "sppas_report_0001.txt"
        with open(os.path.join(self.logs, _name), "wb") as fp:
            fp.write(b"\xff\xfe is not a text")

        # The report is listed, and the person checks it: checking makes no request.
        _page = self.recipe.bake({})
        self.assertIsNotNone(re.search(r'<input(?=[^>]*name="annotate_report")(?=[^>]*value="' + re.escape(_name) + r'")',
                                       _page))
        _events = swappPageFields(_page).submitted("event_bake", "annotate_show")
        _events["annotate_report"] = _name
        _page = self.recipe.bake(_events)
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

    # -----------------------------------------------------------------------

    def test_te44_what_an_annotation_requires_in_the_list(self):
        """TE44. After the files it reads, by its name; nothing for one which requires none. [307]"""
        _declared = sppasParam()
        _name = _declared.get_step_name(_declared.get_step_idx("textnorm"))
        _page = self.recipe.bake({"event_bake": "annotate_annotations_STANDALONE"})

        _item = item_of(_page, "phonetize")
        _found = re.search(r"<dt>\s*Required annotation\s*</dt>\s*<dd>\s*" + re.escape(_name) + r"\s*</dd>", _item)
        self.assertIsNotNone(_found)
        _requires = _found.start()
        self.assertLess(_item.find("Required files"), _requires)
        self.assertEqual(-1, item_of(_page, "textnorm").find("Required annotation"))

    # -----------------------------------------------------------------------

    def test_te46_the_files_an_annotation_reads_in_the_list(self):
        """TE46. Every installed annotation, after its description, each name once. [307]"""
        _declared = sppasParam()
        _page = self.recipe.bake({"event_bake": "annotate_annotations_STANDALONE"})

        _item = item_of(_page, "alignment")
        _found = re.search(r"<dt>\s*Required files\s*</dt>\s*<dd>\s*audio, annotated file\s*</dd>", _item)
        self.assertIsNotNone(_found)
        _files = _found.start()
        _descr = _declared.get_step_descr(_declared.get_step_idx("alignment")).strip()[:20]
        self.assertLess(_item.find(_descr), _files)
        self.assertIsNotNone(re.search(r"<dt>\s*Required files\s*</dt>\s*<dd>\s*annotated file\s*</dd>",
                                       item_of(_page, "textnorm")))
        for _key in keys_listed(_page):
            _item = item_of(_page, _key)
            if _item.find('class="annotate-missing"') == -1:
                self.assertGreater(_item.find("Required files"), -1, _key)

    # -----------------------------------------------------------------------

    def test_te48_why_an_annotation_is_not_installed_in_the_list(self):
        """TE48. Said in place of what it requires; the others say what they require. C7"""
        _declared = sppasParam()
        _api = _declared.get_step(_declared.get_step_idx("textnorm")).get_api()
        with patch.object(sppas.src.annotations, _api, NotEnabledForTests):
            _page = self.recipe.bake({"event_bake": "annotate_annotations_STANDALONE"})

        _item = item_of(_page, "textnorm")
        self.assertIsNotNone(re.search(r'<p class="annotate-missing">[^<]*feature_for_tests', _item))
        self.assertEqual(-1, _item.find("Required files"))
        self.assertGreater(item_of(_page, "phonetize").find("Required files"), -1)

    # -----------------------------------------------------------------------

    def test_te50_locally_no_type_is_disabled(self):
        """TE50. Locally, no button of a type is disabled. [311], C27"""
        _fields = swappPageFields(self.recipe.bake({}))
        for _type in ("STANDALONE", "SPEAKER", "INTERACTION"):
            _button = _fields.button("annotate_type_" + _type)
            self.assertEqual("annotate_annotations_" + _type, _button["value"])
            self.assertNotIn("disabled", _button)

# ---------------------------------------------------------------------------


class TestAnnotateOnline(unittest.TestCase):
    """TE49, TE50. Online, as the page sends it: the files are sent, and no annotation of SPPAS is run."""

    def setUp(self):
        self.local = patch.object(swapp_settings, "served_locally", False)
        self.local.start()
        DepositSpaceForTests.settings = swappDepositSettings()
        DepositSpaceForTests.settings.space = tempfile.mkdtemp(prefix="test_annotate_view_")
        self.space = patch("sppas.ui.swapp.services.files.files_place.swappDepositSpace", DepositSpaceForTests)
        self.space.start()
        ManagerForTests.seconds = 0.
        ManagerForTests.fails = ""
        ManagerForTests.created = list()
        ManagerForTests.writes = list()
        self.manager = patch.object(annotate_run, "sppasAnnotationsManager", ManagerForTests)
        self.manager.start()
        self.recipe = swappAnnotateResponseRecipe()

    def tearDown(self):
        while self.recipe.is_running() is True:
            time.sleep(0.05)
        self.manager.stop()
        self.space.stop()
        self.local.stop()
        shutil.rmtree(DepositSpaceForTests.settings.space, ignore_errors=True)

    # -----------------------------------------------------------------------

    def send(self) -> str:
        """Open the panel of the files, designate a TextGrid and send it, as the page sends them.

        :return: (str) The page of the panel of the files

        """
        _page = self.recipe.bake({})
        _files = self.recipe.bake(swappPageFields(_page).submitted("event_bake", "annotate_files"))
        _content = TEXTGRID.encode("utf-8")
        self.recipe.bake(files_request(self.recipe._data["container"], "designate",
                                       {"name": "sample.TextGrid", "size": str(len(_content))}))
        self.recipe.bake(files_request(self.recipe._data["container"], "send",
                                       {"name": "sample.TextGrid",
                                        "content": base64.b64encode(_content).decode("ascii")}))
        return _files

    # -----------------------------------------------------------------------

    def perform(self, files: str) -> str:
        """Come back to the six steps, select an annotation in the panel of its type, and press Let's go.

        :param files: (str) The page of the panel of the files
        :return: (str) The main content the server answered

        """
        _steps = self.recipe.bake(with_container(swappPageFields(files).submitted("event_bake", "annotate_steps"),
                                                 self.recipe._data["container"]))
        _annotations = self.recipe.bake(swappPageFields(_steps).submitted("event_bake",
                                                                          "annotate_annotations_STANDALONE"))
        _events = swappPageFields(_annotations).submitted("event_bake", "annotate_steps")
        _events["annotate_ann_textnorm"] = "True"
        _steps = self.recipe.bake(_events)
        self.recipe.bake(swappPageFields(_steps).submitted("event_bake", "annotate_perform"))
        return self.recipe._data["main-content"]

    # -----------------------------------------------------------------------

    def test_te49_online_the_report_of_the_run(self):
        """TE49. Once performed, the report is read, downloaded on its own, and in the archive. [601], [605], [803]"""
        _files = self.send()
        _provision = self.recipe._swappAnnotateResponseRecipe__manager
        _folder = _provision.files_for_app().get_paths()[0].get_id()
        _produced = os.path.join(_folder, "sample-token.xra")
        with open(_produced, "w") as fp:
            fp.write("")
        ManagerForTests.writes = [_produced]

        _main = self.perform(_files)
        _form = swappPageFields(_main).fields_of("annotate_form")
        _report = _form["annotate_followed"]
        self.assertTrue(len(_report) > 0)
        _answer, _status = follow(self.recipe, _form[PROCESS_FIELD])
        self.assertEqual(200, _status)

        _events = swappPageFields(_main).fields_of("annotate_form")
        _events["event_bake"] = "annotate_complete"
        self.recipe.bake(_events)
        _done = self.recipe._data["main-content"]

        self.assertEqual(-1, errors_said(_done).find("The report is not available"))
        self.assertIn("textnorm: done", _done)
        self.assertIsNotNone(re.search(r'<a href="[^"]*/' + re.escape(_report) + r'" download="' + re.escape(_report) + r'"',
                                       _done))
        _archive = re.search(r'<a href="([^"]*)" download=""', _done).group(1)
        with zipfile.ZipFile(io.BytesIO(_provision.serve(_archive))) as _zip:
            _names = [os.path.basename(_name) for _name in _zip.namelist()]
        self.assertIn(_report, _names)
        self.assertIn("sample-token.xra", _names)

    # -----------------------------------------------------------------------

    def test_te50_online_two_types_are_disabled(self):
        """TE50. Online, the buttons of SPEAKER and INTERACTION are disabled, and the one of STANDALONE is not. [311], C27"""
        _pages = [self.recipe.bake({})]
        # The six steps again, once the files were sent.
        _pages.append(self.recipe.bake(swappPageFields(self.send()).submitted("event_bake", "annotate_steps")))
        for _page in _pages:
            _fields = swappPageFields(_page)
            self.assertNotIn("disabled", _fields.button("annotate_type_STANDALONE"))
            for _type in ("SPEAKER", "INTERACTION"):
                _button = _fields.button("annotate_type_" + _type)
                self.assertEqual("annotate_annotations_" + _type, _button["value"])
                self.assertIn("disabled", _button)


if __name__ == "__main__":
    unittest.main()
