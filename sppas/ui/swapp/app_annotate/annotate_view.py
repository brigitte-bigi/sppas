"""
:filename: sppas.ui.swapp.app_annotate.annotate_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The view of Annotate: the tree of its page.

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
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_view import swappBaseView
from ..swapp_core.swappsg import swapp_settings

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Annotate")

# ---------------------------------------------------------------------------


class swappAnnotateView(swappBaseView):
    """View class responsible for populating the page of Annotate.

    It builds the header and the nav of the page. It decides nothing: what
    it shows was decided before it was called.

    """

    def __init__(self, tree: HTMLTree, help_page: str):
        """Initialize and populate the Annotate view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate
        :param help_page: (str) Name of the page serving the document of the app
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappAnnotateView: tree must be an instance of HTMLTree. "
                            "Got {} instead.".format(type(tree)))
        # Set before the base view populates the nav with it.
        self.__help_page = help_page
        super(swappAnnotateView, self).__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self, *args, **kwargs):
        """Override. Add the sheet of the panel-view toggle, and the one of Annotate."""
        super()._populate_head_css(*args, **kwargs)
        self._htree.head.link("stylesheet", swapp_settings.wexa_statics + "css/togglegroup.css",
                              link_type="text/css")
        self._htree.head.link("stylesheet", swapp_settings.css + "app_annotate.css", link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page."""
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _populate_body_nav(self):
        """Override. Populate the nav area of the page."""
        _s = TagNode(self._htree.body_nav.identifier, None, "section")
        self.append_pin_button(_s)
        self.append_accessibility_buttons(_s)
        self._htree.body_nav.append_child(_s)
        self.append_home_link_button(self._htree.body_nav, self._home_target())
        self.append_help_link_button(self._htree.body_nav, self.__help_page)
        self.append_trace_link_button(self._htree.body_nav)

    # -----------------------------------------------------------------------
    # Update the tree -- for baking the page
    # -----------------------------------------------------------------------

    def populate_tree_content(self) -> None:
        """Append the content of the page to the main content: it has none yet."""
