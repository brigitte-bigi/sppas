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

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_view import swappBaseView

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Plugins")

# ---------------------------------------------------------------------------


class swappPluginsView(swappBaseView):
    """View class responsible for populating the page of Plugins.

    It builds the header and the nav of the page. The main content shows
    nothing yet.

    """

    def __init__(self, tree: HTMLTree):
        """Initialize and populate the Plugins view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappPluginsView: tree must be an instance of HTMLTree. "
                            "Got {} instead.".format(type(tree)))
        super(swappPluginsView, self).__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page."""
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def populate_tree_content(self) -> None:
        """Populate the main content of the page: nothing is shown yet."""
        pass
