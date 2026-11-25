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

from .plugins_record import swappPluginsRecord
from .plugins_view import swappPluginsView

# ---------------------------------------------------------------------------


class swappPluginsController:
    """Read the task a request carries, and answer it.

    It is called once per request, and holds nothing afterward. What is
    installed is shown at every request, each plugin with the README which
    comes with it.

    """

    def __init__(self, model, view: swappPluginsView):
        """Create the controller with what it is given.

        :param model: (swappPluginsModel) The model of Plugins
        :param view: (swappPluginsView) The view of Plugins
        :raises: sppasTypeError: The given view is not a swappPluginsView

        """
        if isinstance(view, swappPluginsView) is False:
            raise sppasTypeError(view, "swappPluginsView")
        self.__model = model
        self.__view = view
        self.__record = swappPluginsRecord()

    # -----------------------------------------------------------------------

    def handle(self, events: dict) -> None:
        """Do the task the events of a request ask for.

        :param events: (dict) What a page sent

        """
        self.__record = swappPluginsRecord()
        self.__record.parse(events)

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build its tree from the record: the plugins which are installed, and their README."""
        _plugins = self.__model.plugins()
        _readmes = dict()
        for _plugin in _plugins:
            _readmes[_plugin.get_key()] = self.__model.readme(_plugin.get_key())
        self.__record.show("plugins", _plugins)
        self.__record.show("readmes", _readmes)
        self.__view.populate_tree_content(self.__record)
