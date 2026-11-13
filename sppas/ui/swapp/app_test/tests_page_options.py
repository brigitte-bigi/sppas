# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_test.tests_page_options.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The page which tests the service of the options.

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


"""

from __future__ import annotations
import logging

from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.src.structs.baseoption import sppasOption
from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.swapp_base.swapp_response import swappBaseResponse
from sppas.ui.swapp.services.options import swappOptionsManager

from .tests_view import swappTestsBaseView

# ---------------------------------------------------------------------------

MSG_TITLE = "Test of the service of the options"
MSG_APP_TITLE = "What an app receives"
MSG_APP_TEXT = ("This page is an app which has no work of its own: it hands "
                "six options over to the service, one of each kind, and shows "
                "below what the service gives back. What the person sees above "
                "is the container of the service, and nothing of it is built "
                "here.")

JS_VALUE = (
    "import { OnLoadManager, LinkController } from "
    f"'/{swapp_settings.wexa_statics}js/wexa.js';"
    """

OnLoadManager.addLoadFunction(() => {
    new LinkController().handleLinksWithParameters(["home_button"]);
});

"""
)

# ---------------------------------------------------------------------------


class swappTestOptionsResponseRecipe(swappBaseResponse):
    """Bake the page which tests the service of the options.

    The page holds what an app holds of the service -- its manager -- and
    does what an app does with it: it hands its options over, offers it the
    events, appends its container, and asks for its options back.

    """

    def __init__(self, name="TestOptions", tree=None,
                 title=sg.__name__ + " Test of the options"):
        """Create the recipe of the page.

        :param name: (str) Name of the body main content

        """
        self.__manager = None
        super(swappTestOptionsResponseRecipe, self).__init__(name, tree, title)

    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Return the name of the page."""
        return "test_options.html"

    # -----------------------------------------------------------------------

    @staticmethod
    def name() -> str:
        """Return the name of the test."""
        return "The service of the options"

    # -----------------------------------------------------------------------

    @staticmethod
    def description() -> str:
        """Return a short description of the test."""
        return ("What an app lets one set, what a person gives, and what the "
                "app gets back.")

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed content of the page."""
        super().create()

        _view = swappTestsBaseView(self._htree, MSG_TITLE, JS_VALUE)
        _view.append_back_link_button(self._htree.body_nav)

        self.__manager = swappOptionsManager(self._htree.body_main.identifier,
                                             swappTestOptionsResponseRecipe.__options())

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Answer the events of a request.

        The events are offered to the service: this page has no event of its
        own.

        :param events: (dict) key=event_name, value=event_value
        :return: (bool) True when the whole page has to be baked again

        """
        logging.debug(" >>>>> Page {} -- Process events: {} <<<<<< "
                      "".format(swappTestOptionsResponseRecipe.page(), events))
        self._status.code = 200
        self.__manager.consumes(events)

        return True

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Create the content of the page.

        The container of the service is asked for and appended; what this
        page adds is under it: the options, as the service gives them back.

        """
        self.comment("Body content")
        self._htree.body_main.clear_children()
        self._htree.body_main.append_child(self.__manager.container())

        _h2 = HTMLNode(self._htree.body_main.identifier, None, "h2",
                       value=MSG_APP_TITLE)
        self._htree.body_main.append_child(_h2)
        _p = HTMLNode(self._htree.body_main.identifier, None, "p",
                      value=MSG_APP_TEXT)
        self._htree.body_main.append_child(_p)

        _list = TagNode(self._htree.body_main.identifier, None, "ul")
        self._htree.body_main.append_child(_list)
        for _option in self.__manager.options_for_app():
            _given = "{}: {!r}".format(_option.get_key(), _option.get_value())
            _list.append_child(HTMLNode(_list.identifier, None, "li", value=_given))

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __options() -> list:
        """Return the options this page hands over: one of each kind.

        They are the ones the test of the panel of the desktop interface
        declares.

        :return: (list of sppasOption)

        """
        _o1 = sppasOption("bool_test1", option_type="bool", option_value=False)
        _o1.set_text("Test a bool with False value")
        _o2 = sppasOption("bool_test2", option_type="bool", option_value=True)
        _o2.set_text("Test a bool with True value")
        _o3 = sppasOption("int_test", option_type="int", option_value=5)
        _o3.set_text("Test an int with '5' value")
        _o4 = sppasOption("float_test", option_type="float", option_value=0.20)
        _o4.set_text("Test a float with '0.2' value")
        _o5 = sppasOption("text_test", option_type="str", option_value="")
        _o5.set_text("Test a text with empty value")
        _o6 = sppasOption("file_test", option_type="filename", option_value="")
        _o6.set_text("Test a filename selection")

        return [_o1, _o2, _o3, _o4, _o5, _o6]
