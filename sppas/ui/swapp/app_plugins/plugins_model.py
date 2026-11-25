"""
:filename: sppas.ui.swapp.app_plugins.plugins_model.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The model of the Plugins application.

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
import os

from sppas.src.plugins import sppasPluginsManager

# ---------------------------------------------------------------------------

# The file of the folder of a plugin which says of it what its card does not.
README = "README.txt"

# ---------------------------------------------------------------------------


class swappPluginsModel:
    """The plugins which are installed, as the domain of the plugins holds them.

    It is the only class of this application which speaks to the domain of
    the plugins: what a plugin declares of itself is read there, and nothing
    is added to it.

    """

    def __init__(self):
        """Create the model, and the domain of the plugins it reads.

        :raises: Exception: The domain of the plugins cannot be created

        """
        self.__manager = sppasPluginsManager()

    # -----------------------------------------------------------------------

    def plugins(self) -> list:
        """Return the plugins which are installed, in the order the domain of the plugins gives them.

        :return: (list of sppasPluginParam) Empty when none is installed

        """
        _plugins = list()
        for _id in self.__manager.get_plugin_ids():
            _plugins.append(self.__manager.get_plugin(_id))

        return _plugins

    # -----------------------------------------------------------------------

    def one(self, plugin_id: str):
        """Return one plugin, by its identifier.

        :param plugin_id: (str) Identifier of a plugin
        :return: (sppasPluginParam|None) None when no plugin bears that identifier

        """
        return self.__manager.get_plugin(plugin_id)

    # -----------------------------------------------------------------------

    def readme(self, plugin_id: str) -> str:
        """Return the README which comes with a plugin, as it is written.

        :param plugin_id: (str) Identifier of a plugin which is installed
        :return: (str) Empty when its folder holds none

        """
        _readme = os.path.join(self.__manager.get_plugin(plugin_id).get_directory(), README)
        if os.path.exists(_readme) is False:
            return ""
        with open(_readme, "r") as fp:
            return fp.read()
