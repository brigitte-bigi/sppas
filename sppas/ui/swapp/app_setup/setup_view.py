"""
:filename: sppas.ui.swapp.app_setup.setup_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Setup View of the MVC paradigm.

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

from ..wappbase.wappview import swappBaseView
from ..wappcore.wappsg import wapp_settings

from .basefieldset import SetupBaseFieldset
from .fieldsets import SetupFieldsets
from .actions_node import SetupActionsNode

# ---------------------------------------------------------------------------


MSG_HEADER = f"SPPAS {sg.__release__} » Setup"

BODY_SCRIPT = f"""
        import {{ SetupManager }} from '/{wapp_settings.js}sppas.js';
        const setupManager = new SetupManager();
        setupManager.handleSetupManagerOnLoad();
"""

# ---------------------------------------------------------------------------


class SetupView(swappBaseView):
    """View class responsible for populating the *setup.html* page.

    This class represents the **View** component of the MVC pattern for the
    SPPAS Setup web application. It receives an existing :class:`HTMLTree`
    instance and fills it with all static and semi-static visual content.

    The :class:`SetupView` does not manage user events nor business logic;
    it focuses solely on defining the HTML structure and resources required
    for rendering the Setup interface.

    The generated content includes:
        - Head section with meta, stylesheets, and JS imports.
        - Header (title, navigation buttons, accessibility controls).
        - Main content area and its fieldsets.
        - Footer with copyright information.
        - Script element

    """

    def __init__(self, tree: HTMLTree):
        """Initialize and populate the Setup view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate with
                     the setup-specific content.
        """        
        self.__fieldsets = list()
        super().__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Getters / Setters
    # -----------------------------------------------------------------------

    def set_fieldsets(self, fieldsets: SetupFieldsets) -> None:
        """Set a new fieldset and update the tree consequently.

        :param fieldsets: (list) An instance of :class:`SetupFieldsets`
        :raises: TypeError: fieldsets is not an instance of SetupFieldsets

        """
        if isinstance(fieldsets, SetupFieldsets) is False:
            raise TypeError("SetupView: fieldsets must be an instance of SetupFieldsets. Got {}".format(type(fieldsets)))
        self.__fieldsets = fieldsets

        # Re-create nodes making use of fieldsets
        self.update_header_breadcrumb(0)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self):
        """Override. Populate the `<head>` section of the HTML tree for CSS links.

        """
        self._htree.head.link("stylesheet", wapp_settings.css + "app_setup.css", link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the Setup page.

        """
        witems = HTMLNode(self._htree.body_header.identifier, "breadcrumb", "ol",
                          attributes={"class": "breadcrumb"})
        self._htree.body_header.append_child(witems)
        if len(self.__fieldsets) > 0:
            self.update_header_breadcrumb(0)

        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _populate_body_nav(self):
        """Override. Populate the nav area of the Setup page.

        """
        _s = TagNode(self._htree.body_nav.identifier, None, "section")
        self.append_pin_button(_s)
        self.append_accessibility_buttons(_s)
        self._htree.body_nav.append_child(_s)

        self.append_home_link_button(self._htree.body_nav, self._home_target())
        self.append_help_link_button(self._htree.body_nav)
        self.append_trace_link_button(self._htree.body_nav)
        self.append_sppas_link_button(self._htree.body_nav)

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section.

        """
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT)

    # -----------------------------------------------------------------------
    # Getters
    # -----------------------------------------------------------------------

    @property
    def __breadcrumb(self):
        return self._htree.body_header.get_child("breadcrumb")

    # -----------------------------------------------------------------------
    # Update the tree -- for baking the page
    # -----------------------------------------------------------------------

    def update_header_breadcrumb(self, cur_idx: int) -> None:
        """Update the breadcrumb of the header by highlighting the given n-th fieldset.

        :param cur_idx: (int) Index of the currently enabled fieldset
        :raises: TypeError: if current is not a SetupBaseFieldset

        """
        # Delete the existing children
        self.__breadcrumb.clear_children()

        # Create a new ones
        if len(self.__fieldsets) > 0:
            for i, field_node in enumerate(self.__fieldsets):
                li = HTMLNode(self.__breadcrumb.identifier, "wizarditem_%d" % i, "li",
                              value=field_node.get_msg())
                if i < cur_idx:
                    li.set_attribute("class", "visited")
                elif i == cur_idx:
                    li.set_attribute("class", "active")
                self.__breadcrumb.append_child(li)

    # -----------------------------------------------------------------------

    def update_tree_content(self,
                            current_fieldset: SetupBaseFieldset,
                            actions: bool = True,
                            install: bool = True):
        """Update the tree content depending on the actual fieldset.

        :param current_fieldset: (SetupBaseFieldset) The currently enabled fieldset
        :param actions: (bool) Whether the actions bar should be appended
        :param install: (bool) Whether the button "Install" is displayed or not

        """
        # Delete any existing node in the main content
        self._htree.body_main.clear_children()

        # Add dialogs for messages
        self.append_alert_dialogs(self._htree.body_main)

        # The fieldset
        current_fieldset.set_parent(self._htree.body_main.identifier)
        self._htree.body_main.append_child(current_fieldset)

        # The action buttons to enable/disable or change its buttons,
        # and to associate the right fieldset index.
        action_nav = SetupActionsNode(self._htree.body_main.identifier,
                                      self.__fieldsets,
                                      current_fieldset,
                                      install)
        self._htree.body_main.append_child(action_nav)
        if actions is False:
            action_nav.disable_all()
