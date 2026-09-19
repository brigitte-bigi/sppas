"""
:filename: sppas.ui.swapp.app_setup.actions_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A node to represent the action toolbar of the Setup app.

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

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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
from whakerpy.htmlmaker import HTMLNode

from sppas.core.coreutils import msg
from sppas.ui.swapp import swappImagesAccess

# -----------------------------------------------------------------------


MSG_ACTION_BACK = msg('Back', "ui")
MSG_ACTION_NEXT = msg('Next', "ui")
MSG_ACTION_INSTALL = msg('Install', "ui")
MSG_ACTION_REDO = msg('Redo', "ui")
MSG_ACTION_CANCEL = msg('Cancel', "ui")
MSG_ACTION_EXIT = msg('Exit', "ui")

# -----------------------------------------------------------------------


class swappSetupActionsNode(HTMLNode):
    """Append an action bar which allows browsing through fieldsets.

    """

    def __init__(self, parent_id: str, fieldsets: list, current: object, install: bool = False):
        """Create a panel for the Setup app footer.

        :param parent_id: (str) Identifier
        :param fieldsets: (list of setup fieldsets)
        :param current: (swappSetupBaseFieldset) The currently enabled fieldset
        :param install: (bool) Whether the button "Install" is displayed or not

        """
        super(swappSetupActionsNode, self).__init__(
            parent_id, "actions_section", "section",
            attributes={"class": "panel actions-panel width_70 center",
                        "id": "actions_section"})
        cur_idx = fieldsets.get_index(current)

        # --- b1 = Redo or Previous
        if cur_idx + 1 == len(fieldsets):
            b1 = self.__create_button_svg("redo_btn", MSG_ACTION_REDO, "redo")
        else:
            b1 = self.__create_button_svg("prev_btn", MSG_ACTION_BACK, "back")
            if cur_idx == 0:
                # There's no previous fieldset for the 1st one,
                # or the installation is finished (and do not allow to re-starts a new one).
                b1.add_attribute("disabled", None)

        # --- b2 = Next or Install
        if install is True:
            b2 = self.__create_button_svg("install_btn", MSG_ACTION_INSTALL, "install")
            b2.add_attribute("class", "install-button")
        else:
            b2 = self.__create_button_svg("next_btn", MSG_ACTION_NEXT, "next")
        # b2 is disabled if last fieldset (no next fieldset)
        if cur_idx+1 == len(fieldsets):
            b2.add_attribute("disabled", None)

        # --- b3 = Cancel or Exit
        if cur_idx+1 == len(fieldsets):
            b3 = self.__create_button_svg("exit_btn", MSG_ACTION_EXIT, "logout")
        else:
            b3 = self.__create_button_svg("cancel_btn", MSG_ACTION_CANCEL, "cancel")

        # --- shared action button properties
        for b in (b1, b2, b3):
            b.add_attribute("class", "flex-item")
            b.add_attribute("type", "submit")
            b.add_attribute("value", str(fieldsets.get_index(current)))
            self.append_child(b)

    # -----------------------------------------------------------------------

    def disable_all(self):
        """Disable all action buttons.

        """
        for child in self._children:
            if child.has_attribute("disabled") is False:
                child.add_attribute("disabled", None)

    # -----------------------------------------------------------------------

    def __create_button_svg(self, ident, text, svg_name):
        _button = HTMLNode(self.identifier, ident, "button",
                           value="<span>" + text + "</span>")
        _button.set_attribute("data-icon", svg_name)
        _button.set_attribute("name", ident)
        _button.set_attribute("id", ident)
        return _button
