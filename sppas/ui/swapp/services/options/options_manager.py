"""
:filename: sppas.ui.swapp.services.options.options_manager.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What an app holds of the service of the options.

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

from __future__ import annotations

from sppas.core.coreutils import sppasTypeError

from .options_controller import swappOptionsController
from .options_view import swappOptionsView

# ---------------------------------------------------------------------------


class swappOptionsManager:
    """What an app holds of this service, and the only object of it it holds.

    This service has no page of its own: it is reached by the app which
    placed its container. An app offers it the events it does not recognize,
    places its container in its page, and asks for its options back.

    """

    def __init__(self, parent: str, options: list):
        """Create what an app holds of this service.

        :param parent: (str) Identifier of the node the container is appended to
        :param options: (list of sppasOption) What the app lets one set
        :raises: sppasTypeError: The given parent is not a string

        """
        if isinstance(parent, str) is False:
            raise sppasTypeError(parent, "str")

        self.__view = swappOptionsView(parent)
        self.__controller = swappOptionsController(self.__view, options)

    # -----------------------------------------------------------------------

    def consumes(self, events: dict) -> bool:
        """Answer whether the events of a request were for this service.

        :param events: (dict) What a page sent
        :return: (bool) True when the events carried a task of this service, and it was done

        """
        if swappOptionsController.is_a_task(events) is False:
            return False

        self.__controller.handle(events)
        return True

    # -----------------------------------------------------------------------

    def options_for_app(self) -> list:
        """Return the options the app handed over, every one holding the value it holds.

        :return: (list of sppasOption)

        """
        return self.__controller.options_for_app()

    # -----------------------------------------------------------------------

    def container(self):
        """Return the container an app appends in its page.

        :return: (TagNode) One line per option of the set

        """
        self.__controller.populate_view()
        return self.__view.get_node()
