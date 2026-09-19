# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_wkps.page_files.filesmaker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The page "Files" of the SPPAS Web UI.

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

    Copyright (C) 2011-2024  Brigitte Bigi, CNRS
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

from whakerpy.htmlmaker import HTMLComment
from whakerpy.htmlmaker import HTMLNode

from sppas.ui import _
from sppas.ui.swapp.swappcore.swappsg import swapp_settings
from sppas.ui.swapp.swappbase.swappresponse import BaseResponseRecipe

from .col_wkps import WkpsNode
from .col_files import FilesNode
from .col_links import AssociateNode
from .col_refs import ReferencesNode

# ---------------------------------------------------------------------------


class FilesResponseRecipe(BaseResponseRecipe):
    """The Recipe to create the Files page of SPPAS Main Web UI.

    The page is made of 4 different panels, each one in a column:
        1. Workspaces
        2. Files
        3. Associate
        4. References

    """

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return "workspaces.html"

    @staticmethod
    def title() -> str:
        """Return the page title."""
        return _("Files")

    @staticmethod
    def ident() -> str:
        """Return the page identifier."""
        return "files"

    @staticmethod
    def icon() -> str:
        """Return the page icon name."""
        return "page_files"

    # -----------------------------------------------------------------------

    def __init__(self, name="Files", tree=None, title="Files"):
        super(FilesResponseRecipe, self).__init__(name, tree)

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the parts that can't be invalidated:
        head, body_header, body_footer.

        """
        super().create()

        # Add this page style
        # self._htree.add_css_link(os.path.join(swapp_settings.css, "page_files.css"))
        # Add the menubar page style
        # self._htree.add_css_link(os.path.join(swapp_settings.css, "menubar.css"))
        # Add the style of each used element
        # self._htree.add_css_link(os.path.join(swapp_settings.css, "title.css"))
        # self._htree.add_css_link(os.path.join(swapp_settings.css, "modal.css"))
        self._htree.head.link(rel="stylesheet", link_type="text/css", href=swapp_settings.css + "/main_swapp.css")
        self._htree.head.link(rel="stylesheet", link_type="text/css", href=swapp_settings.css + "/main_swapp_theme.css")
        self._htree.head.link(rel="stylesheet", link_type="text/css", href=swapp_settings.css + "/page_files.css")
        self._htree.head.link(rel="stylesheet", link_type="text/css", href=swapp_settings.css + "/menubar.css")

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug("Page files -- Process events: {}".format(events))

        refresh = list()
        for event_key in events:
            event_value = events[event_key]
            dirty = False
            if event_key.startswith("wkps_"):
                dirty = self._wkps.process_event(event_key, event_value)
            elif event_key.startswith("files_"):
                dirty = self._files.process_event(event_key, event_value)
            elif event_key.startswith("links_"):
                dirty = self._links.process_event(event_key, event_value)
            elif event_key.startswith("refs_"):
                dirty = self._refs.process_event(event_key, event_value)
            else:
                logging.warning("Ignored event: {:s}".format(event_key))
            logging.debug("Returned dirty={}".format(dirty))
            refresh.append(dirty)

        self._status.code = 200
        return any(refresh)

    # -----------------------------------------------------------------------

    def _bake(self):
        """Create or re-create the Home page content in HTML.

        """
        d = HTMLNode(self._htree.body_main.identifier, "files_cols", "div", attributes={"class": "panel cols_files"})
        self._htree.body_main.append_child(d)

        c = HTMLComment(d.identifier, "COLUMN 1: Workspaces")
        d.append_child(c)
        d.append_child(WkpsNode(d))

        c = HTMLComment(d.identifier, "COLUMN 2: Files")
        d.append_child(c)
        d.append_child(FilesNode(d))

        c = HTMLComment(d.identifier, "COLUMN 3: Associate")
        d.append_child(c)
        d.append_child(AssociateNode(d))

        c = HTMLComment(d.identifier, "COLUMN 4: References")
        d.append_child(c)
        d.append_child(ReferencesNode(d))

    # -----------------------------------------------------------------------
    # Useful method to get direct access to the columns' nodes
    # -----------------------------------------------------------------------

    @property
    def _wkps(self):
        return self._htree.body_main.get_child("files_cols").get_child("column_files_wkps")

    @property
    def _files(self):
        return self._htree.body_main.get_child("column_files_files")

    @property
    def _links(self):
        return self._htree.body_main.get_child("column_files_links")

    @property
    def _refs(self):
        return self._htree.body_main.get_child("column_files_refs")
