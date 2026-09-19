"""
:filename: sppas.ui.swapp.pages.cite_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: View of the "How to cite" page.

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
from whakerpy.htmlmaker import EmptyNode

from sppas.core.config import sg
from sppas.ui import _
from sppas.ui.swapp import sppasImagesAccess
from sppas.ui.swapp.swappbase.swappview import swappBaseView

# ---------------------------------------------------------------------------


MSG_MAIN_CITE = _("For a general citation of SPPAS, use the reference below:")
MSG_OTHERS_CITE = _("please refer to the related specific publication")
MSG_CLICK_HERE = _("Click here to get all references")

MSG_CITATION = """
                Brigitte Bigi.
                <b>SPPAS - MULTI-LINGUAL APPROACHES TO THE AUTOMATIC ANNOTATION OF SPEECH.</b>
                <i>The Phonetician.</i> Journal of the International Society of Phonetic Sciences, 2015,
                Journal of ISPhS/International Society of Phonetic Sciences, 111-112 (ISSN:0741-6164),
                pp. 54-69.
      """

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("How to cite")

BODY_SCRIPT = """
"""

# ---------------------------------------------------------------------------


class CiteView(swappBaseView):
    """View class responsible for populating the *cite.html* page.

    This class represents the **View** component of the "How to cite" page.
    It receives an existing :class:`HTMLTree` instance and fills it with the
    citation information of SPPAS. As a page, it has no business logic: its
    content is pure information, reachable from the nav of any app.

    """

    def __init__(self, tree: HTMLTree):
        """Initialize and populate the "How to cite" view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate with
                     the page-specific content.
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("CiteView: tree must be an instance of HTMLTree. Got {}".format(type(tree)))
        super().__init__(tree, MSG_HEADER)

        # The SPPAS way of organizing an illustration with its content.
        self._htree.body_main.add_attribute("class", "illustrated-content")

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self):
        """Override. Populate the `<head>` section of the HTML tree for CSS links.

        No page-specific stylesheet: the page relies on the shared one only.

        """
        pass

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page.

        """
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _populate_body_nav(self):
        """Override. Populate the nav area of the page.

        """
        _s = TagNode(self._htree.body_nav.identifier, None, "section")
        self.append_pin_button(_s)
        self.append_accessibility_buttons(_s)
        self._htree.body_nav.append_child(_s)

        self.append_home_link_button(self._htree.body_nav, self._home_target())
        self.append_trace_link_button(self._htree.body_nav)

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section.

        """
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT)

    # -----------------------------------------------------------------------
    # Update the tree -- for baking the page
    # -----------------------------------------------------------------------

    def populate_tree_content(self):
        """Populate the tree content with the citation information.

        """
        # At left: the capture of the reference article, in a link
        _a = TagNode(self._htree.body_main.identifier, None, "a")
        _a.set_attribute("class", "noborder")
        _a.set_attribute("role", "button")
        _a.set_attribute("target", "_blank")
        _a.set_attribute("href", "https://hal.science/hal-01417876")
        self._htree.body_main.append_child(_a)
        _logo = EmptyNode(_a.identifier, None, "img")
        _logo.set_attribute("src", sppasImagesAccess.get_image_filename("article_reference"))
        _logo.set_attribute("alt", "Capture article")
        _a.append_child(_logo)

        # At right: the citation information
        _content_section = TagNode(self._htree.body_main.identifier, None, "section")
        self._htree.body_main.append_child(_content_section)

        _article1 = TagNode(_content_section.identifier, None, "article")
        _content_section.append_child(_article1)
        _p = HTMLNode(_article1.identifier, None, "p", value=MSG_MAIN_CITE)
        _article1.append_child(_p)
        _b = HTMLNode(_article1.identifier, None, "blockquote", value=MSG_CITATION)
        _article1.append_child(_b)

        _article2 = TagNode(_content_section.identifier, None, "article")
        _content_section.append_child(_article2)
        _p = HTMLNode(_article2.identifier, None, "p", value=MSG_OTHERS_CITE)
        _article2.append_child(_p)
        _link = HTMLNode(_article2.identifier, None, "a", value=MSG_CLICK_HERE)
        _link.set_attribute("target", "_blank")
        _link.set_attribute("class", "external-link")
        _link.set_attribute("href", "https://sppas.org/book_references.html")
        _article2.append_child(_link)
