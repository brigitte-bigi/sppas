# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_wkps.page_files.col_wkps.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The column "Workspaces" of the page "Files" for SPPAS Web UI.

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

    Copyright (C) 2011-2023  Brigitte Bigi, CNRS
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

import logging

from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import HTMLRadioBox
from whakerpy.htmlmaker import HTMLInputText

from sppas.ui import _
from sppas.ui.swapp.swapp_core.swappsg import swapp_wkps
from sppas.ui.swapp.nodes import swappHTMLButton
from sppas.ui.swapp.nodes import swappConfirmDialog

# ---------------------------------------------------------------------------
# List of displayed messages:


WKP = _("Workspace")

WKP_TITLE = _("Workspaces: ")
WKP_ACT_IMPORT = _("Import from")
WKP_ACT_EXPORT = _("Export to")
WKP_ACT_SAVE = _("Pin & Save")
WKP_ACT_RENAME = _("Rename")

WKP_MSG_ASK_NAME = _("New name of the workspace: ")
WKP_SWITCH_DISABLED = _("The current workspace contains locked files. You need to close files first.")

# ---------------------------------------------------------------------------


class swappWkpsNode(HTMLNode):
    """The column with workspaces of the page files.

    The identity of the node is 'column_files_wkps', and the name of each
    of its events starts with "wkps_".

    """

    def __init__(self, parent):
        super(swappWkpsNode, self).__init__(parent.identifier, "column_files_wkps", "div")
        self.add_attribute("class", self.identifier)

        # The HTML to design the UI
        self._create_content()

        # The javascript to manage the events (listen & notify)
        content = self.__script_for_events()
        js = HTMLNode(self.identifier, None, "script", value=content)
        self.append_child(js)

    # -----------------------------------------------------------------------
    # Setup events
    # -----------------------------------------------------------------------

    def process_event(self, event_name, event_value) -> bool:
        """Process the given events.

        :param event_name: (str)
        :param event_value: (str)
        :return: None

        """
        if event_name == "wkps_rename" and len(event_value) > 0:
            return self.perform_rename(event_value)
        if event_name == "wkps_listitem" and len(event_value) > 0:
            return self.perform_switch_to(event_value)

        return False

    # -----------------------------------------------------------------------

    def perform_rename(self, new_name):
        """Rename the current workspace.

        Changing the name of a workspace implies to change both its filename
        and the label of the corresponding button in the list.

        :param new_name: (str)

        """
        current_name = swapp_wkps.get_wkp_name()
        if current_name == new_name:
            logging.error("The given new name is the same than the existing one.")
            return False

        try:
            swapp_wkps.rename(new_name)
            form_list = self._wkps_list.get_child("wkps_listitem_form")
            wkp_node = form_list.get_nidx_child(swapp_wkps.get_wkp_current_index())
            # get the span text and set its new value
            span_node = wkp_node.get_nidx_child(1)  # 0=input, 1=span
            span_node.set_value(new_name)
        except Exception as e:
            # WkpRenameBlankError, WkpIdValueError
            # IndexError
            import traceback
            logging.error(traceback.format_exc())
            logging.error(str(e))

        return False

    # -----------------------------------------------------------------------

    def perform_switch_to(self, dest_name):
        """Swap the current workspace.

        :param dest_name: (src) Name of the workspace to switch to

        """
        # Can't switch if locked files. Files must be closed first.
        if swapp_wkps.data.has_locked_files():
            logging.error(WKP_SWITCH_DISABLED)
            return False

        # Save the currently displayed data (they correspond to the previous wkp)
        if swapp_wkps.get_wkp_current_index() == 0 and swapp_wkps.data.is_empty() is False:
            # User must confirm to really switch
            # response = Confirm(WKP_MSG_CONFIRM, WKP_MSG_CONFIRM_SWITCH)
            logging.error("Switch to another workspace needs to be confirmed.")
            return False

        # The user really intended to switch to. Update the current data.
        if swapp_wkps.get_wkp_current_index() > 0:
            # the 'Blank' workspace can't be saved... the others can
            try:
                swapp_wkps.save(swapp_wkps.data)
            except Exception as e:
                logging.error(str(e))
                # User must confirm to really switch
                # message = WKP_ACT_SAVECURRENT_ERROR.format(str(e))
                # response = Confirm(message, WKP_MSG_CONFIRM_SWITCH)
                return False

        try:
            # Change the index
            wkp_index = swapp_wkps.get_wkp_index(dest_name)
            # Load the data of the workspace from its file
            swapp_wkps.switch_to(wkp_index)
            # The "Files" & "Refs" columns need to be fully re-created (and our listitems)
            logging.info("Current workspace: {:s}".format(swapp_wkps.get_wkp_name()))
            return True
        except Exception as e:
            import traceback
            logging.error(traceback.format_exc())
            return False

    # -----------------------------------------------------------------------
    # Create and append the children nodes
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the HTML content of this column."""
        # A toolbar with action buttons
        wkps_toolbar = HTMLNode(self.identifier, None, "div", attributes={"class": "wkps_wkpbar"})
        self.append_child(wkps_toolbar)
        self.__create_toolbar(wkps_toolbar)

        # The list of available workspaces
        wkps_list = HTMLNode(self.identifier, "wkps_wkplist", "div", attributes={"class": "wkps_wkplist"})
        self.append_child(wkps_list)
        self.__create_list(wkps_list)

    @property
    def _wkps_list(self):
        return self.get_child("wkps_wkplist")

    # -----------------------------------------------------------------------

    def __create_toolbar(self, parent):
        """Add action buttons to the toolbar.

        Buttons are disabled until the event is implemented (i.e. listened
        and catch).

        """
        att = {"class": "wkps_title"}
        h1 = HTMLNode(parent.identifier, None, "h1", attributes=att, value=WKP_TITLE)
        parent.append_child(h1)

        tooltip = "Import a workspace from a file somewhere on the\n" \
                  "computer into the SPPAS workspaces folder (.wjson)."
        btn = self.__action_button(
            parent, "wkps_import", "wkps_wkpbar_item",
            icon_name="workspace_import", text=WKP_ACT_IMPORT,
            onclick="processEvent(this.id);", tooltip=tooltip)
        btn.set_attribute("accept", ".wjson")
        btn.set_attribute("disabled", None)

        tooltip = "Save the current workspace to a file, somewhere on the \n" \
                  "computer, not necessarily into the SPPAS workspaces folder."
        btn = self.__action_button(
            parent, "wkps_export", "wkps_wkpbar_item",
            icon_name="workspace_export", text=WKP_ACT_EXPORT,
            onclick="processEvent(this.id);", tooltip=tooltip)
        btn.set_attribute("accept", ".wjson")
        btn.set_attribute("disabled", None)

        tooltip = "Save the current workspace into the SPPAS workspaces folder.\n" \
                  "In case the Blank folder is currently used, a name is asked."
        btn = self.__action_button(
            parent, "wkps_pinsave", "wkps_wkpbar_item",
            icon_name="workspace_pin", text=WKP_ACT_SAVE,
            onclick="processEvent(this.id);", tooltip=tooltip)
        btn.set_attribute("disabled", None)

        self.__action_rename(parent)

    # -----------------------------------------------------------------------

    def __action_rename(self, parent):
        """Create the rename button and the dialog to fix the new name.

        """
        # Create a popup modal dialog to fix the new name. Not displayed.
        dlg = swappConfirmDialog(parent.identifier, WKP_MSG_ASK_NAME)
        name_node = HTMLInputText(dlg.content_node.identifier, "wkps_rename")
        name_node.set_attribute("placeholder", swapp_wkps.get_wkp_name())
        dlg.content_node.append_child(name_node)

        # Create the "Rename" button, which is used to display the popup.
        tooltip = "Allows to change the name of the current workspace\n" \
                  "except for the Blank one."
        attributes = dict()
        attributes["class"] = "wkps_wkpbar_item"
        attributes["onclick"] = "document.getElementById('"+dlg.identifier+"').style.display='block';"
        attributes["title"] = tooltip
        button_node = swappHTMLButton(parent.identifier, None, attributes)
        button_node.set_icon("workspace_rename")
        button_node.set_text("wkp_rename_button", WKP_ACT_RENAME)
        button_node.set_attribute("disabled", None)

        # Append both to the parent
        parent.append_child(button_node)
        parent.append_child(dlg)

    # -----------------------------------------------------------------------

    def __create_list(self, parent):
        """Add the list of current available workspaces.

        """
        box = HTMLRadioBox(parent.identifier, "wkps_listitem_form")
        box.add_attribute("class", "buttonbox_vertical")
        for i in range(swapp_wkps.get_size()):
            box.append_input(
                "wkps_listitem", swapp_wkps.get_wkp_name(i),
                text=None,
                checked=(i == swapp_wkps.get_wkp_current_index()))
        parent.append_child(box)

    # -----------------------------------------------------------------------

    @staticmethod
    def __action_button(parent, ident, class_name, icon_name, text, onclick, tooltip):
        """A specific button on which the ident is on the span text...

        """
        # The button is a child of a form
        attributes = dict()
        attributes['method'] = "POST"
        attributes['name'] = ident + "_form"
        attributes['id'] = ident + "_form"
        form = HTMLNode(parent.identifier, None, "form", attributes=attributes)
        parent.append_child(form)

        attributes = dict()
        attributes["name"] = ident
        attributes["id"] = ident
        attributes["class"] = class_name
        attributes["onclick"] = onclick
        attributes["title"] = tooltip
        button_node = swappHTMLButton(form.identifier, None, attributes)
        button_node.set_icon(icon_name)
        button_node.set_text(None, text)
        form.append_child(button_node)

        return button_node

    # -----------------------------------------------------------------------
    # HTML scripts content
    # -----------------------------------------------------------------------

    def __script_for_events(self):
        # Event listeners for buttons of the toolbar
        content = self.script_event_listener(("wkps_import", "wkps_export"), "change")
        content += self.script_event_listener(("wkps_pinsave",), "click")

        # Event listeners for the list of workspaces
        content += """
    const radioButtons = document.querySelectorAll('input[name="wkps_listitem"]');
    for (const radioButton of radioButtons) {
        radioButton.addEventListener('click', function (e) {
                processEvent("wkps_listitem");
            });
    }\n
        """
        
        # JS process events
        content += """
    function processEvent(ident) {
        notify(ident + "_form");
    }

        """

        return content

    # -----------------------------------------------------------------------

    def script_event_listener(self, idents, event_type, action="processEvent"):
        """Add a javascript event listener for each given identity.

        """
        html = "\n"
        for ident in idents:
            html += '    var ' + ident + ' = document.getElementById("' + ident + '");\n'
            html += '    ' + ident + '.addEventListener("' + event_type + '", ' + action + ');\n'

        return html
