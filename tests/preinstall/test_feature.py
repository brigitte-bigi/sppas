"""
:filename: tests.preinstall.test_feature.py
:author: Brigitte Bigi
:contributor: Florian Hocquet
:contact: contact@sppas.org
:summary: Test of Feature()

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

from sppas.core.preinstall.feature import Feature
from sppas.core.preinstall.feature import DepsFeature
from sppas.core.preinstall.feature import SpinOffFeature

# ---------------------------------------------------------------------------


class TestFeature(unittest.TestCase):

    def setUp(self):
        self.__feature = Feature("feature")

    # ---------------------------------------------------------------------------

    def test_init(self):
        f = Feature("identifier")
        self.assertEqual(f.get_id(), "identifier")

        # Invalid identifiers: a GUID is set instead
        f = Feature("x")
        self.assertNotEqual(f.get_id(), "x")
        self.assertEqual(len(f.get_id()), 36)
        f = Feature("è bè...")
        self.assertEqual(len(f.get_id()), 36)

    # ---------------------------------------------------------------------------

    def test_get_id(self):
        """Return the id of feature."""
        y = self.__feature.get_id()
        self.assertEqual(y, "feature")

    # ---------------------------------------------------------------------------

    def test_type(self):
        self.assertEqual(self.__feature.get_type(), "")

    # ---------------------------------------------------------------------------

    def test_get_set_enable(self):
        """Return(get_enable) or set(set_enable) enable of feature."""
        self.__feature.set_enable(True)
        y = self.__feature.get_enable()
        self.assertIsInstance(y, bool)
        self.assertFalse(y)

        self.__feature.set_available(False)
        self.__feature.set_enable(True)
        y = self.__feature.get_enable()
        self.assertIsInstance(y, bool)
        self.assertFalse(y)

        self.__feature.set_available(True)
        self.__feature.set_enable(["a", "b", "c"])
        y = self.__feature.get_enable()
        self.assertIsInstance(y, bool)
        self.assertTrue(y)

        self.__feature.set_enable({"1": "a", "2": "b", "3": "c"})
        y = self.__feature.get_enable()
        self.assertIsInstance(y, bool)
        self.assertTrue(y)

        self.__feature.set_enable("")
        y = self.__feature.get_enable()
        self.assertIsInstance(y, bool)
        self.assertFalse(y)

        self.__feature.set_enable(4)
        y = self.__feature.get_enable()
        self.assertIsInstance(y, bool)
        self.assertTrue(y)

    # ---------------------------------------------------------------------------

    def test_get_set_available(self):
        """Return(get_available) or set(set_available) available of feature."""
        self.__feature.set_available(True)
        y = self.__feature.get_available()
        self.assertIsInstance(y, bool)
        self.assertEqual(y, True)

        self.__feature.set_enable(True)
        self.__feature.set_available(False)
        y = self.__feature.get_available()
        x = self.__feature.get_enable()
        self.assertIsInstance(y, bool)
        self.assertIsInstance(x, bool)
        self.assertEqual(y, False)
        self.assertEqual(x, False)

        self.__feature.set_available(["a", "b", "c"])
        y = self.__feature.get_available()
        self.assertIsInstance(y, bool)
        self.assertEqual(y, True)

        self.__feature.set_available({"1": "a", "2": "b", "3": "c"})
        y = self.__feature.get_available()
        self.assertIsInstance(y, bool)
        self.assertEqual(y, True)

        self.__feature.set_available("")
        y = self.__feature.get_available()
        self.assertIsInstance(y, bool)
        self.assertEqual(y, False)

        self.__feature.set_available(4)
        y = self.__feature.get_available()
        self.assertIsInstance(y, bool)
        self.assertEqual(y, True)

    # ---------------------------------------------------------------------------

    def test_get_set_desc(self):
        """Return(get_desc) or set(set_desc) the description of feature."""
        self.__feature.set_desc("aaaa")
        y = self.__feature.get_desc()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "aaaa")

        self.__feature.set_desc(True)
        y = self.__feature.get_desc()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "True")

        self.__feature.set_desc(["a", "b", "c"])
        y = self.__feature.get_desc()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "['a', 'b', 'c']")

        self.__feature.set_desc({"1": "a", "2": "b", "3": "c"})
        y = self.__feature.get_desc()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "{'1': 'a', '2': 'b', '3': 'c'}")

        self.__feature.set_desc(4)
        y = self.__feature.get_desc()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "4")

# ---------------------------------------------------------------------------


class TestDepsFeature(unittest.TestCase):

    def setUp(self):
        self.__feature = DepsFeature("feature")

    # ---------------------------------------------------------------------------

    def test_type(self):
        self.assertEqual(self.__feature.get_type(), "deps")

    # ---------------------------------------------------------------------------

    def test_get_set_packages(self):
        """Return(get_packages) or set(set_packages) the dictionary of system dependencies."""
        self.__feature.set_packages(dict())
        y = self.__feature.get_packages()
        self.assertIsInstance(y, dict)
        self.assertEqual(y, {})

        self.__feature.set_packages({'1': 'a', '2': 'b', '3': 'c'})
        y = self.__feature.get_packages()
        self.assertIsInstance(y, dict)
        self.assertEqual(y, {'1': 'a', '2': 'b', '3': 'c'})

        with self.assertRaises(ValueError):
            self.__feature.set_packages(["a", "b", "c"])

        with self.assertRaises(ValueError):
            self.__feature.set_packages("a")

        with self.assertRaises(TypeError):
            self.__feature.set_packages((1, 2, 3))

        with self.assertRaises(TypeError):
            self.__feature.set_packages(4)

        with self.assertRaises(TypeError):
            self.__feature.set_packages(True)

        with self.assertRaises(TypeError):
            self.__feature.set_packages(4.0)

    # ---------------------------------------------------------------------------

    def test_get_set_pypi(self):
        """Return(get_pypi) or set(set_pypi) the dictionary of pip dependencies."""
        y = self.__feature.get_pypi_packages()
        self.assertIsInstance(y, list)
        self.assertEqual(len(y), 0)

        depends = {'1': 'a', '2': 'b', '3': 'c'}
        for key in depends:
            self.__feature.add_pypi(key, depends[key])
        y = self.__feature.get_pypi_packages()
        # Test package names
        self.assertIsInstance(y, list)
        self.assertEqual(y, ['1', '2', '3'])
        # Test package versions ==> do it...

    # ---------------------------------------------------------------------------

    def test_get_set_cmd(self):
        """Return(get_cmd) or set(set_cmd) the command to execute"""
        self.__feature.set_cmd("aaaa")
        y = self.__feature.get_cmd()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "aaaa")

        self.__feature.set_cmd(True)
        y = self.__feature.get_cmd()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "True")

        self.__feature.set_cmd(["a", "b", "c"])
        y = self.__feature.get_cmd()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "['a', 'b', 'c']")

        self.__feature.set_cmd({"1": "a", "2": "b", "3": "c"})
        y = self.__feature.get_cmd()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "{'1': 'a', '2': 'b', '3': 'c'}")

        self.__feature.set_cmd(4)
        y = self.__feature.get_cmd()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "4")

    # ---------------------------------------------------------------------------

    def test_get_set_pip_options(self):
        """Return(get_pip_options) or set(set_pip_options) the pip options."""
        # Initial state: no option at all
        self.assertEqual(self.__feature.get_pip_options(), "")
        self.assertEqual(self.__feature.get_pip_options("torch"), "")

        # Options of a given package
        self.__feature.set_pip_options({"torch": "--index-url https://download.pytorch.org/whl/cpu"})
        self.assertEqual(
            self.__feature.get_pip_options("torch"),
            "--index-url https://download.pytorch.org/whl/cpu"
        )
        # ... are not the ones of the other packages of the feature
        self.assertEqual(self.__feature.get_pip_options("openai-whisper"), "")

        # Options of all the packages of the feature
        self.__feature.set_pip_options({"": "-f https://wxpython.org/Phoenix/snapshot-builds/"})
        self.assertEqual(
            self.__feature.get_pip_options("wxpython"),
            "-f https://wxpython.org/Phoenix/snapshot-builds/"
        )
        self.assertEqual(
            self.__feature.get_pip_options(),
            "-f https://wxpython.org/Phoenix/snapshot-builds/"
        )

        # The options of a package are used instead of the ones of the feature
        self.__feature.set_pip_options({"": "--pre", "torch": "--index-url https://download.pytorch.org/whl/cpu"})
        self.assertEqual(
            self.__feature.get_pip_options("torch"),
            "--index-url https://download.pytorch.org/whl/cpu"
        )
        self.assertEqual(self.__feature.get_pip_options("numpy"), "--pre")

        # Any given package name is turned into a string
        self.__feature.set_pip_options({"4": "--pre"})
        self.assertEqual(self.__feature.get_pip_options(4), "--pre")

        with self.assertRaises(TypeError):
            self.__feature.set_pip_options(4)

    # ---------------------------------------------------------------------------

    def test_get_set_pip_test(self):
        """Return(get_pip_test) or set(set_pip_test) the value of pip_test."""
        # Initial state: should be empty string
        self.assertEqual(self.__feature.get_pip_test(), "")

        # Set a simple value
        self.__feature.set_pip_test("whakerpy audioopy clamming")
        self.assertEqual(
            self.__feature.get_pip_test(),
            "whakerpy audioopy clamming"
        )

        # Set a value with OR alternative
        self.__feature.set_pip_test("pyaudio|simpleaudio")
        self.assertEqual(self.__feature.get_pip_test(), "pyaudio|simpleaudio")

        # Set an empty value (should store as empty string)
        self.__feature.set_pip_test("")
        self.assertEqual(self.__feature.get_pip_test(), "")

        # Set a non-string value (should be converted to string)
        self.__feature.set_pip_test(None)
        self.assertEqual(self.__feature.get_pip_test(), "None")

        self.__feature.set_pip_test(1234)
        self.assertEqual(self.__feature.get_pip_test(), "1234")

    # ---------------------------------------------------------------------------

    def test_pip_test_julius_absent(self):
        """Check pip_test is missing or empty for a non-Python-only feature (like julius)."""
        feature = DepsFeature("julius")
        # Simulate absence (default after init)
        self.assertEqual(feature.get_pip_test(), "")

# ---------------------------------------------------------------------------


class TestSpinOffFeature(unittest.TestCase):

    def setUp(self):
        from sppas.core.preinstall.feature import SpinOffFeature
        self.__feature = SpinOffFeature("myspin")

    # ---------------------------------------------------------------------------

    def test_type(self):
        self.assertEqual(self.__feature.get_type(), "spin")

    # ---------------------------------------------------------------------------

    def test_get_set_spin(self):
        """Return (get_spin) or set (set_spin) the spin-off name."""
        self.__feature.set_spin("customannot")
        y = self.__feature.get_spin()
        self.assertIsInstance(y, str)
        self.assertEqual(y, "customannot")

        # Test with different types converted to str
        self.__feature.set_spin(True)
        y = self.__feature.get_spin()
        self.assertEqual(y, "True")

        self.__feature.set_spin(["a", "b"])
        y = self.__feature.get_spin()
        self.assertEqual(y, "['a', 'b']")

        self.__feature.set_spin({"x": 1})
        y = self.__feature.get_spin()
        self.assertEqual(y, "{'x': 1}")

        self.__feature.set_spin(123)
        y = self.__feature.get_spin()
        self.assertEqual(y, "123")

        # Test with empty value → warning expected, but no crash
        self.__feature.set_spin("")
        y = self.__feature.get_spin()
        self.assertEqual(y, "123")  # previous value is not deleted

