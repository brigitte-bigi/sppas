# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_test.tests_controller.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What answers a request of the index of the tests.

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

from .tests_model import swappTestsModel
from .tests_view import swappTestsView

# ---------------------------------------------------------------------------


class swappTestsController:
    """Answer a request of the index, and have the view build it.

    The index has nothing to do of its own: it shows the tests the model
    knows, and each of them answers on its own page.

    """

    def __init__(self, model: swappTestsModel, view: swappTestsView):
        """Create the controller with what it is given.

        :param model: (swappTestsModel) The tests this app serves
        :param view: (swappTestsView) The index

        """
        self.__model = model
        self.__view = view

    # -----------------------------------------------------------------------

    def handle(self, events: dict) -> bool:
        """Answer the events of a request.

        :param events: (dict) The events a request carries
        :return: (bool) True when the page has to be baked again

        """
        return False

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build the index from the tests of the model."""
        self.__view.populate_tree_content(self.__model.tests())
