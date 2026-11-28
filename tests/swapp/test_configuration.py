# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_configuration.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the page Configuration of swapp, on the machine of the person and on the web service.

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
from html.parser import HTMLParser

from sppas.core.config import cfg
from sppas.core.config import lgs
from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.pages.configuration_maker import swappConfigurationResponseRecipe

# ---------------------------------------------------------------------------

# The post of the Save button, with the level Debug chosen.
SAVE_DEBUG = {"event_bake": "handle_configuration_save",
              "configuration_log_level": "10"}

# ---------------------------------------------------------------------------


class swappFieldsetReader(HTMLParser):
    """Read the attributes of the fieldsets of a page."""

    def __init__(self, page: str):
        """Read the given page.

        :param page: (str) The HTML of a page

        """
        super(swappFieldsetReader, self).__init__(convert_charrefs=True)
        self.fieldsets = dict()
        self.feed(page)
        self.close()

    def handle_starttag(self, tag, attrs):
        _attributes = dict(attrs)
        if tag == "fieldset" and "id" in _attributes:
            self.fieldsets[_attributes["id"]] = _attributes

# ---------------------------------------------------------------------------


class TestLogLevel(unittest.TestCase):
    """The level of the log is changed on the machine of the person only."""

    def test_the_journal_on_the_machine(self):
        """The levels of the Journal can be chosen."""
        with mock.patch.object(swapp_settings, "served_locally", True):
            page = swappConfigurationResponseRecipe().bake({})
        attributes = swappFieldsetReader(page).fieldsets["configuration_journal"]
        self.assertNotIn("disabled", attributes)

    # -----------------------------------------------------------------------

    def test_the_journal_on_the_web_service(self):
        """The levels of the Journal can be chosen: the button which saves is the one disabled."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            page = swappConfigurationResponseRecipe().bake({})
        attributes = swappFieldsetReader(page).fieldsets["configuration_journal"]
        self.assertNotIn("disabled", attributes)

    # -----------------------------------------------------------------------

    def test_a_level_posted_on_the_machine(self):
        """The level posted is the one of the configuration and of the log."""
        with mock.patch.object(swapp_settings, "served_locally", True), \
                mock.patch.object(cfg, "set_interoperability"), \
                mock.patch.object(cfg, "save"), \
                mock.patch.object(cfg, "set_log_level") as cfg_level, \
                mock.patch.object(lgs, "set_log_level") as lgs_level:
            swappConfigurationResponseRecipe().bake(dict(SAVE_DEBUG))
        cfg_level.assert_called_once_with(10)
        lgs_level.assert_called_once_with(10)

    # -----------------------------------------------------------------------

    def test_a_level_posted_on_the_web_service(self):
        """A level posted anyway changes neither the configuration nor the log."""
        with mock.patch.object(swapp_settings, "served_locally", False), \
                mock.patch.object(cfg, "set_interoperability"), \
                mock.patch.object(cfg, "save"), \
                mock.patch.object(cfg, "set_log_level") as cfg_level, \
                mock.patch.object(lgs, "set_log_level") as lgs_level:
            swappConfigurationResponseRecipe().bake(dict(SAVE_DEBUG))
        cfg_level.assert_not_called()
        lgs_level.assert_not_called()


# ---------------------------------------------------------------------------


class TestConfigurationOnline(unittest.TestCase):
    """Served by the web service, the configuration cannot be saved."""

    def test_the_save_button_on_the_web_service(self):
        """Online, the button which saves is disabled, and the page says why; on the machine, it is not."""
        with mock.patch.object(swapp_settings, "served_locally", False):
            page = swappConfigurationResponseRecipe().bake({})
        self.assertIsNotNone(re.search(r'<button[^>]*value="handle_configuration_save"[^>]*disabled', page))
        self.assertIn("SPPAS online does not allow the configuration to be customized.", page)

        with mock.patch.object(swapp_settings, "served_locally", True):
            page = swappConfigurationResponseRecipe().bake({})
        self.assertIsNone(re.search(r'<button[^>]*value="handle_configuration_save"[^>]*disabled', page))
        self.assertNotIn("SPPAS online does not allow the configuration to be customized.", page)

    def test_nothing_is_saved_on_the_web_service(self):
        """A save posted anyway changes nothing of the configuration, and writes nothing."""
        with mock.patch.object(swapp_settings, "served_locally", False), \
                mock.patch.object(cfg, "set_interoperability") as interoperability, \
                mock.patch.object(cfg, "save") as save, \
                mock.patch.object(cfg, "set_log_level"), \
                mock.patch.object(lgs, "set_log_level"):
            swappConfigurationResponseRecipe().bake(dict(SAVE_DEBUG))
        interoperability.assert_not_called()
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
