"""
:filename: sppas.ui.swapp.nodes.dialogs.hdialog.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Base class for modal dialogs for SPPAS web-based apps.

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

from whakerpy.htmlmaker import HTMLNode

from sppas.ui import _
from ..buttons.hbutton import swappHTMLButton

# ----------------------------------------------------------------------------


MSG_ACTION_OK = _("Okay")
MSG_ACTION_CANCEL = _("Cancel")
MSG_ACTION_YES = _("Yes")
MSG_ACTION_NO = _("No",)
MSG_ACTION_APPLY = _("Apply")
MSG_ACTION_CLOSE = _("Close")
MSG_ACTION_SAVE = _("Save")

# -----------------------------------------------------------------------


class swappHTMLModalDialog(HTMLNode):
    """Represent a generic modal dialog tree root element.

    The dialog can be customized thanks to the following child nodes:
        - header_node
        - content_node
        - action_node

    """

    def __init__(self, parent, identifier):
        """Create an HTML node with <div> element and its content.

        """
        super(swappHTMLModalDialog, self).__init__(parent, identifier, "div")
        self.add_attribute("id", self.identifier)
        self.add_attribute("name", self.identifier)

        # Turn this node into a modal dialog window...
        self.add_attribute("class", "sp-modal-panel")
        attributes = dict()
        attributes['method'] = "POST"
        attributes['class'] = "sp-modal-content"
        form_node = HTMLNode(self.identifier, None, "form", attributes=attributes)
        self.append_child(form_node)

        # Fill-in the dialog box with public access to child nodes.
        # Create the header
        self.header_node = HTMLNode(
            form_node.identifier, "header_"+self.identifier[:5], "header")
        form_node.append_child(self.header_node)

        # Create the content
        self.content_node = HTMLNode(
            form_node.identifier, "content_"+self.identifier[:5], "main")
        form_node.append_child(self.content_node)

        # Create the action
        self.action_node = HTMLNode(
            form_node.identifier, "action_"+self.identifier[:5], "footer")
        form_node.append_child(self.action_node)

    # -----------------------------------------------------------------------
    # Customize the header
    # -----------------------------------------------------------------------

    def set_title(self, text, attributes=dict()):
        """Set a title text in the header from its filename.

        :param text: (str)
        :param attributes: (dict).

        """
        node = HTMLNode(self.header_node.identifier, None, "span", value=text, attributes=attributes)
        self.header_node.append_child(node)
        return node

    # -----------------------------------------------------------------------
    # Customize the action
    # -----------------------------------------------------------------------

    def add_action(self, name, onclick=None):
        """Add an action to the action panel.

        :param name: (str) One of: okay, cancel, close, yes, no, save.
        :param onclick: (str) JS
        :return: (swappHTMLButton)
        :raises: ValueError if name is unknown

        <button onclick="whatever();" id="df3ea8c9" name="df3ea8c9"
                data-icon="valid">
            <span class="button_text">Okay</span>
        </button>

        """
        attributes = dict()
        if onclick is not None:
            attributes["onclick"] = onclick
        if name in ("okay", "yes", "no", "save"):
            attributes["type"] = "submit"

        button_node = swappHTMLButton(self.action_node.identifier, None, attributes)
        if name == "cancel":
            button_node.add_attribute("data-icon", "cancel")
            button_node.set_text("cancel_action_button", MSG_ACTION_CANCEL)
        elif name == "close":
            button_node.add_attribute("data-icon", "close")
            button_node.set_text("close_action_button", MSG_ACTION_CLOSE)
        elif name == "okay":
            button_node.add_attribute("data-icon", "valid")
            button_node.set_text("ok_action_button", MSG_ACTION_OK)
        elif name == "yes":
            attributes["type"] = "submit"
            button_node.add_attribute("data-icon", "yes")
            button_node.set_text("yes_action_button", MSG_ACTION_YES)
        elif name == "no":
            button_node.add_attribute("data-icon", "no")
            button_node.set_text("no_action_button", MSG_ACTION_NO)
        elif name == "save":
            attributes["type"] = "submit"
            button_node.add_attribute("data-icon", "save")
            button_node.set_text("save_action_button", MSG_ACTION_SAVE)
        else:
            raise ValueError("Unknown action '{:s}".format(name))
        self.action_node.append_child(button_node)

        return button_node
