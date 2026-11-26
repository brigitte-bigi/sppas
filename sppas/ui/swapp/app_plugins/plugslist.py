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

from ..services.options import swappOptionsDialog

# ---------------------------------------------------------------------------

MSG_ABOUT = _("About")
MSG_CLOSE = _("Close")
MSG_CONFIGURE = _("Configure...")

# ---------------------------------------------------------------------------


class swappPluginsList(TagNode):
    """The installed plugins, one line each, in the order they are given.

    There is none when nothing is installed.

    """

    def __init__(self, parent: str, plugins: list, readmes: dict, selected: list,
                 configured: str, options: TagNode | None, form_id: str):
        """Create the list of the plugins.

        :param parent: (str) Identifier of the node the list is appended to
        :param plugins: (list of sppasPluginParam) The installed plugins, in their order
        :param readmes: (dict) key=identifier of a plugin, value=its README, empty if none
        :param selected: (list of str) The identifiers of the selected plugins
        :param configured: (str) The identifier of the plugin whose options are set, empty if none
        :param options: (TagNode|None) The container of the service of the options, for that plugin
        :param form_id: (str) Identifier of the form the fields and the buttons of a line belong to

        """
        super(swappPluginsList, self).__init__(parent, "plugins_list", "ul",
                                               attributes={"id": "plugins_list"})
        for _plugin in plugins:
            _key = _plugin.get_key()
            _options = None
            if _key == configured:
                _options = options
            self.append_child(swappPluginDescription(self.identifier, _plugin, readmes.get(_key, ""),
                                                     _key in selected, _options, form_id))

# ---------------------------------------------------------------------------


class swappPluginDescription(TagNode):
    """The line of one plugin, in columns, and its two dialogs.

    What selects it, with its name, and what sets its options; what opens
    its README; then what it says of itself. What is shown is what the plugin
    declares, and nothing is written of its own. Its options and its README
    are in dialogs of their own, which their buttons open.

    """

    def __init__(self, parent: str, plugin, readme: str, selected: bool, options: TagNode | None,
                 form_id: str):
        """Create the line of a plugin.

        :param parent: (str) Identifier of the node the line is appended to
        :param plugin: (sppasPluginParam) The plugin
        :param readme: (str) The README which comes with it, empty if none
        :param selected: (bool) The plugin is selected
        :param options: (TagNode|None) The container of the service of the options, None when they are not set
        :param form_id: (str) Identifier of the form the fields and the buttons of the line belong to

        """
        super(swappPluginDescription, self).__init__(parent, None, "li")
        _key = plugin.get_key()
        _flex = TagNode(self.identifier, None, "div", attributes={"class": "flex-panel"})
        self.append_child(_flex)

        # What selects it, with its name; then what sets its options.
        _column = TagNode(_flex.identifier, None, "div", attributes={"class": "flex-item width_25"})
        _flex.append_child(_column)
        _p = TagNode(_column.identifier, None, "p", attributes={"class": "plugins-name"})
        _column.append_child(_p)
        _switch = TagNode(_p.identifier, None, "label", attributes={"class": "switch", "for": "plugins_sel_" + _key})
        _p.append_child(_switch)
        _attributes = {"type": "checkbox", "role": "switch", "id": "plugins_sel_" + _key,
                       "name": "plugins_sel_" + _key, "value": "True", "form": form_id}
        if selected is True:
            _attributes["checked"] = None
        _switch.append_child(EmptyNode(_switch.identifier, None, "input", attributes=_attributes))
        _switch.append_child(HTMLNode(_switch.identifier, None, "span",
                                      attributes={"class": "switch-slider switch-no-text round"}))
        _p.append_child(HTMLNode(_p.identifier, None, "label", value=plugin.get_name(),
                                 attributes={"for": "plugins_sel_" + _key}))

        _p = TagNode(_column.identifier, None, "p")
        _column.append_child(_p)
        _configure = TagNode(_p.identifier, None, "button",
                             attributes={"type": "submit", "form": form_id, "name": "event_bake",
                                         "value": "plugins_options_" + _key,
                                         "class": "text-reveal-button", "data-icon": "parameters"})
        _p.append_child(_configure)
        _configure.append_child(HTMLNode(_configure.identifier, None, "span", value=MSG_CONFIGURE))

        # What opens its README.
        _column = TagNode(_flex.identifier, None, "div", attributes={"class": "flex-item width_10"})
        _flex.append_child(_column)
        _dialog_id = "plugin_about_" + _key
        _column.append_child(HTMLNode(_column.identifier, None, "button", value=MSG_ABOUT + "...",
                                      attributes={"type": "button", "aria-haspopup": "dialog",
                                                  "aria-controls": _dialog_id}))

        # What it says of itself.
        _column = TagNode(_flex.identifier, None, "div", attributes={"class": "flex-item width_65"})
        _flex.append_child(_column)
        _column.append_child(HTMLNode(_column.identifier, None, "p", value=plugin.get_descr()))

        # The window of its options, which the service of the options offers.
        self.append_child(swappOptionsDialog(self.identifier, "plugins_options_" + _key, plugin.get_name(), options))
        swappPluginDescription.__append_about(self, plugin, readme, _dialog_id)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __append_about(parent: TagNode, plugin, readme: str, dialog_id: str) -> None:
        """Append the About of a plugin, a window of three sections.

        Its title; the name and the icon of the plugin, and its README; and
        what closes it.

        """
        _dialog = TagNode(parent.identifier, dialog_id, "dialog",
                          attributes={"id": dialog_id, "class": "plugins-about", "aria-labelledby": dialog_id + "_h"})
        parent.append_child(_dialog)
        _title = TagNode(_dialog.identifier, None, "section")
        _dialog.append_child(_title)
        _title.append_child(HTMLNode(_title.identifier, None, "h4",
                                     value=MSG_ABOUT + " " + plugin.get_key() + "...",
                                     attributes={"id": dialog_id + "_h"}))

        _section = TagNode(_dialog.identifier, None, "section")
        _dialog.append_child(_section)
        # The icon is a file of the folder of the plugin: its address is
        # relative, as the one of every image the server serves.
        if len(plugin.get_icon()) > 0:
            _icon = os.path.relpath(os.path.join(plugin.get_directory(), plugin.get_icon()))
            _section.append_child(EmptyNode(_section.identifier, None, "img", attributes={"alt": "", "src": _icon}))
        _section.append_child(HTMLNode(_section.identifier, None, "p", value=plugin.get_name()))
        if len(readme) > 0:
            _section.append_child(HTMLNode(_section.identifier, None, "pre", value=html.escape(readme)))

        # A form of the dialog closes it, without a script.
        _actions = TagNode(_dialog.identifier, None, "section")
        _dialog.append_child(_actions)
        _form = TagNode(_actions.identifier, None, "form", attributes={"method": "dialog"})
        _actions.append_child(_form)
        _form.append_child(HTMLNode(_form.identifier, None, "button", value=MSG_CLOSE,
                                    attributes={"type": "submit", "class": "action-button"}))
