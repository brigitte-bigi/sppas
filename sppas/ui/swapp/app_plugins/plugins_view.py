"""
:filename: sppas.ui.swapp.app_plugins.plugins_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The view of the Plugins application.

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
from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_view import swappBaseView
from ..swapp_core.swappsg import swapp_settings
from ..swapp_core.swappsg import swapp_serverstate

from .plugins_record import swappPluginsRecord
from .plugslist import swappPluginsList

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Plugins")
MSG_INSTALL = _("Install")
MSG_DELETE = _("Delete")

# The script of the page, filled in with the folder of the scripts.
BODY_SCRIPT = """
        import {{ PluginsManager }} from '/{js}sppas.js';
        const pluginsManager = new PluginsManager();
        pluginsManager.handlePluginsManagerOnLoad();
"""

# ---------------------------------------------------------------------------


class swappPluginsView(swappBaseView):
    """View class responsible for populating the page of Plugins.

    It builds the header and the nav of the page, and the main content from
    a record: it decides nothing, and shows what it is given.

    """

    def __init__(self, tree: HTMLTree, form_id: str):
        """Initialize and populate the Plugins view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate
        :param form_id: (str) Identifier of the form which carries the record of the app
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappPluginsView: tree must be an instance of HTMLTree. "
                            "Got {} instead.".format(type(tree)))
        # Set before the base view populates the nav with it.
        self.__form_id = form_id
        super(swappPluginsView, self).__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self, *args, **kwargs):
        """Override. Add the sheet of Plugins."""
        super()._populate_head_css(*args, **kwargs)
        self._htree.head.link("stylesheet", swapp_settings.css + "app_plugins.css", link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page."""
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _form_id(self) -> str:
        """Override. Return the identifier of the form which carries the record of the app."""
        return self.__form_id

    # -----------------------------------------------------------------------

    def _populate_body_nav(self):
        """Override. Append the items of Plugins to the menu, in a section of their own.

        Installing and deleting a plugin happen where SPPAS runs on the
        machine of the person, and nowhere else: where it answers from a
        server, the section is not there.

        """
        if swapp_serverstate.local is True:
            _s = TagNode(self._htree.body_nav.identifier, None, "section")
            self._htree.body_nav.append_child(_s)
            for _identifier, _label in (("plugins_install", MSG_INSTALL), ("plugins_delete", MSG_DELETE)):
                _button = HTMLNode(_s.identifier, None, "button", value="<span>" + _label + "</span>")
                _button.add_attribute("id", _identifier)
                _button.add_attribute("type", "button")
                _button.add_attribute("aria-label", _label)
                _button.add_attribute("class", "menuitem")
                _s.append_child(_button)

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section."""
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT.format(js=swapp_settings.js))

    # -----------------------------------------------------------------------

    def populate_tree_content(self, record: swappPluginsRecord) -> None:
        """Populate the main content of the page from what the record says is to be shown.

        :param record: (swappPluginsRecord) What is to be shown

        """
        _shown = record.to_be_shown

        # The form of the page: every button of the page is tied to it by its
        # attribute "form".
        self._htree.body_main.append_child(TagNode(self._htree.body_main.identifier, None, "form",
                                                   attributes={"id": self.__form_id, "method": "post"}))

        self._htree.body_main.append_child(swappPluginsList(self._htree.body_main.identifier,
                                                            _shown.get("plugins", list()),
                                                            _shown.get("readmes", dict())))
