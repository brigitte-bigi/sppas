"""
:filename: sppas.ui.swapp.app_plugins.plugins_controller.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The controller of the Plugins application.

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

from .plugins_view import swappPluginsView

# ---------------------------------------------------------------------------


class swappPluginsController:
    """Read the task a request carries, and answer it.

    It is called once per request, and holds nothing afterward. No task of
    this application is answered yet.

    """

    def __init__(self, view: swappPluginsView):
        """Create the controller with what it is given.

        :param view: (swappPluginsView) The view of Plugins
        :raises: sppasTypeError: The given view is not a swappPluginsView

        """
        if isinstance(view, swappPluginsView) is False:
            raise sppasTypeError(view, "swappPluginsView")
        self.__view = view

    # -----------------------------------------------------------------------

    def handle(self, events: dict) -> None:
        """Do the task the events of a request ask for: none is answered yet.

        :param events: (dict) What a page sent

        """
        pass

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build its tree."""
        self.__view.populate_tree_content()
