"""
:filename: tests.preinstall.test_features.py
:author: Brigitte Bigi
:contributor: Florian Hocquet
:contact: contact@sppas.org
:summary: Test of Features()

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

from sppas.core.preinstall.features import Features

# ---------------------------------------------------------------------------


class TestFeatures(unittest.TestCase):

    def setUp(self):
        self.__features = Features("req_win", "cmd_win")

    # -----------------------------------------------------------------------

    def test_type(self):
        self.assertEqual(self.__features.feature_type("video"), "deps")
        self.assertEqual(self.__features.feature_type("stt"), "deps")
        self.assertEqual(self.__features.feature_type("wxpython"), "deps")
        self.assertEqual(self.__features.feature_type("facedetect"), "annot")
        self.assertEqual(self.__features.feature_type("fra"), "lang")
        self.assertEqual(self.__features.feature_type("autocs"), "spin")
        self.assertEqual(self.__features.feature_type("toto"), None)

    # -----------------------------------------------------------------------

    def test_get_features_filename(self):
        # Return the name of the file with the feature descriptions.
        y = self.__features.get_features_filename()
        self.assertIn("features.ini", y)

    # -----------------------------------------------------------------------

    def test_get_ids(self):
        # Return the list of feature identifiers.
        y = self.__features.get_ids()
        self.assertTrue("wxpython" in y)
        self.assertTrue("stt" in y)
        self.assertTrue("wintools" in y)
        self.assertTrue("video" in y)
        self.assertTrue("pol" in y)

    # -----------------------------------------------------------------------

    def test_enable(self):
        # Return True if the feature is enabled and/or set it.
        self.__features.enable("wxpython", False)
        y = self.__features.enable("wxpython")
        self.assertEqual(y, False)

        self.__features.enable("wxpython", True)
        y = self.__features.enable("wxpython")
        self.assertEqual(y, True)

    # -----------------------------------------------------------------------

    def test_available(self):
        # Return True if the feature is available and/or set it.
        y = self.__features.available("video")
        self.assertEqual(y, True)

        y = self.__features.available("wxpython")
        self.assertEqual(y, True)

        self.__features.available("wxpython", False)
        y = self.__features.available("wxpython")
        self.assertEqual(y, False)

        y = self.__features.available("toto")
        self.assertEqual(y, False)

    # -----------------------------------------------------------------------

    def test_description(self):
        # Return the description of the feature
        y = self.__features.description("wxpython")
        self.assertGreater(len(y), 0)

        y = self.__features.description("stt")
        self.assertGreater(len(y), 0)

        y = self.__features.description("wintools")
        self.assertGreater(len(y), 0)

    # -----------------------------------------------------------------------

    def test_packages(self):
        """Return the system dependencies dictionary of the feature."""
        # For WindowsInstaller
        y = self.__features.packages("wxpython")
        self.assertEqual(y, {})

        y = self.__features.packages("stt")
        self.assertEqual(y, {})

    # ------------------------------------------------------------------------

    def test_pypi(self):
        # For WindowsInstaller
        """Return the pip dependencies dictionary of the feature."""
        y = self.__features.pypi("wxpython")
        self.assertEqual(y, {'wxpython': '>=4.1'})

        # torch is installed only if openai-whisper can't be imported
        y = self.__features.pypi("stt")
        self.assertEqual(y, {'openai-whisper': ''})
        y = self.__features.pypi_alt("stt")
        self.assertEqual(y, {'torch': ''})

        y = self.__features.pypi("wintools")
        self.assertEqual(y, {})

    # -----------------------------------------------------------------------

    def test_cmd(self):
        # For WindowsInstaller
        """Return the command to execute for the feature."""
        y = self.__features.cmd("wxpython")
        self.assertEqual(y, "")

        y = self.__features.cmd("stt")
        self.assertEqual(y, "")

        self.assertTrue("wintools.py" in self.__features.cmd("wintools"))

    # -----------------------------------------------------------------------

    def test_init_features(self):
        # Return a parsed version of the features.ini file.
        y = self.__features._Features__init_features()

        self.assertGreater(len(y.sections()), 20)
        self.assertTrue("wxpython" in y.sections())

        self.assertEqual(y.get("wxpython", "pip"), "wxpython:>=4.1")

        self.assertTrue("wintools.py" in y.get("wintools", "cmd_win"))

    # -----------------------------------------------------------------------

    def test_set_features(self):
        # Browses the features.ini file and instantiate a Feature().
        self.setUp()

        self.__features.set_features()

        y = self.__features.get_ids()

        self.assertEqual(y[0], "sppas")
        self.assertEqual(self.__features.packages(y[0]), {})
        self.assertEqual(self.__features.pypi(y[0]), {'sppas': ''})
        self.assertEqual(self.__features.pypi_alt(y[0]), {})
        self.assertEqual(self.__features.cmd(y[0]), "")

        self.assertEqual(y[1], "wintools")
        self.assertEqual(self.__features.packages(y[1]), {})
        self.assertEqual(self.__features.pypi(y[1]), {})
        self.assertEqual(self.__features.pypi_alt(y[1]), {})
        self.assertTrue("wintools.py" in self.__features.cmd(y[1]))

        self.assertEqual(y[3], "wxpython")
        self.assertEqual(self.__features.packages(y[3]), {})
        self.assertEqual(self.__features.pypi(y[3]), {'wxpython': '>=4.1'})
        self.assertEqual(self.__features.pypi_alt(y[3]), {})
        self.assertEqual(self.__features.cmd(y[3]), "")

        self.assertEqual(y[6], "audioplay")
        self.assertEqual(self.__features.packages(y[6]), {})
        self.assertEqual(len(self.__features.pypi(y[6])), 1)
        self.assertEqual(len(self.__features.pypi_alt(y[6])), 2)
        self.assertEqual(self.__features.cmd(y[6]), "")

        self.assertEqual(y[7], "video")
        self.assertEqual(self.__features.packages(y[7]), {})
        self.assertEqual(len(self.__features.pypi(y[7])), 3)
        self.assertEqual(self.__features.pypi_alt(y[7]), {})
        self.assertEqual(self.__features.cmd(y[7]), "")

    # -----------------------------------------------------------------------

    def test_parse_depend(self):
        # Create a dictionary from the string given as an argument.
        parse = self.__features._Features__parse_depend

        y = parse("aa:aa aa:aa aa:aa aa:aa")
        self.assertEqual(y, {'aa': 'aa'})
        y = parse("aa:aa bb:bb cc:cc dd:dd")
        self.assertEqual(y, {'aa': 'aa', 'bb': 'bb', 'cc': 'cc', 'dd': 'dd'})

        # A package without any version constraint
        y = parse("torch openai-whisper")
        self.assertEqual(y, {'torch': '', 'openai-whisper': ''})

        # Only the first ':' is separating the name and the constraints
        y = parse("numpy:>2.0,<2.3.0")
        self.assertEqual(y, {'numpy': '>2.0,<2.3.0'})

        # Any given value is turned into a string
        y = parse(4)
        self.assertEqual(y, {'4': ''})

    # -----------------------------------------------------------------------

    def test_parse_pip_options(self):
        # Create a dictionary from the pip_opt value given as an argument.
        parse = self.__features._Features__parse_pip_options

        # Options of a given package
        y = parse("torch:--index-url https://download.pytorch.org/whl/cpu")
        self.assertEqual(y, {'torch': '--index-url https://download.pytorch.org/whl/cpu'})

        # Options of all the packages of the feature
        y = parse("-f https://wxpython.org/Phoenix/snapshot-builds/")
        self.assertEqual(y, {'': '-f https://wxpython.org/Phoenix/snapshot-builds/'})

        # One line for each package
        y = parse("torch:--index-url https://download.pytorch.org/whl/cpu\nnumpy:--pre")
        self.assertEqual(y, {'torch': '--index-url https://download.pytorch.org/whl/cpu',
                             'numpy': '--pre'})

        # Empty lines are ignored
        y = parse("\n   torch:--pre  \n\n")
        self.assertEqual(y, {'torch': '--pre'})

        y = parse("")
        self.assertEqual(y, {})

    # -----------------------------------------------------------------------

    def test_pypi_opt(self):
        # Return the options of a pip dependency of the feature.
        # The 'stt' feature requires the CPU-only version of torch, but the
        # index url must not be used for the other packages of the feature.
        y = self.__features.pypi_opt("stt", "torch")
        self.assertEqual(y, "--index-url https://download.pytorch.org/whl/cpu")

        y = self.__features.pypi_opt("stt", "openai-whisper")
        self.assertEqual(y, "")

        # The 'wxpython' feature defines options for all its packages, and it
        # does not define any alternative package
        y = self.__features.pypi_opt("wxpython", "wxpython")
        self.assertEqual(y, "-f https://wxpython.org/Phoenix/snapshot-builds/")

        # No option at all
        y = self.__features.pypi_opt("video", "numpy")
        self.assertEqual(y, "")

        y = self.__features.pypi_opt("toto", "numpy")
        self.assertEqual(y, "")

    # -----------------------------------------------------------------------

    def test__len__(self):
        # Return the number of features.
        y = self.__features.__len__()
        self.assertEqual(y, 33)

    # -----------------------------------------------------------------------

    def test__contains__(self):
        # Return the number of features.
        y = self.__features.__contains__("wxpython")
        self.assertTrue(y)

        y = self.__features.__contains__("stt")
        self.assertTrue(y)

        y = self.__features.__contains__("wintools")
        self.assertTrue(y)

        y = self.__features.__contains__("toto")
        self.assertFalse(y)

    # -----------------------------------------------------------------------

    def test_check_feature_deps(self):
        """Check the dependencies of one single feature."""
        from sppas.core.preinstall.feature import DepsFeature
        features = Features("req_win", "cmd_win")

        # An importable module and an executable command
        feat = DepsFeature("sys_and_cmd")
        feat.set_pip_test("sys")
        feat.set_cmd_test("python")
        features._Features__features.append(feat)
        self.assertTrue(features.check_feature_deps("sys_and_cmd"))
        self.assertTrue(features.available("sys_and_cmd"))
        self.assertTrue(features.enable("sys_and_cmd"))

        # A module which can't be imported
        feat = DepsFeature("bogus_module")
        feat.set_pip_test("idonotexist987654")
        feat.set_available(True)
        feat.set_enable(True)
        features._Features__features.append(feat)
        self.assertFalse(features.check_feature_deps("bogus_module"))
        self.assertFalse(features.available("bogus_module"))
        self.assertFalse(features.enable("bogus_module"))

        # A command which can't be executed
        feat = DepsFeature("bogus_command")
        feat.set_cmd_test("idonotexist987654")
        feat.set_available(True)
        feat.set_enable(True)
        features._Features__features.append(feat)
        self.assertFalse(features.check_feature_deps("bogus_command"))
        self.assertFalse(features.available("bogus_command"))

        # Nothing to be tested: the state of the feature is unchanged
        feat = DepsFeature("nothing_to_test")
        feat.set_available(True)
        features._Features__features.append(feat)
        self.assertTrue(features.check_feature_deps("nothing_to_test"))
        self.assertTrue(features.available("nothing_to_test"))

        # Not a deps feature, and an unknown feature
        self.assertFalse(features.check_feature_deps("fra"))
        self.assertFalse(features.check_feature_deps("toto"))

    # -----------------------------------------------------------------------

    def test_check_pip_deps_missing_module(self):
        """Feature must be unavailable if module(s) in pip_test are missing."""
        features = Features("req_win", "cmd_win")
        # Add a dummy feature with a non-existent module
        from sppas.core.preinstall.feature import DepsFeature
        dummy = DepsFeature("dummyfeature")
        dummy.set_pip_test("idonotexist987654")
        dummy.set_available(True)
        dummy.set_enable(True)
        features._Features__features.append(dummy)
        features.check_pip_deps()
        self.assertFalse(features.available("dummyfeature"))
        self.assertFalse(features.enable("dummyfeature"))

    # -----------------------------------------------------------------------

    def test_check_pip_deps_or_logic(self):
        """Feature should be available if at least one alternative exists."""
        features = Features("req_win", "cmd_win")
        # Add a feature that requires either sys (standard) or a bogus module
        from sppas.core.preinstall.feature import DepsFeature
        feat = DepsFeature("sys_or_bogus")
        feat.set_pip_test("sys|idonotexist123")
        feat.set_available(True)
        feat.set_enable(True)
        features._Features__features.append(feat)
        features.check_pip_deps()
        self.assertTrue(features.available("sys_or_bogus"))
        self.assertTrue(features.enable("sys_or_bogus"))

    def test_check_pip_deps_and_logic(self):
        """Feature should be available only if all AND groups are importable."""
        features = Features("req_win", "cmd_win")
        # Add a feature that requires sys AND unittest (should exist)
        from sppas.core.preinstall.feature import DepsFeature
        feat = DepsFeature("sys_and_unittest")
        feat.set_pip_test("sys unittest")
        feat.set_available(True)
        feat.set_enable(True)
        features._Features__features.append(feat)
        features.check_pip_deps()
        self.assertTrue(features.available("sys_and_unittest"))
        self.assertTrue(features.enable("sys_and_unittest"))

        # Now with a required module that doesn't exist
        feat2 = DepsFeature("sys_and_bogus")
        feat2.set_pip_test("sys idonotexist999")
        feat2.set_available(True)
        feat2.set_enable(True)
        features._Features__features.append(feat2)
        features.check_pip_deps()
        self.assertFalse(features.available("sys_and_bogus"))
        self.assertFalse(features.enable("sys_and_bogus"))
