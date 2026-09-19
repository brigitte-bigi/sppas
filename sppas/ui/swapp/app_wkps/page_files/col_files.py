# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_wkps.page_files.col_files.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The column "Files" of the page "Files" for SPPAS Web UI.

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

from sppas.src.wkps import States
from sppas.ui import _
from sppas.ui.swapp.swappcore.swappsg import swapp_wkps

# ---------------------------------------------------------------------------


STATES_ICON_NAMES = {
    States().MISSING: "choice_checkbox_dashed",
    States().UNUSED: "choice_checkbox",
    States().CHECKED: "choice_checked",
    States().LOCKED: "locked",
    States().AT_LEAST_ONE_CHECKED: "choice_pos",
    States().AT_LEAST_ONE_LOCKED: "choice_neg"
}

# ---------------------------------------------------------------------------


class FilesNode(HTMLNode):
    """The column with the list of files of the page files.

    The identity of the node is 'column_files_files', and the name of each
    of its events starts with "files_".

    """

    def __init__(self, parent):
        super(FilesNode, self).__init__(parent.identifier, "column_files_files", "div")
        self.add_attribute("class", self.identifier)

        # A toolbar with action buttons
        files_toolbar = HTMLNode(self.identifier, None, "div", attributes={"class": "filesbar"})
        self.append_child(files_toolbar)
        self.__create_toolbar(files_toolbar)

        # The list of available files of the current workspace
        files_list = HTMLNode(self.identifier, None, "div", attributes={"class": "fileslist"})
        self.append_child(files_list)
        self.__create_list(files_list)

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
                      attributes={"class": "filestitle"},
                      value=_('Files') + ":")
        parent.append_child(h1)

    # -----------------------------------------------------------------------

    def __create_list(self, parent):
        """Add the list of path/root/files of the in-use workspace.

        """
        p = HTMLNode(parent.identifier, None, "p",
                     value="Tree of files of workspace: {:s}".format(swapp_wkps.get_wkp_name()))
        parent.append_child(p)
