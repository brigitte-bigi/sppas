# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_swapp_nav.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the nav of the apps and of the pages of swapp, as the page is served.

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

    "How the nav of a view is built", in the README of swapp. The nav is
    read in the page the server answers to a first request.

"""

import re
import unittest
from unittest import mock
from html.parser import HTMLParser

from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.swapp_core.swappsg import swapp_wxstate

from sppas.ui.swapp.swapp_base.swapp_help_button import HELP_BUTTON_ID
from sppas.ui.swapp.app_annotate.annotate_maker import swappAnnotateResponseRecipe
from sppas.ui.swapp.app_plugins.plugins_maker import swappPluginsResponseRecipe
from sppas.ui.swapp.app_convert.convert_maker import swappConvertResponseRecipe
from sppas.ui.swapp.app_dashboard.dashboard_maker import swappDashboardResponseRecipe
from sppas.ui.swapp.app_setup.setup_maker import swappSetupResponseRecipe
from sppas.ui.swapp.app_test.tests_maker import swappTestsResponseRecipe
from sppas.ui.swapp.app_test.tests_page_swapp import swappTestSwappResponseRecipe
from sppas.ui.swapp.pages.about_maker import swappAboutResponseRecipe
from sppas.ui.swapp.pages.cite_maker import swappCiteResponseRecipe
from sppas.ui.swapp.pages.configuration_maker import swappConfigurationResponseRecipe
from sppas.ui.swapp.pages.feedback_maker import swappFeedbackResponseRecipe
from sppas.ui.swapp.pages.trace_maker import swappTraceResponseRecipe

# ---------------------------------------------------------------------------

# What changes the look of the page, first in every nav.
APPEARANCE = ["pin-menu", "btn-css-theme", "btn-contrast", "btn-color"]

# The items every view has, second in every nav, in this order.
COMMON = ["link-home_button", "link-trace_button", HELP_BUTTON_ID]

# ---------------------------------------------------------------------------


class swappNavReader(HTMLParser):
    """Read the sections of the nav of a page, and the items each one holds."""

    def __init__(self, page: str):
        """Read the given page.

        :param page: (str) The HTML of a page

        """
        super(swappNavReader, self).__init__(convert_charrefs=True)
        self.sections = list()
        self.items = dict()
        self.forms_in_sections = 0
        self.__in_nav = False
        self.__in_section = False
        self.feed(page)
        self.close()

    def handle_starttag(self, tag, attrs):
        _attributes = dict(attrs)
        if tag == "nav":
            self.__in_nav = True
        elif self.__in_nav is True and tag == "section":
            self.sections.append(list())
            self.__in_section = True
        elif self.__in_section is True and tag == "form":
            self.forms_in_sections += 1
        elif self.__in_nav is True and tag in ("a", "button") and "id" in _attributes:
            self.sections[-1].append(_attributes["id"])
            self.items[_attributes["id"]] = (tag, _attributes)

    def handle_endtag(self, tag):
        if tag == "nav":
            self.__in_nav = False
        elif tag == "section":
            self.__in_section = False

# ---------------------------------------------------------------------------


class TestNav(unittest.TestCase):
    """The same first two sections in every nav, then the items of the view in a third one."""

    def test_the_apps(self):
        """The Help of an app is a button which sends the form of the app, or a form of its own."""
        expected = ((swappDashboardResponseRecipe, ["exit-menu"]),
                    (swappAnnotateResponseRecipe, None),
                    (swappPluginsResponseRecipe, None),
                    (swappConvertResponseRecipe, None),
                    (swappSetupResponseRecipe, ["link-sppas_button"]),
                    (swappTestsResponseRecipe, None),
                    (swappTestSwappResponseRecipe, ["link-tests_button"]))
        for recipe_class, own in expected:
            with self.subTest(app=recipe_class.__name__):
                # The items of an app are the ones of SPPAS on the machine of the person.
                with mock.patch.object(swapp_settings, "served_locally", True):
                    nav = swappNavReader(recipe_class().bake({}))
                sections = [APPEARANCE, COMMON]
                if own is not None:
                    sections.append(own)
                self.assertEqual(sections, nav.sections)
                # A form holds no place among the items.
                self.assertEqual(0, nav.forms_in_sections)
                tag, attributes = nav.items[HELP_BUTTON_ID]
                self.assertEqual("button", tag)
                self.assertNotIn("aria-disabled", attributes)

    # -----------------------------------------------------------------------

    def test_the_form_the_help_of_an_app_sends(self):
        """Annotate and Convert send their own form with the Help."""
        for recipe_class in (swappAnnotateResponseRecipe, swappConvertResponseRecipe):
            with self.subTest(app=recipe_class.__name__):
                nav = swappNavReader(recipe_class().bake({}))
                tag, attributes = nav.items[HELP_BUTTON_ID]
                self.assertEqual(recipe_class.form_id(), attributes["form"])

    # -----------------------------------------------------------------------

    def test_the_pages(self):
        """The Help of a page is at the same place, disabled."""
        expected = ((swappAboutResponseRecipe, None),
                    (swappCiteResponseRecipe, None),
                    (swappConfigurationResponseRecipe, None),
                    (swappFeedbackResponseRecipe, None),
                    (swappTraceResponseRecipe, ["close-tab_button"]))
        for recipe_class, own in expected:
            with self.subTest(page=recipe_class.__name__):
                nav = swappNavReader(recipe_class().bake({}))
                sections = [APPEARANCE, COMMON]
                if own is not None:
                    sections.append(own)
                self.assertEqual(sections, nav.sections)
                tag, attributes = nav.items[HELP_BUTTON_ID]
                self.assertEqual("a", tag)
                self.assertEqual("true", attributes["aria-disabled"])

# ---------------------------------------------------------------------------


class TestExit(unittest.TestCase):
    """The Exit of the Dashboard, on the machine of the person and on the web service."""

    def tearDown(self):
        swapp_wxstate.exit_granted = False
        swapp_wxstate.exit_pending = False

    # -----------------------------------------------------------------------

    def test_the_item_on_the_web_service(self):
        """On the web service, the Exit item is disabled; on the machine, it is not."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            nav = swappNavReader(swappDashboardResponseRecipe().bake({}))
        tag, attributes = nav.items["exit-menu"]
        self.assertEqual("button", tag)
        self.assertIn("disabled", attributes)

        with mock.patch.object(swapp_settings, "served_locally", True):
            nav = swappNavReader(swappDashboardResponseRecipe().bake({}))
        tag, attributes = nav.items["exit-menu"]
        self.assertNotIn("disabled", attributes)

    def test_the_close_on_the_web_service(self):
        """On the web service, a close is refused: nothing is granted, nothing waits."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            swappDashboardResponseRecipe().bake({"event_bake": "close"})
        self.assertIs(False, swapp_wxstate.exit_granted)
        self.assertIs(False, swapp_wxstate.exit_pending)

    def test_the_close_on_the_machine(self):
        """On the machine, without the wx interface, a close is granted."""
        with mock.patch.object(swapp_settings, "served_locally", True):
            swappDashboardResponseRecipe().bake({"event_bake": "close"})
        self.assertIs(True, swapp_wxstate.exit_granted)


# ---------------------------------------------------------------------------


class TestJournalOnline(unittest.TestCase):
    """Served by a web service, SPPAS has no Journal: its item stays, disabled, and nothing invites to it."""

    def test_the_item_on_the_web_service(self):
        """On the web service, the Journal item is disabled; on the machine, it is not."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            nav = swappNavReader(swappConvertResponseRecipe().bake({}))
        tag, attributes = nav.items["link-trace_button"]
        self.assertEqual("button", tag)
        self.assertIn("disabled", attributes)

        with mock.patch.object(swapp_settings, "served_locally", True):
            nav = swappNavReader(swappConvertResponseRecipe().bake({}))
        tag, attributes = nav.items["link-trace_button"]
        self.assertNotIn("disabled", attributes)

    def test_no_invitation_on_the_web_service(self):
        """On the web service, the Dashboard holds no dialog inviting to open the Journal."""
        with mock.patch.object(swapp_settings, "license_agreement", True):
            with mock.patch.object(swapp_settings, "served_locally", False):
                self.assertNotIn('id="trace_dialog"', swappDashboardResponseRecipe().bake({}))
            with mock.patch.object(swapp_settings, "served_locally", True):
                self.assertIn('id="trace_dialog"', swappDashboardResponseRecipe().bake({}))


# ---------------------------------------------------------------------------


class TestLicenseOnline(unittest.TestCase):
    """Served by a web service, the license asks for no validation: using the page is accepting."""

    def test_the_license_on_the_web_service(self):
        """Online, the license is shown at each display, its box checked and disabled; locally, with its button, once."""
        with mock.patch.object(swapp_settings, "license_agreement", True), \
                mock.patch.object(swapp_settings, "served_locally", False):
            page = swappDashboardResponseRecipe().bake({})
        self.assertIn('id="agreement_dialog"', page)
        self.assertNotIn('id="agree_button"', page)
        self.assertIsNotNone(re.search(r'<input[^>]*id="agree_check"[^>]*checked[^>]*disabled', page))

        with mock.patch.object(swapp_settings, "license_agreement", False), \
                mock.patch.object(swapp_settings, "served_locally", True):
            page = swappDashboardResponseRecipe().bake({})
        self.assertIn('id="agree_button"', page)

        with mock.patch.object(swapp_settings, "license_agreement", True), \
                mock.patch.object(swapp_settings, "served_locally", True):
            self.assertNotIn('id="agreement_dialog"', swappDashboardResponseRecipe().bake({}))

    def test_no_agreement_kept_on_the_web_service(self):
        """Online, an agreement sent to the server is not kept for anybody."""
        with mock.patch.object(swapp_settings, "license_agreement", False), \
                mock.patch.object(swapp_settings, "served_locally", False):
            swappDashboardResponseRecipe().bake({"event_bake": "handle_licence_agreement"})
            self.assertIs(False, swapp_settings.license_agreement)


if __name__ == "__main__":
    unittest.main()
