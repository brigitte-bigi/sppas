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

from ..nodes import swappProgressBar
from ..services.options import swappOptionsDialog
from ..swapp_base.swapp_process import PROCESS_FIELD

# ---------------------------------------------------------------------------

MSG_ABOUT = _("About")
MSG_CONFIGURE = _("Configure...")
MSG_PROGRESS = _("Run")
MSG_RESULTS_CAPTION = _("One line per file of the run")
MSG_FILE = _("File")
MSG_STATUS = _("Status")
MSG_RESULT = _("Result")
MSG_DONE = _("done")
MSG_FAILED = _("failed")

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
        """Append the About of a plugin, a modal dialog.

        Its title, on one line: the icon of the plugin, and About its name;
        then its README.

        """
        _dialog = TagNode(parent.identifier, dialog_id, "dialog",
                          attributes={"id": dialog_id, "class": "hidden-alert", "aria-labelledby": dialog_id + "_h"})
        parent.append_child(_dialog)

        _title = TagNode(_dialog.identifier, None, "h2", attributes={"class": "flex-panel"})
        _dialog.append_child(_title)
        # The icon is a file of the folder of the plugin: its address is
        # relative, as the one of every image the server serves.
        if len(plugin.get_icon()) > 0:
            _icon = os.path.relpath(os.path.join(plugin.get_directory(), plugin.get_icon()))
            _title.append_child(EmptyNode(_title.identifier, None, "img",
                                          attributes={"alt": "Plugin logo",
                                                      "src": _icon,
                                                      "class": "flex-item small-logo width_10"}
                                          )
                                )
        _text = HTMLNode(_title.identifier, None, "span", value=MSG_ABOUT + " " + plugin.get_name())
        _text.add_attribute("class", "flex-item width_80")
        _title.append_child(_text)
        if len(readme) > 0:
            _dialog.append_child(HTMLNode(_dialog.identifier, None, "pre", value=html.escape(readme)))

# ---------------------------------------------------------------------------


class swappPluginRunPanel(TagNode):
    """The runs of the selected plugins: their progress while they go, then their results.

    While the runs go: the progress bar, named for a screen reader by what it
    measures, and the names the page follows them by. Once they are over:
    plugin by plugin, one line per file which is done, with what the plugin
    said about it, as it said it, and the files which appeared.

    """

    def __init__(self, parent: str, form_id: str, report: str, process: str, runs: list, addresses: dict):
        """Create the panel of the runs.

        :param parent: (str) Identifier of the node the panel is appended to
        :param form_id: (str) Identifier of the form the names of the runs belong to
        :param report: (str) Name of the report of the runs
        :param process: (str) Name of the process of the runs, empty when they are not going
        :param runs: (list of swappPluginRun) The runs, with their results; empty while they go
        :param addresses: (dict) The address of a produced file, by name, when the person is not on the machine which wrote it

        """
        super(swappPluginRunPanel, self).__init__(parent, None, "section")

        # The bar measures the whole runs, and it is named so for a screen
        # reader only. The header is given its node: it holds the plugin
        # which is running, and the text which file is treated.
        if len(process) > 0:
            _progress = swappProgressBar(self.identifier)
            _progress.set_header("")
            _progress.set_text("")
            _bar = _progress.get_node()
            _bar.get_child("percent_progress").add_attribute("aria-label", MSG_PROGRESS)
            _bar.insert_child(0, HTMLNode(_bar.identifier, "progress_header", "h3",
                                          attributes={"id": "progress_header"}))
            self.append_child(_bar)
            for _name, _value in (("plugins_report", report), (PROCESS_FIELD, process)):
                self.append_child(EmptyNode(self.identifier, None, "input",
                                            attributes={"type": "hidden", "form": form_id,
                                                        "name": _name, "value": _value}))

        for _run in runs:
            swappPluginRunPanel.__append_run(self, _run, addresses)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __append_run(parent: TagNode, run, addresses: dict) -> None:
        """Append the results of one run: the plugin, then one line per file which is done.

        :param parent: (TagNode) The panel
        :param run: (swappPluginRun) The run
        :param addresses: (dict) The address of a produced file, by name

        """
        parent.append_child(HTMLNode(parent.identifier, None, "h3", value=run.plugin))
        _table = TagNode(parent.identifier, None, "table")
        parent.append_child(_table)
        _table.append_child(HTMLNode(_table.identifier, None, "caption", value=MSG_RESULTS_CAPTION))

        _head = TagNode(_table.identifier, None, "thead")
        _table.append_child(_head)
        _tr = TagNode(_head.identifier, None, "tr")
        _head.append_child(_tr)
        for _text in (MSG_FILE, MSG_STATUS, MSG_RESULT):
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=_text, attributes={"scope": "col"}))

        _body = TagNode(_table.identifier, None, "tbody")
        _table.append_child(_body)
        for _result in run.results:
            _tr = TagNode(_body.identifier, None, "tr")
            _body.append_child(_tr)
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=os.path.basename(_result.file),
                                      attributes={"scope": "row"}))
            _icon = "no"
            _status = MSG_FAILED
            if _result.done is True:
                _icon = "yes"
                _status = MSG_DONE
            _td = TagNode(_tr.identifier, None, "td")
            _tr.append_child(_td)
            _td.append_child(HTMLNode(_td.identifier, None, "span", value="",
                                      attributes={"data-icon": _icon, "role": "img", "aria-label": _status}))

            # What the plugin said, as it said it, then what appeared.
            _td = TagNode(_tr.identifier, None, "td")
            _tr.append_child(_td)
            _td.append_child(HTMLNode(_td.identifier, None, "pre", value=html.escape(_result.said)))
            if len(_result.produced) > 0:
                _ul = TagNode(_td.identifier, None, "ul")
                _td.append_child(_ul)
                for _produced in _result.produced:
                    _li = TagNode(_ul.identifier, None, "li")
                    _ul.append_child(_li)
                    _name = os.path.basename(_produced)
                    if _produced in addresses:
                        # The file was written where the person is not: the
                        # name leads to it, and the browser is told to keep
                        # it under that name instead of showing it.
                        _li.append_child(HTMLNode(_li.identifier, None, "a", value=_name,
                                                  attributes={"href": addresses[_produced], "download": _name}))
                    else:
                        _li.set_value(_name)
