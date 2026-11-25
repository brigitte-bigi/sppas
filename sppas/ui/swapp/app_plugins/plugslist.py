"""
:filename: sppas.ui.swapp.app_plugins.plugslist.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The parts of the page of the Plugins application.

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
import html
from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.ui import _

# ---------------------------------------------------------------------------

MSG_ABOUT = _("About")

# ---------------------------------------------------------------------------


class swappPluginsList(TagNode):
    """The installed plugins, one under another: one card per plugin.

    There is none when nothing is installed.

    """

    def __init__(self, parent: str, plugins: list, readmes: dict):
        """Create the list of the plugins.

        :param parent: (str) Identifier of the node the list is appended to
        :param plugins: (list of sppasPluginParam) The installed plugins, in their order
        :param readmes: (dict) key=identifier of a plugin, value=its README, empty if none

        """
        super(swappPluginsList, self).__init__(parent, "plugins_list", "ul",
                                               attributes={"id": "plugins_list",
                                                           "class": "cards-panel apps-panel"})
        for _plugin in plugins:
            self.append_child(swappPluginDescription(self.identifier, _plugin,
                                                     readmes.get(_plugin.get_key(), "")))

# ---------------------------------------------------------------------------


class swappPluginDescription(TagNode):
    """One plugin: its icon, its name, what it says of itself, what runs it, and its About.

    What is shown is what the plugin declares, and nothing is written of its
    own. The About is a dialog of the card, which its button opens.

    """

    def __init__(self, parent: str, plugin, readme: str):
        """Create the card of a plugin.

        :param parent: (str) Identifier of the node the card is appended to
        :param plugin: (sppasPluginParam) The plugin
        :param readme: (str) The README which comes with it, empty if none

        """
        super(swappPluginDescription, self).__init__(parent, None, "li", attributes={"class": "card app"})
        # The icon is a file of the folder of the plugin: its address is
        # relative, as the one of every image the server serves.
        if len(plugin.get_icon()) > 0:
            _icon = os.path.relpath(os.path.join(plugin.get_directory(), plugin.get_icon()))
            self.append_child(EmptyNode(self.identifier, None, "img",
                                        attributes={"class": "app-background-img", "alt": "", "src": _icon}))
        _content = TagNode(self.identifier, None, "div", attributes={"class": "app-content flow"})
        self.append_child(_content)
        _container = TagNode(_content.identifier, None, "div", attributes={"class": "app-container flow"})
        _content.append_child(_container)
        _container.append_child(HTMLNode(_container.identifier, None, "h2", value=plugin.get_name(),
                                         attributes={"class": "app-title"}))
        _container.append_child(HTMLNode(_container.identifier, None, "p", value=plugin.get_descr(),
                                         attributes={"class": "app-description"}))
        # What runs the plugin bears its identifier, as in the desktop interface.
        _content.append_child(HTMLNode(_content.identifier, None, "button", value=plugin.get_key(),
                                       attributes={"type": "button", "class": "action-button app-button"}))

        _dialog_id = "plugin_about_" + plugin.get_key()
        _content.append_child(HTMLNode(_content.identifier, None, "button", value=MSG_ABOUT + "...",
                                       attributes={"type": "button", "class": "app-button",
                                                   "aria-haspopup": "dialog", "aria-controls": _dialog_id}))

        # The About: the name and the icon of the plugin, and its README.
        _dialog = TagNode(self.identifier, _dialog_id, "dialog",
                          attributes={"id": _dialog_id, "aria-labelledby": _dialog_id + "_h"})
        self.append_child(_dialog)
        _dialog.append_child(HTMLNode(_dialog.identifier, None, "h4",
                                      value=MSG_ABOUT + " " + plugin.get_key() + "...",
                                      attributes={"id": _dialog_id + "_h"}))
        if len(plugin.get_icon()) > 0:
            _dialog.append_child(EmptyNode(_dialog.identifier, None, "img",
                                           attributes={"alt": "", "src": _icon}))
        _dialog.append_child(HTMLNode(_dialog.identifier, None, "p", value=plugin.get_name()))
        if len(readme) > 0:
            _dialog.append_child(HTMLNode(_dialog.identifier, None, "pre", value=html.escape(readme)))
