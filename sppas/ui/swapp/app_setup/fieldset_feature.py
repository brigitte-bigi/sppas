"""
:filename: sppas.ui.swapp.app_setup.fieldset_feature.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: Create a "Feature" fieldset node of the setup app.

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

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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

from sppas.core.coreutils import msg
from sppas.core.coreutils import info

from .base_fieldset_feature_type import swappSetupFeatureTypeFieldset

# ---------------------------------------------------------------------------


DEPS_FEATURES = info(514, "install")
LANG_FEATURES = info(515, "install")
ANNOT_FEATURES = info(516, "install")
SPIN_FEATURES = info(517, "install")

# ---------------------------------------------------------------------------


class swappSetupDepsFieldset(swappSetupFeatureTypeFieldset):
    """List of features of type 'deps'.

    """

    def __init__(self, parent, installer, uri: str = ""):
        super(swappSetupDepsFieldset, self).__init__(
            parent, "fieldset_deps", installer, "deps", DEPS_FEATURES, uri)
        self._msg = msg("Tools", "install")

# ---------------------------------------------------------------------------


class swappSetupLangFieldset(swappSetupFeatureTypeFieldset):
    """List of features of type 'lang'.

    """

    def __init__(self, parent, installer, uri: str = ""):
        super(swappSetupLangFieldset, self).__init__(
            parent, "fieldset_lang", installer, "lang", LANG_FEATURES, uri)
        self._msg = msg("Langs", "install")

# ---------------------------------------------------------------------------


class swappSetupAnnotFieldset(swappSetupFeatureTypeFieldset):
    """List of features of type 'annot'.

    """

    def __init__(self, parent, installer, uri: str = ""):
        super(swappSetupAnnotFieldset, self).__init__(
            parent, "fieldset_annot", installer, "annot", ANNOT_FEATURES, uri)
        self._msg = msg("Models", "install")

# ---------------------------------------------------------------------------


class swappSetupSpinOffFieldset(swappSetupFeatureTypeFieldset):
    """List of features of type 'spin'.

    """

    def __init__(self, parent, installer, uri: str = ""):
        super(swappSetupSpinOffFieldset, self).__init__(
            parent, "fieldset_spinoff", installer, "spin", SPIN_FEATURES, uri)
        self._msg = msg("Extras", "install")

