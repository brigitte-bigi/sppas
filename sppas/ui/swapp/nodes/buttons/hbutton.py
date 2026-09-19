# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.nodes.buttons.hbutton.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A button node with easy access to icons.

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
from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLButtonNode

from ...swapp_core.swapp_utils import swappImagesAccess

# ---------------------------------------------------------------------------


class swappHTMLButton(HTMLButtonNode):
    """Represent a button element.

    Overridden for an easier icon access and CSS properties added:
    "sp-button-text" and "sp-button-icon".

    """

    def __init__(self, parent, identifier, attributes=dict()):
        """Create an input node. Default type is 'text'.

        """
        super(swappHTMLButton, self).__init__(parent, identifier, attributes=attributes)

    # -----------------------------------------------------------------------

    def set_icon(self, icon_name, attributes=dict()):
        """Override. Set an icon to the button from its name in the app.

        Class sp-button-icon is added.

        :param icon_name: (str) Name of an icon in the app.
        :param attributes: (dict).

        """
        icon = swappImagesAccess.get_image_filename(name=icon_name)
        node = HTMLButtonNode.set_icon(self, icon, attributes)
        return node

# ---------------------------------------------------------------------------


class swappHTMLLink(HTMLNode):
    """Represent a link element carrying the content of a button.

    A card of the Dashboard leads to a page: it is a link, and it holds
    what a button holds -- an icon and a text.

    """

    def __init__(self, parent, identifier, attributes=dict()):
        """Create a link node.

        """
        super(swappHTMLLink, self).__init__(parent, identifier, "a", attributes=attributes)

        if "id" not in attributes:
            self.add_attribute("id", self.identifier)

    # -----------------------------------------------------------------------

    def set_icon(self, icon_name, attributes=dict()):
        """Set an icon to the link from its name in the app.

        :param icon_name: (str) Name of an icon in the app.
        :param attributes: (dict).

        """
        icon = swappImagesAccess.get_image_filename(name=icon_name)
        node = EmptyNode(self.identifier, None, "img")
        node.set_attribute("src", icon)
        node.set_attribute("alt", "")
        for key in attributes:
            node.set_attribute(key, attributes[key])
        self.append_child(node)
        return node

    # -----------------------------------------------------------------------

    def set_text(self, ident, text, attributes=dict()):
        """Set a text to the link.

        :param ident: (str) Identifier for the span text.
        :param text: (str) Link text.
        :param attributes: (dict)

        """
        node = HTMLNode(self.identifier, ident, "span", value=text, attributes=attributes)
        if ident is not None:
            node.set_attribute("id", ident)
            self.set_attribute("aria-labelledby", node.identifier)
        self.append_child(node)
        return node


# ---------------------------------------------------------------------------


class swappLinkButtonNode(HTMLNode):

    def __init__(self, parent_id, identifier: str, target_page: str):
        """Create a button to redirect to target page with data-href attribute.

        """
        super(swappLinkButtonNode, self).__init__(parent_id, identifier, "button")
        self.add_attribute("id", identifier)
        self.add_attribute("name", identifier)
        self.add_attribute("role", "link")
        self.add_attribute("type", "button")
        if len(target_page.strip()) > 0:
            self.add_attribute("data-href", target_page)

    def set_text(self, text):
        if len(text.strip()) > 0:
            _text = HTMLNode(self.identifier, None, "span", value=text)
            self.append_child(_text)

    def set_icon(self, identifier, full_path):
        _img = EmptyNode(self.identifier, identifier, "img")
        _img.set_attribute('src', full_path)
        _img.set_attribute('alt', "")
        self.append_child(_img)
        return _img
