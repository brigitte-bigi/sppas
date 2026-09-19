# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_wkps.page_files.col_refs.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The column "References" of the page "Files" for SPPAS Web UI.

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

# ---------------------------------------------------------------------------


class swappReferencesNode(HTMLNode):
    """The column with the list of references of the page files.

    The identity of the node is 'column_files_refs', and the name of each
    of its events starts with "refs_".

    """

    def __init__(self, parent):
        super(swappReferencesNode, self).__init__(parent.identifier, "column_files_refs", "div")
        self.add_attribute("class", self.identifier)

        # A toolbar with action buttons
        refs_toolbar = HTMLNode(self.identifier, None, "div", attributes={"class": "refsbar"})
        self.append_child(refs_toolbar)
        self.__create_toolbar(refs_toolbar)

        # The list of available files of the current workspace
        refs_list = HTMLNode(self.identifier, None, "div", attributes={"class": "refslist"})
        self.append_child(refs_list)
        self.__create_list(refs_list)

    # -----------------------------------------------------------------------

    def process_event(self, event_name, event_value) -> bool:
        """Process the given events.

        :param event_name: (str)
        :param event_value: (str)
        :return: None

        """
        pass

    # -----------------------------------------------------------------------
    # Create and append the children nodes
    # -----------------------------------------------------------------------

    def __create_toolbar(self, parent):
        """Add action buttons to the toolbar.

        """
        h1 = HTMLNode(parent.identifier, None, "h1",
                      attributes={"class": "refstitle"},
                      value=_('References') + ":")
        parent.append_child(h1)

    # -----------------------------------------------------------------------

    def __create_list(self, parent):
        """Add the list of refs/attributes of the in-use workspace.

        """
        p = HTMLNode(parent.identifier, None, "p", value="List of refs...")
        parent.append_child(p)
