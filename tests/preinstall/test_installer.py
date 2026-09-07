"""
:filename: tests.preinstall.test_installer.py
:author: Florian Hocquet, Brigitte Bigi
:contact: contact@sppas.org
:summary: Test of Installer()

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

import os
import unittest

from sppas.core.config import sppasLogSetup
from sppas.core.config import paths

from sppas.core.coreutils import sppasInstallationError
from sppas.core.preinstall.features import Features
from sppas.core.preinstall.installer import Installer

# ---------------------------------------------------------------------------

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# ---------------------------------------------------------------------------


class InstallerTest(Installer):
    """Manage the installation of external required or optional features. """
    def __init__(self):
        super(InstallerTest, self).__init__()
        self._features = Features(req="", cmdos="")

# ---------------------------------------------------------------------------


class TestInstaller(unittest.TestCase):

    def setUp(self):
        lgs = sppasLogSetup(0)
        lgs.stream_handler()
        self.__installer = InstallerTest()

    # ---------------------------------------------------------------------------

    def test_download_resource(self):
        with self.assertRaises(sppasInstallationError):
            InstallerTest().install_resource("url", "toto.zip", paths.resources)

        with self.assertRaises(sppasInstallationError):
            InstallerTest().install_resource(DATA, "badtest.zip", paths.resources)

        InstallerTest().install_resource(DATA, "test.zip", paths.resources)
        downloaded = os.path.join(paths.resources, "test.zip")
        installed = os.path.join(paths.resources, "faces", "test.txt")
        self.assertTrue(os.path.exists(installed))
        self.assertFalse(os.path.exists(downloaded))
        os.remove(installed)

    # ---------------------------------------------------------------------------

    def test_type(self):
        self.assertEqual(self.__installer.feature_type("video"), "deps")
        self.assertEqual(self.__installer.feature_type("stt"), "deps")
        self.assertEqual(self.__installer.feature_type("wxpython"), "deps")

    # ---------------------------------------------------------------------------

    def test_get_feat_ids(self):
        # Return the list of feature identifiers.
        y = self.__installer.get_fids()
        self.assertEqual(len(y), 33)
        self.assertTrue("wxpython" in y)
        self.assertTrue("stt" in y)
        self.assertTrue("wintools" in y)

        y = self.__installer.get_fids("deps")
        self.assertEqual(len(y), 9)

    # ---------------------------------------------------------------------------

    def test_enable(self):
        """Return True if the feature is enabled and/or set it."""
        y = self.__installer.get_fids()
        self.__installer.enable(y[0], True)
        self.assertTrue(self.__installer.enable(y[0]))

        self.__installer.enable(y[0], False)
        self.assertFalse(self.__installer.enable(y[0]))

    # ---------------------------------------------------------------------------

    def test_available(self):
        """Return True if the feature is available and/or set it."""
        y = self.__installer.get_fids()
        self.assertEqual(self.__installer.available(y[0]), True)

        self.__installer.available(y[0], False)
        self.assertEqual(self.__installer.available(y[0]), False)

    # ---------------------------------------------------------------------------

    def test_get_fids(self):
        y = self.__installer.get_fids()
        self.assertEqual(len(y), 33)

    # ---------------------------------------------------------------------------

    def test_pip_command(self):
        # Return the pip command line to install or update a package.
        y = self.__installer._pip_command("pip", "")
        self.assertTrue(y.endswith(" -m pip install 'pip' --no-warn-script-location") or
                        y.endswith(" -m pip install 'pip' --user --no-warn-script-location"))

        # The version constraints are appended to the name of the package
        y = self.__installer._pip_command("wxpython", ">=4.1")
        self.assertIn(" 'wxpython>=4.1'", y)

        # The arguments are given before the options and the package
        y = self.__installer._pip_command("torch", "", "--index-url https://download.pytorch.org/whl/cpu", "-U")
        self.assertIn(" -m pip install -U --index-url https://download.pytorch.org/whl/cpu 'torch'", y)

        y = self.__installer._pip_command("wxpython", ">=4.1", "-f https://wxpython.org/Phoenix/snapshot-builds/", "--pre")
        self.assertIn(" -m pip install --pre -f https://wxpython.org/Phoenix/snapshot-builds/ 'wxpython>=4.1'", y)

        y = self.__installer._pip_command("numpy", ">2.0,<2.3.0", "", "--only-binary=:all:")
        self.assertIn(" -m pip install --only-binary=:all: 'numpy>2.0,<2.3.0'", y)

    # ---------------------------------------------------------------------------

    def test_pip_command_options(self):
        # The options of a package are the ones of the feature it belongs to.
        features = self.__installer._features

        y = self.__installer._pip_command("torch", "", features.pypi_opt("stt", "torch"))
        self.assertIn("--index-url https://download.pytorch.org/whl/cpu 'torch'", y)

        # The index url of torch must not be used for the other packages
        y = self.__installer._pip_command("openai-whisper", "", features.pypi_opt("stt", "openai-whisper"))
        self.assertNotIn("--index-url", y)
        self.assertIn(" 'openai-whisper'", y)

    # ---------------------------------------------------------------------------

    def test_show_pypi(self):
        self.assertTrue(self.__installer._show_pypi("pip"))
        self.assertFalse(self.__installer._show_pypi("wxpythonnnnnn"))
        with self.assertRaises(sppasInstallationError):
            self.assertFalse(self.__installer._show_pypi(4))

    # ---------------------------------------------------------------------------

    def test_version_pypi(self):
        # Bug on MacOS but only in the test file not with the script "sppasinstall.py"
        # self.assertTrue(self.__installer._version_pypi("pip", ">;0.0"))
        self.assertFalse(self.__installer._version_pypi("numpy", ">;8.0"))

        self.assertFalse(self.__installer._version_pypi("pip", "aaaa"))
        self.assertFalse(self.__installer._version_pypi("pip", "<;4.2"))
        self.assertFalse(self.__installer._version_pypi("pip", "=;4.2"))

    # ---------------------------------------------------------------------------

    def test_need_update_pypi(self):
        x = "Name: wxPython \\r\\n" \
            "Version: 4.0.7.post2 \\r\\n" \
            "Summary: Cross platform GUI toolkit \\r\\n" \
            "Home-page: http://wxPython.org/ \\r\\n" \
            "Author: Robin Dunn \\r\\n" \

        y = "Name: numpy \\r\\n" \
            "Version: 1.18.3 \\r\\n" \
            "Summary: NumPy is the fundamental package for array computing with Python. \\r\\n" \
            "Home-page: https://www.numpy.org \\r\\n" \
            "Author: Travis E. Oliphant et al. \\r\\n"

        with self.assertRaises(IndexError):
            self.__installer._need_update_pypi("Bonjour", "aaaa")

        with self.assertRaises(IndexError):
            self.__installer._need_update_pypi(y, "aaaa")

        self.assertTrue(self.__installer._need_update_pypi(x, ">;4.2"))
        self.assertFalse(self.__installer._need_update_pypi(x, ">;4.0"))

        self.assertTrue(self.__installer._need_update_pypi(y, ">;1.2"))
        self.assertFalse(self.__installer._need_update_pypi(y, ">;1.0"))

        with self.assertRaises(ValueError):
            self.assertTrue(self.__installer._need_update_pypi(x, "<;4.2"))

        with self.assertRaises(ValueError):
            self.assertTrue(self.__installer._need_update_pypi(y, "=;1.2"))

    # ---------------------------------------------------------------------------

    def test_update_pypi_command(self):
        # The update of a package is using the options of this package
        y = self.__installer._pip_command("torch", "", "--index-url https://download.pytorch.org/whl/cpu", "-U")
        self.assertIn(" -m pip install -U ", y)
        self.assertIn("--index-url https://download.pytorch.org/whl/cpu", y)
        self.assertIn(" 'torch'", y)

    # ---------------------------------------------------------------------------

    def test_search_package(self):
        with self.assertRaises(NotImplementedError):
            self.__installer._search_package("aaaa")

    # ---------------------------------------------------------------------------

    def test_install_package(self):
        with self.assertRaises(NotImplementedError):
            self.__installer._install_package("aaaa")

    # ---------------------------------------------------------------------------

    def test_version_package(self):
        with self.assertRaises(NotImplementedError):
            self.__installer._version_package("aaaa", "aaaa")

    # ---------------------------------------------------------------------------

    def test_need_update_package(self):
        with self.assertRaises(NotImplementedError):
            self.__installer._need_update_package("aaaa", "aaaa")

    # ---------------------------------------------------------------------------

    def test_update_package(self):
        with self.assertRaises(NotImplementedError):
            self.__installer._update_package("aaaa", "4.0")
