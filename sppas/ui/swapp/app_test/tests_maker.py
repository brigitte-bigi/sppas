# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_test.tests_maker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The index of the tests of swapp.

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

from sppas.core.config import sg
from sppas.ui.swapp.swapp_base.swapp_response import swappBaseResponse

from .tests_model import swappTestsModel
from .tests_view import swappTestsBaseView
from .tests_view import swappTestsView
from .tests_controller import swappTestsController

# ---------------------------------------------------------------------------

MSG_TITLE = "Tests of swapp"

# ---------------------------------------------------------------------------


class swappTestsResponseRecipe(swappBaseResponse):
    """Bake the index of the tests.

    It shows the tests the model knows and leads to them. Nothing is tested
    here: each test answers on its own page.

    """

    def __init__(self, name="Tests", tree=None, title=sg.__name__ + " Tests"):
        """Create the recipe of the index.

        :param name: (str) Name of the body main content

        """
        self.__model = swappTestsModel()
        self.__view = None
        self.__controller = None
        super(swappTestsResponseRecipe, self).__init__(name, tree, title)
        self._bake()

    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Return the name of the page."""
        return "test.html"

    # -----------------------------------------------------------------------

    @staticmethod
    def description() -> str:
        """Return a short description of the response."""
        return "The index of the tests of the swapp of SPPAS."

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed content of the index."""
        super().create()

        swappTestsBaseView(self._htree, MSG_TITLE)
        for _link in self.__model.links():
            self._htree.head.add_links(_link)

        self.__view = swappTestsView(self._htree.body_main)
        self.__controller = swappTestsController(self.__model, self.__view)

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Answer the events of a request.

        :param events: (dict) key=event_name, value=event_value
        :return: (bool) True when the whole page has to be baked again

        """
        logging.debug(" >>>>> Page test.html -- Process events: {} <<<<<< "
                      "".format(events))
        self._status.code = 200

        return self.__controller.handle(events)

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Override. Create the content of the index."""
        self.comment("Body content")
        self.__controller.populate_view()

