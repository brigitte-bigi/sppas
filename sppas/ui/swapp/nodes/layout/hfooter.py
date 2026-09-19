# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.nodes.layout.hfooter.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Default footer node for any SPPAS Web APPlication.

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

from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLFooterNode

from sppas.core.config import sg
from sppas.ui.swapp.swappcore.swappsg import swapp_settings
from sppas.ui.swapp.swappcore.swapputils import sppasImagesAccess

# ---------------------------------------------------------------------------


class swappFooter(HTMLFooterNode):
    """Create the footer node and make available nodes to be appended.

    """

    def __init__(self, parent_id: str):
        super(swappFooter, self).__init__(parent_id)
        self.set_attribute("class", "center")

    # -----------------------------------------------------------------------

    def append_sppas_splash(self):
        """Append the sppas banner.

        """
        img_splash = EmptyNode(self.identifier, None, "img")
        img_splash.add_attribute("src", f"{swapp_settings.images}/sppas-splash-v5.png")
        img_splash.add_attribute("id", "splash")
        img_splash.add_attribute("class", "")
        img_splash.add_attribute("alt", "")
        self.append_child(img_splash)

    # -----------------------------------------------------------------------

    def append_copyright(self):
        """Append the copyright text.

        """
        _p = HTMLNode(self.identifier, None, "p", value=sg.__copyright__)
        _p.add_attribute("class", "copyright")
        self.append_child(_p)

    # -----------------------------------------------------------------------

    def append_scroll_top(self):
        """Append the scroll button.

        """
        back_top = HTMLNode(self.identifier, None, "a")
        back_top.add_attribute("data-icon", "scrolltop")
        back_top.add_attribute("href", "#header-content")
        back_top.add_attribute("role", "button")
        back_top.add_attribute("class", "footer-button")
        self.append_child(back_top)
