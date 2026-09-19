# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.nodes.inputs.hcheckbox.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A checkbox node for a custom input of type checkbox.

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

Requirements:

- javascript function checkbox_switch(checkbox);
- css property "focusable"

"""

from __future__ import annotations
from whakerpy.htmlmaker import HTMLNode

# ---------------------------------------------------------------------------


class swappHTMLCheckboxNode(HTMLNode):
    """A customized checkbox.

    Requires a javascript management of checkboxes and the css "focusable".
    The function is invoked each time the input is checked. The function then
    POST a form with the input to the server.

    :Example:

    Python code:
        > checkbox = HTMLCheckboxNode(self.identifier, "check_01", "I agree")
        > checkbox.check(True)
        > self.append_child(checkbox)

    HTML serialized result:
        <label for="check_01_input" class="focusable">
            <input id="check_01_input" type="checkbox" name="check_01_input" value="I agree"/>
            <span>I agree</span>
        </label>

    Posted event when clicked:
        key="check_01_input_posted", value="I+agree"

    """

    def __init__(self, parent_id, identifier="und", text="", uri = ""):
        """Create the Checkbox node.

        :param parent_id: (str) Identifier of the parent node
        :param identifier: (str) Identifier of the checkbox
        :param text: (str) Text of the checkbox. It's also the value of the input.
        :param uri: (str) URI of the checkbox, i.e., the page name.

        """
        super(swappHTMLCheckboxNode, self).__init__(parent_id, identifier, "label")
        check_input_id = self.identifier + "_input"
        self.add_attribute("for", check_input_id)
        self.add_attribute("class", "focusable")

        # Create the input checkbox
        input_attributes = dict()
        input_attributes['id'] = check_input_id
        input_attributes['type'] = "checkbox"
        input_attributes['name'] = check_input_id
        # value is what is really received by the server after a POST event.
        input_attributes['value'] = text
        # input_attributes["onkeydown"] = (
        #    f"if (event.key == 'Enter') {{event.target.checked = !event.target.checked; checkbox_switch(this, {uri});}};"
        # )
        # input_attributes["onchange"] = f"checkbox_switch(this, '{uri}');"
        check_input = HTMLNode(self.identifier, check_input_id, "input", attributes=input_attributes)
        self.append_child(check_input)

        # Create the text value of the label
        span_node = HTMLNode(self.identifier, None, "span", value=text)
        self.append_child(span_node)

    # -----------------------------------------------------------------------

    @property
    def _check_input(self):
        """Return the node of the input checkbox."""
        return self.get_child(self.identifier + "_input")

    # -----------------------------------------------------------------------

    def add_input_attribute(self, key: str, value: str):
        """Add an attribute to the input checkbox."""
        _c = self.get_child(self.identifier + "_input")
        _c.add_attribute(key, value)

    # -----------------------------------------------------------------------

    def check(self, value=True):
        """Check the box or un-check it.

        Add the checked information both in the label and in the checkbox.

        :param value: (bool) True to turn the input into checked state

        """
        c = self._check_input
        # Remove the existing state (if any)
        if c.has_attribute("checked") is True:
            c.remove_attribute("checked")

        # Set the given state (if any)
        if value is True:
            c.set_attribute("checked", None)

    # -----------------------------------------------------------------------

    def is_checked(self):
        """Return True if the box is currently checked."""
        return self._check_input.has_attribute("checked")
