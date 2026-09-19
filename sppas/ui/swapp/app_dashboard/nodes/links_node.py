"""
:filename: sppas.ui.swapp.app_dashboard.nodes.links_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The links section of the SPPAS Dashboard Application.

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

from sppas.ui import _
from sppas.ui.swapp.panels import swappBaseLinksNode
from sppas.ui.swapp.swapp_core.swapp_utils import swappImagesAccess

# ---------------------------------------------------------------------------


MSG_HOME = _("Website")
MSG_DOC = _("Book")
MSG_RSC = _("Resources")
MSG_TUTOS = _("Tutorials")
MSG_FAQ = "F.A.Q."
MSG_AUTH = _("The author")
MSG_AWARD = _("Award")

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------


class swappLinksNode(swappBaseLinksNode):
    """The section with external links of the dashboard application.

    """

    ID = "links_section"

    def __init__(self, parent_id):
        super(swappLinksNode, self).__init__(parent_id, swappLinksNode.ID)

        self.link_button("web", swappImagesAccess.get_logo_filename("sppas-logo-v5"), MSG_HOME, link="https://sppas.org/")
        self.link_button("docu", "link_docweb", MSG_DOC, link="https://sppas.org/book.html")
        self.link_button("res", "link_resources", MSG_RSC, link="https://sppas.org/resources.html")
        self.link_button("tuto", "link_tutovideo", MSG_TUTOS, link="https://sppas.org/tutorials.html")
        self.link_button("faq", "link_question", MSG_FAQ, link="https://sppas.org/faq.html")
        self.link_button("award", "link_sppas_award", MSG_AWARD, link='https://www.ouvrirlascience.fr/sppas-2/')

# ---------------------------------------------------------------------------


class swappAboutsNode(swappBaseLinksNode):
    """The section with the page links of the dashboard application.

    The buttons are appended dynamically: each page of the WEB_PAGES
    registry declares itself, like any app declares its card.

    """

    ID = "about_section"

    def __init__(self, parent_id):
        super(swappAboutsNode, self).__init__(parent_id, swappAboutsNode.ID)
