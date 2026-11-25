# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_swapp_help.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the help of the apps of swapp, as the page asks for it.

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

    "How the help of an app is shown", in the README of swapp. Every request
    is the one the page sends: the button which is pressed sends the fields
    of its form, read in the page the server answered. The accessibility
    parameters the page adds to the address are sent too.

"""

import time
import unittest

from sppas.ui.swapp.swapp_base.swapp_help import HELP_TASK
from sppas.ui.swapp.swapp_base.swapp_help import BACK_TASK
from sppas.ui.swapp.swapp_base.swapp_help import HELP_ID
from sppas.ui.swapp.swapp_base.swapp_help import HELP_FORM_ID
from sppas.ui.swapp.swapp_base.swapp_help import MSG_NO_HELP
from sppas.ui.swapp.swapp_base.swapp_help_button import HELP_BUTTON_ID
from sppas.ui.swapp.swapp_base.swapp_process import swappProcess
from sppas.ui.swapp.swapp_base.swapp_process import PROCESS_FIELD
from sppas.ui.swapp.app_annotate.annotate_maker import swappAnnotateResponseRecipe
from sppas.ui.swapp.app_plugins.plugins_maker import swappPluginsResponseRecipe
from sppas.ui.swapp.app_convert.convert_maker import swappConvertResponseRecipe
from sppas.ui.swapp.app_dashboard.dashboard_maker import swappDashboardResponseRecipe
from sppas.ui.swapp.app_setup.setup_maker import swappSetupResponseRecipe
from sppas.ui.swapp.app_test.tests_maker import swappTestsResponseRecipe
from sppas.ui.swapp.pages.trace_maker import swappTraceResponseRecipe

from tests.swapp.page_requests import swappPageFields
from tests.swapp.page_requests import main_of

# ---------------------------------------------------------------------------

# What the page adds to the address it sends a form to.
ACCESSIBILITY = {"wexa_theme": "swapp", "wexa_icons": "icons"}

# Every app, with the form its Help button sends and whether it has a document.
APPS = ((swappDashboardResponseRecipe, HELP_FORM_ID, True),
        (swappSetupResponseRecipe, HELP_FORM_ID, False),
        (swappConvertResponseRecipe, "convert_form", True),
        (swappAnnotateResponseRecipe, "annotate_form", True),
        (swappPluginsResponseRecipe, "plugins_form", True),
        (swappTestsResponseRecipe, HELP_FORM_ID, False))

# ---------------------------------------------------------------------------


def press(recipe, page: str, name: str, value: str, identifier: str = "", changed: dict | None = None) -> str:
    """Press a button of the page, and return the page the server answers.

    :param recipe: The bakery of the app
    :param page: (str) The page the button stands in
    :param name: (str) Name of the button
    :param value: (str) Value of the button
    :param identifier: (str) Identifier of the button, empty for the first one
    :param changed: (dict) What the person changed in the fields before, by name
    :return: (str)

    """
    _events = swappPageFields(page).submitted(name, value, identifier)
    if changed is not None:
        for _name in changed:
            _events[_name] = changed[_name]
    for _name in ACCESSIBILITY:
        _events[_name] = ACCESSIBILITY[_name]

    return recipe.bake(_events)

# ---------------------------------------------------------------------------


class TestHelpButton(unittest.TestCase):
    """The Help button of the nav of every app."""

    def test_the_button_sends_the_form_of_the_app(self):
        """It is a submit button of the task of the help, tied to the form of the app or to its own."""
        for recipe_class, form_id, documented in APPS:
            with self.subTest(app=recipe_class.__name__):
                page = recipe_class().bake({})
                button = swappPageFields(page).button(HELP_BUTTON_ID)
                self.assertEqual("submit", button.get("type"))
                self.assertEqual("event_bake", button.get("name"))
                self.assertEqual(HELP_TASK, button.get("value"))
                self.assertEqual(form_id, button.get("form"))
                self.assertEqual("h", button.get("aria-keyshortcuts"))
                if form_id == HELP_FORM_ID:
                    self.assertIn('id="{:s}"'.format(HELP_FORM_ID), page)

    # -----------------------------------------------------------------------

    def test_a_page_keeps_its_disabled_button(self):
        """The Journal is a page: its Help button is a link, disabled, and not the one of an app."""
        page = swappTraceResponseRecipe().bake({})
        self.assertIn('id="{:s}"'.format(HELP_BUTTON_ID), page)
        self.assertEqual(dict(), swappPageFields(page).button(HELP_BUTTON_ID))
        start = page.find('id="{:s}"'.format(HELP_BUTTON_ID))
        tag = page[page.rfind("<", 0, start):page.find(">", start)]
        self.assertTrue(tag.startswith("<a"))
        self.assertIn('aria-disabled="true"', tag)

# ---------------------------------------------------------------------------


class TestHelpAndBack(unittest.TestCase):
    """The help, then the way back, for every app, as its page asks for them."""

    def test_the_help_is_shown_in_place_of_the_app(self):
        """The main content is the help: the document of the app, or what is said in its place."""
        for recipe_class, form_id, documented in APPS:
            with self.subTest(app=recipe_class.__name__):
                recipe = recipe_class()
                page = recipe.bake({})
                helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID)
                main = main_of(helped)
                self.assertIn('id="{:s}"'.format(HELP_ID), main)
                if documented is True:
                    self.assertNotIn(MSG_NO_HELP, main)
                    self.assertIn("<h1>", main)
                else:
                    self.assertIn(MSG_NO_HELP, main)

    # -----------------------------------------------------------------------

    def test_the_help_carries_what_the_form_sent(self):
        """Every field the form of the app sent is in the form of the help, hidden; the task and the accessibility are not."""
        for recipe_class, form_id, documented in APPS:
            with self.subTest(app=recipe_class.__name__):
                recipe = recipe_class()
                page = recipe.bake({})
                sent = swappPageFields(page).submitted("event_bake", HELP_TASK, HELP_BUTTON_ID)
                helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID)
                carried = swappPageFields(main_of(helped)).hidden()
                expected = dict(sent)
                expected.pop("event_bake")
                self.assertEqual(expected, carried)

    # -----------------------------------------------------------------------

    def test_the_nav_button_is_the_way_back_while_the_help_is_shown(self):
        """The same button, the same form, the same key: what it sends and says change."""
        for recipe_class, form_id, documented in APPS:
            with self.subTest(app=recipe_class.__name__):
                recipe = recipe_class()
                page = recipe.bake({})
                helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID)
                button = swappPageFields(helped).button(HELP_BUTTON_ID)
                self.assertEqual(BACK_TASK, button.get("value"))
                self.assertEqual(form_id, button.get("form"))
                self.assertEqual("arrow-up", button.get("data-icon"))
                self.assertEqual("h", button.get("aria-keyshortcuts"))

                back = press(recipe, helped, "event_bake", BACK_TASK, HELP_BUTTON_ID)
                button = swappPageFields(back).button(HELP_BUTTON_ID)
                self.assertEqual(HELP_TASK, button.get("value"))
                self.assertEqual("help", button.get("data-icon"))

    # -----------------------------------------------------------------------

    def test_back_by_the_button_of_the_help(self):
        """The Back button of the help gives the default view of the app again."""
        for recipe_class, form_id, documented in APPS:
            with self.subTest(app=recipe_class.__name__):
                recipe = recipe_class()
                page = recipe.bake({})
                helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID)
                back = press(recipe, main_of(helped), "event_bake", BACK_TASK)
                self.assertNotIn('id="{:s}"'.format(HELP_ID), main_of(back))
                self.assertEqual(main_of(page), main_of(back))

    # -----------------------------------------------------------------------

    def test_back_by_the_button_of_the_nav(self):
        """The Help button of the nav, which is the way back, gives the default view of the app again."""
        for recipe_class, form_id, documented in APPS:
            with self.subTest(app=recipe_class.__name__):
                recipe = recipe_class()
                page = recipe.bake({})
                helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID)
                back = press(recipe, helped, "event_bake", BACK_TASK, HELP_BUTTON_ID)
                self.assertNotIn('id="{:s}"'.format(HELP_ID), main_of(back))
                self.assertEqual(main_of(page), main_of(back))

# ---------------------------------------------------------------------------


class TestWhatIsDecidedComesBack(unittest.TestCase):
    """What the person decided before asking for the help is there when she comes back."""

    def test_convert(self):
        """The destination format and the general options."""
        recipe = swappConvertResponseRecipe()
        page = recipe.bake({})
        helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID,
                       {"convert_destination": ".eaf", "convert_override": "True"})
        back = press(recipe, main_of(helped), "event_bake", BACK_TASK)

        fields = swappPageFields(back).fields_of("convert_form")
        self.assertEqual(".eaf", fields.get("convert_destination"))
        self.assertEqual("True", fields.get("convert_override"))

    # -----------------------------------------------------------------------

    def test_annotate(self):
        """The merge option and the extension, from the six steps."""
        recipe = swappAnnotateResponseRecipe()
        page = recipe.bake({})
        helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID,
                       {"annotate_merge": "True", "annotate_ext_ANNOT": ".TextGrid"})
        back = press(recipe, main_of(helped), "event_bake", BACK_TASK)

        fields = swappPageFields(back).fields_of("annotate_form")
        self.assertEqual("True", fields.get("annotate_merge"))
        self.assertEqual(".TextGrid", fields.get("annotate_ext_ANNOT"))

    # -----------------------------------------------------------------------

    def test_annotate_from_the_annotations_of_a_type(self):
        """An annotation selected in the panel of a type is selected when she comes back to the six steps."""
        recipe = swappAnnotateResponseRecipe()
        page = recipe.bake({})
        annotations = press(recipe, page, "event_bake", "annotate_annotations_STANDALONE")
        helped = press(recipe, annotations, "event_bake", HELP_TASK, HELP_BUTTON_ID,
                       {"annotate_ann_momel": "True"})
        back = press(recipe, main_of(helped), "event_bake", BACK_TASK)

        fields = swappPageFields(back).fields_of("annotate_form")
        self.assertEqual("True", fields.get("annotate_ann_momel"))
        self.assertIn('id="annotate_actions_panel"', main_of(back))

# ---------------------------------------------------------------------------


class TestHelpWhileAProcessGoes(unittest.TestCase):
    """A long process is modal: its help is not shown while it goes."""

    @staticmethod
    def wait(seconds, progress=None):
        """What a process performs: it takes its time."""
        time.sleep(seconds)

    # -----------------------------------------------------------------------

    def test_the_help_is_the_way_back_while_a_process_goes(self):
        """A request which names a process going and asks for the help is answered by the default view."""
        recipe = swappConvertResponseRecipe()
        page = recipe.bake({})
        process = swappProcess.start(TestHelpWhileAProcessGoes.wait, (0.5,))
        helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID, {PROCESS_FIELD: process.name})
        self.assertNotIn('id="{:s}"'.format(HELP_ID), main_of(helped))

        time.sleep(0.7)
        helped = press(recipe, page, "event_bake", HELP_TASK, HELP_BUTTON_ID, {PROCESS_FIELD: process.name})
        self.assertIn('id="{:s}"'.format(HELP_ID), main_of(helped))


if __name__ == "__main__":
    unittest.main()
