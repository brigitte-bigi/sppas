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

from ..services.options import swappOptionsManager

from .plugins_record import swappPluginsRecord
from .plugins_view import swappPluginsView

# ---------------------------------------------------------------------------

# The task which shows the options of a plugin carries its identifier, which
# is the identifier of their dialog as well: the container of the service of
# the options is appended to it.
OPTIONS_TASK = "plugins_options_"

# ---------------------------------------------------------------------------


class swappPluginsController:
    """Read the task a request carries, and answer it.

    It is called once per request, and holds nothing afterward. What is
    installed is shown at every request, each plugin with the README which
    comes with it, and the options of the plugin which is set.

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
        self.__options = None
        # The plugin whose options are set, empty if none.
        self.__configured = ""

    # -----------------------------------------------------------------------

    def handle(self, events: dict) -> None:
        """Do the task the events of a request ask for.

        :param events: (dict) What a page sent

        """
        # The options of every plugin, each one with its value by default:
        # the record sets on them what the page transmitted.
        _options = dict()
        for _plugin in self.__model.plugins():
            _options[_plugin.get_key()] = self.__model.options_of(_plugin.get_key())
        self.__record = swappPluginsRecord(_options)
        self.__record.parse(events)

        # The options of a plugin are handed to the service of the options,
        # which shows and checks them. Applying them validates the plugin:
        # their values are taken back, they are applied, and it is selected.
        # Giving them up invalidates it: they are no longer applied, and it
        # is not selected.
        self.__options = None
        self.__configured = ""
        if self.__record.task.startswith(OPTIONS_TASK) is True:
            _key = self.__record.task[len(OPTIONS_TASK):]
            if self.__model.one(_key) is not None:
                self.__configured = _key
                self.__options = swappOptionsManager(OPTIONS_TASK + _key, self.__record.get_options(_key))
                self.__options.consumes(events)
                if "options_validate" in events:
                    self.__record.set_options(_key, self.__options.options_for_app())
                    self.__record.set_applied(_key, True)
                    self.__record.select(_key)
                elif "options_close" in events:
                    self.__record.set_applied(_key, False)
                    self.__record.unselect(_key)

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build its tree from the record.

        The plugins which are installed and their README are shown, and the
        options of the plugin which is set, with what the page writes of that
        plugin.

        """
        _plugins = self.__model.plugins()
        _readmes = dict()
        for _plugin in _plugins:
            _readmes[_plugin.get_key()] = self.__model.readme(_plugin.get_key())
        self.__record.show("plugins", _plugins)
        self.__record.show("readmes", _readmes)

        if len(self.__configured) > 0:
            self.__record.show("configured", self.__configured)
            self.__record.show("options", self.__options.container())
            self.__record.show("values", self.__record.serialize_plugin(self.__configured))

        self.__view.populate_tree_content(self.__record)
