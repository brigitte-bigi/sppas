"""
:filename: test_swapp_bakery.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test the secret names an app of swapp is reached at online.

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

import re
import unittest
from unittest import mock

from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.swapp_base.swapp_redirect import swappRedirectResponse
from sppas.ui.swapp.app_annotate.app_annotate import swappAnnotateWebData
from sppas.ui.swapp.app_convert.app_convert import swappConvertWebData
from sppas.ui.swapp.app_convert.convert_maker import swappConvertResponseRecipe
from sppas.ui.swapp.app_plugins.app_plugins import swappPluginsWebData
from sppas.ui.swapp.app_plugins.plugins_maker import swappPluginsResponseRecipe
from sppas.ui.swapp.app_annotate.annotate_maker import swappAnnotateResponseRecipe
from sppas.ui.swapp.app_test.app_test import swappTestsWebData
from sppas.ui.swapp.app_test.tests_maker import swappTestsResponseRecipe
from sppas.ui.swapp.swapp_core.swapps import WEB_APPLICATIONS

# ---------------------------------------------------------------------------

# What the page leading to a secret name of Convert holds.
LEADS_TO = r'href="(convert_[0-9a-f]{32}\.html)'

# ---------------------------------------------------------------------------


class TestSecretPage(unittest.TestCase):
    """Online, what an app does is reached at a secret name; locally, at its default page."""

    def test_online_the_default_page_leads_to_a_secret_name(self):
        """The default page leads to a secret name, and the secret name is the app."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            data = swappConvertWebData()
            self.assertTrue(data.is_page("convert.html"))
            response = data.bake_response("convert.html")
            self.assertIsInstance(response, swappRedirectResponse)
            page = response.bake({})
            secret = re.search(LEADS_TO + '"', page)
            self.assertIsNotNone(secret)
            # The page follows its link, whose address WhakerPy signs: no meta element leads elsewhere.
            self.assertIn("location.replace(link.href)", page)
            self.assertNotIn("http-equiv", page)
            self.assertTrue(data.is_page(secret.group(1)))
            self.assertIsInstance(data.bake_response(secret.group(1)), swappConvertResponseRecipe)

    def test_online_a_secret_name_is_drawn_at_each_request(self):
        """Two requests of the default page lead to two secret names."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            response = swappConvertWebData().bake_response("convert.html")
            first = re.search(LEADS_TO, response.bake({})).group(1)
            second = re.search(LEADS_TO, response.bake({})).group(1)
        self.assertNotEqual(first, second)

    def test_online_what_the_reader_chose_is_carried(self):
        """The parameters of the reader are carried to the secret name, and nothing else."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            response = swappConvertWebData().bake_response("convert.html")
            page = response.bake({"wexa_theme": "dark", "wexa_contrast": "high", "convert_override": "on"})
        self.assertIsNotNone(re.search(LEADS_TO + r'\?wexa_theme=dark&wexa_contrast=high"', page))
        self.assertNotIn("convert_override", page)

    def test_online_what_is_not_a_secret_name(self):
        """A name which is not the default page followed by 32 hexadecimal digits is not a page."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            data = swappConvertWebData()
            for name in ("convert_.html", "convert_" + "a" * 31 + ".html", "convert_" + "g" * 32 + ".html",
                         "convert_" + "a" * 32 + ".htm", "annotate_" + "a" * 32 + ".html"):
                with self.subTest(name=name):
                    self.assertFalse(data.is_page(name))
                    self.assertIsNone(data.bake_response(name))

    def test_online_every_app(self):
        """Annotate, Convert and Plugins: the default page leads to a secret name of the app."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            for data_class, page_name in ((swappAnnotateWebData, "annotate.html"),
                                          (swappConvertWebData, "convert.html"),
                                          (swappPluginsWebData, "plugins.html")):
                with self.subTest(page=page_name):
                    data = data_class()
                    response = data.bake_response(page_name)
                    self.assertIsInstance(response, swappRedirectResponse)
                    stem = page_name[:-len(".html")]
                    secret = re.search(r'href="(' + stem + r'_[0-9a-f]{32}\.html)"', response.bake({}))
                    self.assertIsNotNone(secret)
                    self.assertTrue(data.is_page(secret.group(1)))

    def test_online_an_app_in_development_is_not_protected(self):
        """An app declared with show set to False is reached at its default page online."""
        entry = None
        for web_app in WEB_APPLICATIONS:
            if web_app.bakery is swappTestsWebData:
                entry = web_app
        self.assertIsNotNone(entry)

        with mock.patch.object(swapp_settings, "served_locally", False):
            with mock.patch.object(entry, "show", False):
                data = swappTestsWebData()
                self.assertIsInstance(data.bake_response("test.html"), swappTestsResponseRecipe)
                self.assertFalse(data.is_page("test_" + "a" * 32 + ".html"))
            with mock.patch.object(entry, "show", True):
                self.assertIsInstance(swappTestsWebData().bake_response("test.html"), swappRedirectResponse)

    def test_locally_the_default_page_is_the_app(self):
        """Locally, the default page is the app, and a secret name is not a page."""
        with mock.patch.object(swapp_settings, "served_locally", True):
            data = swappConvertWebData()
            self.assertIsInstance(data.bake_response("convert.html"), swappConvertResponseRecipe)
            self.assertFalse(data.is_page("convert_" + "a" * 32 + ".html"))
            self.assertIsNone(data.bake_response("convert_" + "a" * 32 + ".html"))

# ---------------------------------------------------------------------------


class TestSignedAddress(unittest.TestCase):
    """What signs the address of a page online never reaches the app."""

    def test_the_signature_is_not_an_event_of_the_app(self):
        """Annotate, Convert and Plugins bake their page when the address carries ts and sig."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            for recipe_class in (swappAnnotateResponseRecipe, swappConvertResponseRecipe,
                                 swappPluginsResponseRecipe):
                with self.subTest(app=recipe_class.__name__):
                    recipe = recipe_class()
                    page = recipe.bake({"ts": "1795809811", "sig": "5f8c0970", "wexa_theme": "swapp"})
                    self.assertNotIn("Unexpected status", page)
                    self.assertEqual(200, recipe.status.code)


# ---------------------------------------------------------------------------


class TestReaderChoices(unittest.TestCase):
    """What a reader chose to be shown with is kept by a local server only."""

    def test_kept_locally_only(self):
        """Online, the theme, the color and the contrast a reader chose are not kept by the server."""
        for local in (False, True):
            with self.subTest(served_locally=local):
                with mock.patch.object(swapp_settings, "served_locally", local), \
                        mock.patch.object(swapp_settings, "accessibility_theme", ""), \
                        mock.patch.object(swapp_settings, "accessibility_color", ""), \
                        mock.patch.object(swapp_settings, "accessibility_contrast", ""):
                    swappConvertResponseRecipe().bake({"theme": "aurora", "accessibility_color": "dark",
                                                       "accessibility_contrast": "contrast"})
                    kept = (swapp_settings.accessibility_theme, swapp_settings.accessibility_color,
                            swapp_settings.accessibility_contrast)
                if local is True:
                    self.assertEqual(("aurora", "dark", "contrast"), kept)
                else:
                    self.assertEqual(("", "", ""), kept)


if __name__ == "__main__":
    unittest.main()
