# -*- coding: UTF-8 -*-
"""
:filename: tests.annotations.test_baseannot.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Tests of what the automatic annotations expect as input.

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

import sys
import unittest

import sppas.src.annotations
from sppas.src.annotations.autils import sppasFiles
from sppas.src.annotations.baseannot import sppasBaseAnnotation
from sppas.src.annotations.param import sppasParam

# ---------------------------------------------------------------------------


class TestInputFiletypes(unittest.TestCase):
    """The types of file of the inputs, against their extensions."""

    def assert_types_cover_extensions(self, annotation_class) -> None:
        """Each input has its types, and its extensions are some of theirs."""
        _filetypes = annotation_class.get_input_filetypes()
        _extensions = annotation_class.get_input_extensions()
        self.assertEqual(len(_extensions), len(_filetypes), annotation_class.__name__)
        for _types, _input in zip(_filetypes, _extensions):
            self.assertGreater(len(_types), 0, annotation_class.__name__)
            _of_types = list()
            for _type in _types:
                _of_types.extend(sppasFiles.get_informat_extensions(_type))
            for _extension in _input:
                self.assertIn(_extension, _of_types, annotation_class.__name__)

    # -----------------------------------------------------------------------

    def test_default(self):
        """By default, one input: an annotated file."""
        self.assertEqual([["ANNOT_ANNOT"]], sppasBaseAnnotation.get_input_filetypes())
        self.assert_types_cover_extensions(sppasBaseAnnotation)

    # -----------------------------------------------------------------------

    def test_every_declared_annotation(self):
        """For every annotation SPPAS declares, the types cover the extensions."""
        _param = sppasParam()
        for i in range(_param.get_step_numbers()):
            _api = _param.get_step(i).get_api()
            _class = getattr(sys.modules[sppas.src.annotations.__name__], _api)
            self.assert_types_cover_extensions(_class)

    # -----------------------------------------------------------------------

    def test_some_of_them(self):
        """What alignment, momel, searchipus and facedetect expect as input."""
        _param = sppasParam()
        _expected = {"alignment": [["AUDIO"], ["ANNOT_ANNOT"], ["ANNOT_ANNOT"]],
                     "momel": [["ANNOT_MEASURE"]],
                     "searchipus": [["AUDIO"]],
                     "facedetect": [["VIDEO", "IMAGE"]]}
        for _key in _expected:
            _api = _param.get_step(_param.get_step_idx(_key)).get_api()
            _class = getattr(sys.modules[sppas.src.annotations.__name__], _api)
            self.assertEqual(_expected[_key], _class.get_input_filetypes())


if __name__ == "__main__":
    unittest.main()
