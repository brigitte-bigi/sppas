# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_setup.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the choices a person makes in the Setup.

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

    A person goes forward in the Setup, checks a feature, goes back, and
    comes forward again: what she chose is what she sees, and what she sees
    is what is installed. Nothing is installed by these tests.

"""

from __future__ import annotations
import json
import unittest
from unittest import mock
from html.parser import HTMLParser

import sppas.ui.swapp.app_setup.setup_maker as setup_maker
from sppas.ui.swapp.app_setup.setup_model import swappSetupModel

# ---------------------------------------------------------------------------

# The index of the fieldset of the languages, and the type of its features.
LANG_INDEX = 3
LANG_TYPE = "lang"

# ---------------------------------------------------------------------------


class InputReader(HTMLParser):
    """Read the inputs a piece of a page holds, by their identifier."""

    def __init__(self):
        super().__init__()
        self.inputs = dict()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "input" and "id" in attributes:
            self.inputs[attributes["id"]] = attributes

# ---------------------------------------------------------------------------


class TestSetupChoices(unittest.TestCase):
    """What a person chose, once she went back and came forward again."""

    def setUp(self):
        self.models = list()
        with mock.patch.object(setup_maker, "lgs"), \
                mock.patch.object(setup_maker, "swappSetupModel", side_effect=self.make_model):
            self.recipe = setup_maker.swappSetupResponseRecipe()
        self.recipe.bake(dict())
        self.installer = self.models[0].installer

        # The citation and the license are accepted, up to the languages.
        self.accept("check_ref")
        self.accept("check_prod")
        self.browse("next_fieldset", 0)
        self.accept("check_license")
        self.browse("next_fieldset", 1)
        self.browse("next_fieldset", 2)

        self.feature = self.installer.features_ids(LANG_TYPE)[0]
        self.default = self.installer.enable(self.feature)

    # -----------------------------------------------------------------------

    def make_model(self):
        """Make the model of the Setup, and keep it to read what is installed."""
        self.models.append(swappSetupModel())
        return self.models[-1]

    # -----------------------------------------------------------------------

    def check(self, name: str) -> None:
        """Send what a page sends when a checkbox is clicked."""
        self.recipe.bake({"check_name": name})

    # -----------------------------------------------------------------------

    def accept(self, name: str) -> None:
        """Click the checkbox of an acceptance, unless it is accepted already."""
        if self.models[0].is_accepted(name) is False:
            self.check(name + "_input")

    # -----------------------------------------------------------------------

    def browse(self, event_name: str, index: int) -> dict:
        """Send what a page sends to change of fieldset, and return the answer."""
        self.recipe.bake({"event_name": event_name, "event_value": str(index)})
        return json.loads(self.recipe.get_data())

    # -----------------------------------------------------------------------

    def go_away_and_come_back(self) -> bool:
        """Go two fieldsets forward, come back to the languages, and return
        whether the server wrote the feature as checked.
        """
        self.browse("next_fieldset", LANG_INDEX)
        self.browse("next_fieldset", LANG_INDEX + 1)
        self.browse("prev_fieldset", LANG_INDEX + 2)
        answered = self.browse("prev_fieldset", LANG_INDEX + 1)

        reader = InputReader()
        for written in answered.values():
            reader.feed(str(written))
        name = "feature_" + self.feature + "_input"
        self.assertIn(name, reader.inputs)
        return "checked" in reader.inputs[name]

    # -----------------------------------------------------------------------

    def test_te1_a_choice_is_shown_again_when_she_comes_back(self):
        """TE1. A feature she changed is written as she left it, when the
        server writes its fieldset again.
        """
        self.check("feature_" + self.feature + "_input")
        shown = self.go_away_and_come_back()
        self.assertEqual(not self.default, shown)

    # -----------------------------------------------------------------------

    def test_te2_what_is_installed_is_what_is_shown(self):
        """TE2. Once she came back, the feature is to be installed if and
        only if the page shows it checked.
        """
        self.check("feature_" + self.feature + "_input")
        shown = self.go_away_and_come_back()
        self.assertEqual(shown, self.installer.enable(self.feature))

    # -----------------------------------------------------------------------

    def test_te3_choosing_again_what_was_lost_keeps_the_choice(self):
        """TE3. She came back, and does what the page asks of her: when her
        choice is not shown, she makes it again. It is what is installed.
        """
        self.check("feature_" + self.feature + "_input")
        shown = self.go_away_and_come_back()
        if shown == self.default:
            self.check("feature_" + self.feature + "_input")
        self.assertEqual(not self.default, self.installer.enable(self.feature))

# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
