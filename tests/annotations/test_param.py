# -*- coding: UTF-8 -*-
"""
:filename: tests.annotations.test_param.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Tests of the parameters of the automatic annotations.

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
import shutil
import tempfile
import unittest

from sppas.core.config import paths
from sppas.core.coreutils import sppasTypeError
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States
from sppas.src.annotations.autils import sppasFiles
from sppas.src.annotations.param import annotationParam
from sppas.src.annotations.param import sppasParam

# ---------------------------------------------------------------------------


def declared_keys() -> list:
    """Return the keys of the annotations sppasui.json declares, in its order."""
    with open(os.path.join(paths.etc, "sppasui.json")) as fp:
        _config = json.load(fp)
    _keys = list()
    for _ann in _config.get("annotate", []):
        with open(os.path.join(paths.etc, _ann["config"])) as fp:
            _keys.append(json.load(fp)["id"])
    return _keys

# ---------------------------------------------------------------------------


class TestAnnotationParam(unittest.TestCase):
    """What is read from the configuration file of one annotation."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="test_param_")

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def write(self, conf: dict) -> str:
        """Write a configuration file in the folder of the test, and return its name."""
        _filename = os.path.join(self.folder, conf["id"] + ".json")
        with open(_filename, "w") as fp:
            json.dump(conf, fp)
        return _filename

    # -----------------------------------------------------------------------

    def test_init(self):
        """Nothing is read when no file is given."""
        _param = annotationParam()
        self.assertIsNone(_param.get_key())
        self.assertEqual("", _param.get_name())
        self.assertEqual([], _param.get_types())
        self.assertEqual([], _param.get_requires())
        self.assertFalse(_param.get_activate())

    # -----------------------------------------------------------------------

    def test_parse(self):
        """What the file declares is what is given."""
        _param = annotationParam(self.write({"id": "test", "name": "Test", "descr": "A test.",
                                             "api": "TestAnn", "anntype": ["SPEAKER"],
                                             "required": ["textnorm", "phonetize"],
                                             "refs": {"ref": "https://sppas.org/"}, "devel": 50,
                                             "options": [], "resources": []}))
        self.assertEqual("test", _param.get_key())
        self.assertEqual("A test.", _param.get_descr())
        self.assertEqual("TestAnn", _param.get_api())
        self.assertEqual(["SPEAKER"], _param.get_types())
        self.assertEqual(["textnorm", "phonetize"], _param.get_requires())
        self.assertEqual(["ref"], _param.get_reference_identifiers())
        self.assertEqual("https://sppas.org/", _param.get_reference_url("ref"))
        self.assertEqual("", _param.get_reference_url("unknown"))
        self.assertEqual(50, _param.get_devel())

    # -----------------------------------------------------------------------

    def test_requires(self):
        """An annotation which declares nothing required requires nothing."""
        _param = annotationParam(self.write({"id": "alone", "api": "TestAnn",
                                             "options": [], "resources": []}))
        self.assertEqual([], _param.get_requires())

        # What is given back is a copy: changing it changes nothing.
        _param = annotationParam(self.write({"id": "requiring", "api": "TestAnn", "required": ["textnorm"],
                                             "options": [], "resources": []}))
        _param.get_requires().append("phonetize")
        self.assertEqual(["textnorm"], _param.get_requires())

    # -----------------------------------------------------------------------

    def test_every_declared_annotation_requires_a_list(self):
        """In every configuration file of an annotation, what is required is a list."""
        _param = sppasParam()
        for i in range(_param.get_step_numbers()):
            self.assertIsInstance(_param.get_step(i).get_requires(), list)

    # -----------------------------------------------------------------------

    def test_invalid(self):
        """An annotation which declares no api cannot be activated."""
        _param = annotationParam(self.write({"id": "noapi", "options": [], "resources": []}))
        self.assertFalse(_param.set_activate(True))
        self.assertFalse(_param.get_activate())

    # -----------------------------------------------------------------------

    def test_wrong_file(self):
        """A file which is not a json one, or which does not exist, is not read."""
        with self.assertRaises(IOError):
            annotationParam("annotation.ini")
        with self.assertRaises(IOError):
            annotationParam(os.path.join(self.folder, "nothing.json"))

    # -----------------------------------------------------------------------

    def test_option(self):
        """The value of an option is changed by its key; an unknown key is refused."""
        _param = annotationParam(self.write({"id": "options", "api": "TestAnn",
                                             "options": [{"id": "opt", "type": "bool", "value": True}],
                                             "resources": []}))
        self.assertEqual("opt", _param.get_option_by_key("opt").get_key())
        _param.set_option_value("opt", False)
        self.assertFalse(_param.get_option_by_key("opt").get_value())
        with self.assertRaises(KeyError):
            _param.set_option_value("unknown", True)

# ---------------------------------------------------------------------------


class TestSppasParam(unittest.TestCase):
    """The parameters of the annotations SPPAS declares."""

    def setUp(self):
        self.param = sppasParam()
        self.folder = tempfile.mkdtemp(prefix="test_param_")

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_load(self):
        """Every annotation the main configuration file declares is loaded, in its order."""
        _keys = list()
        for i in range(self.param.get_step_numbers()):
            _keys.append(self.param.get_step_key(i))
        _declared = declared_keys()
        self.assertEqual(_declared, _keys[:len(_declared)])
        self.assertEqual(len(_keys), len(self.param.get_steplist()))

    # -----------------------------------------------------------------------

    def test_load_some(self):
        """Only the given configuration files are loaded; one which cannot be is not."""
        _param = sppasParam(["textnorm.json", "phonetize.json", "nothing.json"])
        self.assertEqual(2, _param.get_step_numbers())
        self.assertEqual("textnorm", _param.get_step_key(0))
        self.assertEqual("phonetize", _param.get_step_key(1))

    # -----------------------------------------------------------------------

    def test_step_idx(self):
        """The index of a step is found from the key of its annotation."""
        _idx = self.param.get_step_idx("phonetize")
        self.assertEqual("phonetize", self.param.get_step_key(_idx))
        self.assertIs(self.param.get_step(_idx), self.param.annotations[_idx])
        with self.assertRaises(KeyError):
            self.param.get_step_idx("nothing_bears_this_key")

    # -----------------------------------------------------------------------

    def test_check_step(self):
        """A step which is not an index of the annotations is refused."""
        with self.assertRaises(sppasTypeError):
            self.param.get_step_name(-1)
        with self.assertRaises(sppasTypeError):
            self.param.get_step_name(None)
        with self.assertRaises(ValueError):
            self.param.get_step_name(self.param.get_step_numbers())
        with self.assertRaises(ValueError):
            self.param.get_step_name("one")

    # -----------------------------------------------------------------------

    def test_what_a_step_declares(self):
        """Its name, description, types and options are those of its annotation."""
        for i in range(self.param.get_step_numbers()):
            _step = self.param.get_step(i)
            self.assertEqual(_step.get_name(), self.param.get_step_name(i))
            self.assertEqual(_step.get_descr(), self.param.get_step_descr(i))
            self.assertEqual(_step.get_types(), self.param.get_step_types(i))
            self.assertEqual(_step.get_options(), self.param.get_options(i))
            self.assertEqual(_step.get_langlist(), self.param.get_langlist(i))
            self.assertEqual(_step.get_reference_identifiers(), self.param.get_ref_ids(i))
            self.assertEqual(_step.get_devel(), self.param.get_devel(i))

    # -----------------------------------------------------------------------

    def test_requires(self):
        """What the annotation of a step requires, as its configuration file declares it."""
        self.assertEqual([], self.param.get_requires(self.param.get_step_idx("textnorm")))
        self.assertEqual(["textnorm"], self.param.get_requires(self.param.get_step_idx("phonetize")))
        self.assertEqual(["phonetize"], self.param.get_requires(self.param.get_step_idx("alignment")))
        with self.assertRaises(ValueError):
            self.param.get_requires(self.param.get_step_numbers())

    # -----------------------------------------------------------------------

    def test_activate(self):
        """A step is activated, then disabled; an annotation is activated by its key."""
        _idx = self.param.get_step_idx("textnorm")
        self.assertFalse(self.param.get_step_status(_idx))
        self.param.activate_step(_idx)
        self.assertTrue(self.param.get_step_status(_idx))
        self.param.disable_step(_idx)
        self.assertFalse(self.param.get_step_status(_idx))

        self.assertEqual(_idx, self.param.activate_annotation("textnorm"))
        self.assertTrue(self.param.get_step_status(_idx))
        self.assertEqual(-1, self.param.activate_annotation("nothing_bears_this_key"))

    # -----------------------------------------------------------------------

    def test_test_step(self):
        """An annotation whose class is instantiated without error can be performed."""
        self.assertTrue(self.param.test_step(self.param.get_step_idx("textnorm")))

    # -----------------------------------------------------------------------

    def test_option_value(self):
        """The value of an option of a step is changed; an unknown option is refused."""
        _idx = self.param.get_step_idx("textnorm")
        _option = self.param.get_options(_idx)[0]
        self.param.set_option_value(_idx, _option.get_key(), _option.get_value())
        with self.assertRaises(KeyError):
            self.param.set_option_value(_idx, "nothing_bears_this_key", "")

    # -----------------------------------------------------------------------

    def test_output_extension(self):
        """The default extension of each kind, then one of its own, and one which is not."""
        for _kind in sppasFiles.OUT_FORMATS:
            self.assertEqual(sppasFiles.DEFAULT_EXTENSIONS[_kind], self.param.get_output_extension(_kind))

        _extension = sppasFiles.get_outformat_extensions("ANNOT")[0]
        _assigned = self.param.set_output_extension(_extension.lstrip("."), "ANNOT")
        self.assertEqual(_extension.lower(), _assigned.lower())
        self.assertEqual(_assigned, self.param.get_output_extension("ANNOT"))
        with self.assertRaises(ValueError):
            self.param.set_output_extension(".nothing", "ANNOT")
        with self.assertRaises(KeyError):
            self.param.get_output_extension("NOTHING")

    # -----------------------------------------------------------------------

    def test_report_filename(self):
        """No report is named until one is."""
        self.assertIsNone(self.param.get_report_filename())
        self.param.set_report_filename("report.txt")
        self.assertEqual("report.txt", self.param.get_report_filename())

    # -----------------------------------------------------------------------

    def test_workspace(self):
        """A workspace is set; anything else is refused. What is added is checked."""
        _workspace = sppasWorkspace()
        self.param.set_workspace(_workspace)
        self.assertIs(_workspace, self.param.get_workspace())
        with self.assertRaises(sppasTypeError):
            self.param.set_workspace("workspace")

        _filename = os.path.join(self.folder, "sample.txt")
        with open(_filename, "w") as fp:
            fp.write("")
        self.param.add_to_workspace([_filename, os.path.join(self.folder, "nothing.txt")])
        _checked = list()
        for _file in _workspace.get_filename_from_state(States().CHECKED):
            _checked.append(_file.get_id())
        self.assertEqual([_filename], _checked)
        self.assertEqual([os.path.join(self.folder, "sample")], self.param.get_checked_roots())


if __name__ == "__main__":
    unittest.main()
