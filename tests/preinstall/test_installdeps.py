"""
:filename: tests.preinstall.test_installdeps.py
:author: Florian Hocquet, Brigitte Bigi
:contact: contact@sppas.org
:summary: Test of the deps installers.

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

from sppas.core.preinstall.depsinstall import sppasGuessInstaller
from sppas.core.preinstall.depsinstall import sppasInstallerDeps
from sppas.core.preinstall.installer import WindowsInstaller
from sppas.core.preinstall.installer import MacOsInstaller
from sppas.core.preinstall.installer import DebianInstaller
from sppas.core.preinstall.installer import DnfInstaller

# ---------------------------------------------------------------------------


class TestGuessInstaller(unittest.TestCase):

    def test_guess(self):
        self.assertEqual(WindowsInstaller, sppasGuessInstaller.guess("win32"))
        self.assertEqual(MacOsInstaller, sppasGuessInstaller.guess("darwin"))
        self.assertEqual(DebianInstaller, sppasGuessInstaller.guess("debian"))
        self.assertEqual(DnfInstaller, sppasGuessInstaller.guess("fedora"))

        # An unknown system: the installer depends on the available commands
        self.assertIn(sppasGuessInstaller.guess("linux"),
                      (None, DebianInstaller, MacOsInstaller, DnfInstaller))

# ---------------------------------------------------------------------------


class TestInstallerDeps(unittest.TestCase):

    def setUp(self):
        self.__installer_deps = sppasInstallerDeps()

    # ---------------------------------------------------------------------------

    def test_features_ids(self):
        """Return the list of feature identifiers."""
        y = self.__installer_deps.features_ids()
        self.assertGreaterEqual(len(y), 3)
        self.assertIn("wxpython", y)
        self.assertIn("video", y)
        self.assertIn("stt", y)

        y = self.__installer_deps.features_ids("deps")
        self.assertIn("stt", y)
        self.assertNotIn("fra", y)

    # ---------------------------------------------------------------------------

    def test_set_enable(self):
        """Make a feature enabled."""
        y = self.__installer_deps.features_ids()
        self.__installer_deps.enable(y[0], True)
        self.assertTrue(self.__installer_deps.enable(y[0]))

    # ---------------------------------------------------------------------------

    def test_unset_enable(self):
        """Make a feature disabled."""
        y = self.__installer_deps.features_ids()
        self.__installer_deps.enable(y[0], False)
        self.assertFalse(self.__installer_deps.enable(y[0]))

        self.__installer_deps.enable(y[1], False)
        y = self.__installer_deps.features_ids()
        self.assertFalse(self.__installer_deps.enable(y[1]))

        self.__installer_deps.enable(y[2], False)
        y = self.__installer_deps.features_ids()
        self.assertFalse(self.__installer_deps.enable(y[2]))
