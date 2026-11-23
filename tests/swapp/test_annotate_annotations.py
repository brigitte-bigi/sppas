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

    TE1 to TE13 of the dossier "Annotate - an app of SPPAS": arranging a list,
    with nothing installed, then ModelAnnotations with the API and no file.

    Arranging, and what an annotation requires, wait for the extension of the
    API (E1): TE1 to TE6 and TE12 fail until it is made. The dossier writes it
    that way on purpose for TE12: the test says whether the extension was made.

"""

from __future__ import annotations
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from sppas.src.annotations import sppasParam
from sppas.src.annotations.param import annotationParam

from sppas.ui.swapp.app_annotate.annotate_annotations import swappModelAnnotations

# ---------------------------------------------------------------------------


class AnnotationForTests:
    """An annotation as arranging is given it: its key, and what it requires."""

    def __init__(self, key: str, requires: list):
        self.__key = key
        self.__requires = requires

    def get_key(self) -> str:
        return self.__key

    def get_requires(self) -> list:
        return self.__requires

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
        _conf["required"] = requires
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


class TestArranged(unittest.TestCase):
    """TE1 to TE6. Nothing is installed and nothing is read."""

    def test_te1_what_comes_back_is_what_was_given(self):
        """TE1. Not one annotation added, not one removed."""
        _given = [AnnotationForTests("alignment", ["phonetize"]),
                  AnnotationForTests("textnorm", []),
                  AnnotationForTests("phonetize", ["textnorm"])]
        _arranged = swappModelAnnotations.arranged(_given)
        self.assertEqual(sorted(keys_of(_given)), sorted(keys_of(_arranged)))

    # -----------------------------------------------------------------------

    def test_te2_after_what_it_requires(self):
        """TE2. An annotation stands after every annotation of the list it requires. C9"""
        _arranged = swappModelAnnotations.arranged([AnnotationForTests("alignment", ["phonetize"]),
                                                    AnnotationForTests("phonetize", [])])
        _keys = keys_of(_arranged)
        self.assertLess(_keys.index("phonetize"), _keys.index("alignment"))

    # -----------------------------------------------------------------------

    def test_te3_a_requirement_not_in_the_list(self):
        """TE3. An annotation whose requirement is not in the list is in the list all the same. C9"""
        _arranged = swappModelAnnotations.arranged([AnnotationForTests("alignment", ["phonetize"])])
        self.assertEqual(["alignment"], keys_of(_arranged))

    # -----------------------------------------------------------------------

    def test_te4_a_chain_of_three(self):
        """TE4. Arranged the same way whatever order it was given in, the reverse included. C9"""
        _textnorm = AnnotationForTests("textnorm", [])
        _phonetize = AnnotationForTests("phonetize", ["textnorm"])
        _alignment = AnnotationForTests("alignment", ["phonetize"])
        for _given in ([_textnorm, _phonetize, _alignment],
                       [_alignment, _phonetize, _textnorm],
                       [_phonetize, _alignment, _textnorm]):
            self.assertEqual(["textnorm", "phonetize", "alignment"],
                             keys_of(swappModelAnnotations.arranged(_given)))

    # -----------------------------------------------------------------------

    def test_te5_a_requirement_which_names_nothing(self):
        """TE5. It changes nothing of the arrangement. C9"""
        _given = [AnnotationForTests("textnorm", []),
                  AnnotationForTests("alignment", ["nothing_bears_this_name"])]
        self.assertEqual(keys_of(_given), keys_of(swappModelAnnotations.arranged(_given)))

    # -----------------------------------------------------------------------

    def test_te6_the_same_list_twice(self):
        """TE6. The same list given twice is arranged the same way."""
        _given = [AnnotationForTests("syllabify", ["alignment"]),
                  AnnotationForTests("alignment", ["phonetize"]),
                  AnnotationForTests("textnorm", []),
                  AnnotationForTests("phonetize", ["textnorm"])]
        self.assertEqual(keys_of(swappModelAnnotations.arranged(_given)),
                         keys_of(swappModelAnnotations.arranged(_given)))

# ---------------------------------------------------------------------------


class TestModelAnnotations(unittest.TestCase):
    """TE7 to TE13. The annotations the API declares, and no file of a person."""

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
        self.assertEqual(["textnorm"], _requiring.get_requires())
        self.assertEqual([], _alone.get_requires())

    # -----------------------------------------------------------------------

    def test_te13_an_annotation_which_is_not_installed(self):
        """TE13. It is given all the same, and said so. C7"""
        def _test_step(parameters, step):
            return parameters.get_step_key(step) != "textnorm"

        with patch.object(sppasParam, "test_step", _test_step):
            self.assertIn("textnorm", keys_of(self.model.annotations()))
            self.assertFalse(self.model.is_installed("textnorm"))
            self.assertTrue(self.model.is_installed("phonetize"))


if __name__ == "__main__":
    unittest.main()
