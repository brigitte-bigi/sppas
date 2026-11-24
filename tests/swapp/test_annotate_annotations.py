# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_annotate_annotations.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of what the app of the annotations knows of them.

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

    TE7 to TE13, TE43, TE45 and TE47 of the dossier "Annotate - an app of SPPAS":
    ModelAnnotations with the API and no file.

"""

from __future__ import annotations
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import sppas.src.annotations
from sppas.core.coreutils import sppasEnableFeatureError
from sppas.src.annotations import sppasParam
from sppas.src.annotations.param import annotationParam

from sppas.ui.swapp.app_annotate.annotate_annotations import swappModelAnnotations

# ---------------------------------------------------------------------------


class NotEnabledForTests:
    """The class the package imports for an annotation whose feature is not enabled."""

    def __init__(self, *args, **kwargs):
        raise sppasEnableFeatureError("feature_for_tests")

# ---------------------------------------------------------------------------


def make_annotation(where: str, key: str, anntype: list, requires: list | None = None) -> str:
    """Write the declaration of an annotation in a folder, and return its file name."""
    _conf = {"id": key,
             "name": "Annotation " + key,
             "descr": "What " + key + " says of itself.",
             "api": "TestAnn",
             "anntype": anntype,
             "options": [],
             "resources": []}
    if requires is not None:
        _conf["required_annotations"] = requires
    _filename = os.path.join(where, key + ".json")
    with open(_filename, "w") as fp:
        json.dump(_conf, fp)
    return _filename


def keys_of(annotations: list) -> list:
    """Return the keys of the given annotations, in their order."""
    _keys = list()
    for _annotation in annotations:
        _keys.append(_annotation.get_key())
    return _keys

# ---------------------------------------------------------------------------


class TestModelAnnotations(unittest.TestCase):
    """TE7 to TE13, TE43, TE45, TE47. The annotations the API declares, and no file of a person."""

    def setUp(self):
        self.model = swappModelAnnotations()
        self.declared = sppasParam()
        self.folder = tempfile.mkdtemp(prefix="test_annotate_annotations_")

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te7_every_annotation_declared(self):
        """TE7. Every annotation the API declares is given, and no other. [308], C7"""
        _declared = list()
        for i in range(self.declared.get_step_numbers()):
            _declared.append(self.declared.get_step_key(i))
        self.assertEqual(_declared, keys_of(self.model.annotations()))

    # -----------------------------------------------------------------------

    def test_te8_what_is_given_is_what_is_declared(self):
        """TE8. Its name, description, types, languages, references and development. C8"""
        _given = self.model.annotations()
        for i in range(self.declared.get_step_numbers()):
            _step = self.declared.get_step(i)
            self.assertEqual(_step.get_name(), _given[i].get_name())
            self.assertEqual(_step.get_descr(), _given[i].get_descr())
            self.assertEqual(_step.get_types(), _given[i].get_types())
            self.assertEqual(_step.get_langlist(), _given[i].get_langlist())
            self.assertEqual(_step.get_reference_identifiers(), _given[i].get_reference_identifiers())

    # -----------------------------------------------------------------------

    def test_te9_an_annotation_of_two_types(self):
        """TE9. An annotation which has two types is given for each of them. [301]"""
        _filename = make_annotation(self.folder, "twotypes", ["STANDALONE", "SPEAKER"])
        # The annotations of the model are those of its own sppasParam.
        self.model._swappModelAnnotations__parameters.annotations.append(annotationParam(_filename))

        for _type in ("STANDALONE", "SPEAKER"):
            _of_type = list()
            for _annotation in self.model.annotations():
                if _type in _annotation.get_types():
                    _of_type.append(_annotation.get_key())
            self.assertIn("twotypes", _of_type)

    # -----------------------------------------------------------------------

    def test_te10_the_kinds_of_output_file(self):
        """TE10. No kind without an extension; the default extension of a kind is one of its extensions. C1, C2"""
        _kinds = self.model.kinds()
        self.assertGreater(len(_kinds), 0)
        for _kind in _kinds:
            _extensions, _default = _kinds[_kind]
            self.assertGreater(len(_extensions), 0)
            self.assertIn(_default, _extensions)

    # -----------------------------------------------------------------------

    def test_te11_the_languages_of_the_page(self):
        """TE11. Those of every annotation put together, each of them once. [201]"""
        _expected = list()
        for i in range(self.declared.get_step_numbers()):
            for _lang in self.declared.get_step(i).get_langlist():
                if (_lang in _expected) is False:
                    _expected.append(_lang)
        _languages = self.model.languages()
        self.assertEqual(sorted(_expected), sorted(_languages))
        self.assertEqual(len(set(_languages)), len(_languages))

    # -----------------------------------------------------------------------

    def test_te12_what_an_annotation_requires(self):
        """TE12. Read from its declaration; one which declares none requires nothing. [307]"""
        _requiring = annotationParam(make_annotation(self.folder, "requiring", ["STANDALONE"], ["textnorm"]))
        _alone = annotationParam(make_annotation(self.folder, "alone", ["STANDALONE"]))
        self.assertEqual(["textnorm"], _requiring.get_required_annotations())
        self.assertEqual([], _alone.get_required_annotations())

    # -----------------------------------------------------------------------

    def test_te13_an_annotation_which_is_not_installed(self):
        """TE13. It is given all the same, and said so. C7"""
        _api = self.declared.get_step(self.declared.get_step_idx("textnorm")).get_api()
        with patch.object(sppas.src.annotations, _api, NotEnabledForTests):
            self.assertIn("textnorm", keys_of(self.model.annotations()))
            self.assertFalse(self.model.is_installed("textnorm"))
            self.assertTrue(self.model.is_installed("phonetize"))

    # -----------------------------------------------------------------------

    def test_te47_why_an_annotation_is_not_installed(self):
        """TE47. What the error of its instantiation says: the feature which is not enabled. C7"""
        _api = self.declared.get_step(self.declared.get_step_idx("textnorm")).get_api()
        with patch.object(sppas.src.annotations, _api, NotEnabledForTests):
            self.assertIn("feature_for_tests", self.model.why_not_installed("textnorm"))
            self.assertEqual("", self.model.why_not_installed("phonetize"))
        with self.assertRaises(KeyError):
            self.model.why_not_installed("nothing_bears_this_key")

    # -----------------------------------------------------------------------

    def test_te43_the_names_of_what_an_annotation_requires(self):
        """TE43. The names the API declares for the required keys; none when none is required. [307]"""
        _expected = list()
        for _key in self.declared.get_required_annotations(self.declared.get_step_idx("phonetize")):
            _expected.append(self.declared.get_step_name(self.declared.get_step_idx(_key)))
        self.assertGreater(len(_expected), 0)
        self.assertEqual(_expected, self.model.required_names("phonetize"))
        self.assertEqual([], self.model.required_names("textnorm"))
        with self.assertRaises(KeyError):
            self.model.required_names("nothing_bears_this_key")

        # A required annotation the API does not declare is given as it is written.
        _filename = make_annotation(self.folder, "orphan", ["STANDALONE"], ["nothing_declared"])
        self.model._swappModelAnnotations__parameters.annotations.append(annotationParam(_filename))
        self.assertEqual(["nothing_declared"], self.model.required_names("orphan"))

    # -----------------------------------------------------------------------

    def test_te45_the_types_of_file_an_annotation_reads(self):
        """TE45. Those of all its inputs, each once, in their order. [307]"""
        self.assertEqual(["AUDIO", "ANNOT_ANNOT"], self.model.required_filetypes("alignment"))
        self.assertEqual(["ANNOT_MEASURE"], self.model.required_filetypes("momel"))
        with self.assertRaises(KeyError):
            self.model.required_filetypes("nothing_bears_this_key")

        # An annotation whose class the API does not know is given none.
        _filename = make_annotation(self.folder, "unknown", ["STANDALONE"])
        self.model._swappModelAnnotations__parameters.annotations.append(annotationParam(_filename))
        self.assertEqual([], self.model.required_filetypes("unknown"))


if __name__ == "__main__":
    unittest.main()
