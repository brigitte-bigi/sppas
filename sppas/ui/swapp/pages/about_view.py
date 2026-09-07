"""
:filename: sppas.ui.swapp.pages.about_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: View of the "About" page.

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
from sppas.core.config import cfg
from sppas.ui import _
from sppas.ui.swapp.panels import BaseLinksNode
from sppas.ui.swapp.wappcore.wapputils import sppasImagesAccess
from sppas.ui.swapp.wappbase.wappview import swappBaseView

# ---------------------------------------------------------------------------


# Le code source « sppas » est à jour.
MSG_UP_TO_DATE = _("The « sppas » source code is up to date.")
# Une mise à jour du code source « sppas » est disponible. Lancez Setup pour l’installer.
MSG_UPDATE = _("An update of the « sppas » source code is available. Run Setup to install it.")
# Version
MSG_VERSION = _("Version")
# Notes de version
MSG_RELEASES_NOTES = _("Release notes")
# SPPAS est développé par
MSG_DEVEL_BY = _("SPPAS is developed by ")
# en collaboration avec des phonéticiens et des utilisateurs, dans le but de proposer des outils utiles, fiables et adaptés aux besoins réels.
MSG_IN_COLLAB = _(" in close collaboration with phoneticians and users, with the aim of providing useful, reliable tools adapted to real research needs.")
# Vous souhaitez aider ? Vous pouvez participer en
MSG_WOULD_YOU_LIKE = _("Would you like to help? You can contribute by ")
# créant des ressources.
MSG_CREATING_RESOURCES = _("creating resources.")

# Information de licence
# Liste des langues
# Ecrire des scripts
MSG_LINK_LICENSE = _("License information")
MSG_LINK_LANG = _("List of languages")
MSG_LINK_SCRIPT = _("Write scripts")
MSG_LINK_DOC = _("Documentation of the source code")

# Site web
# Téléchargement
# Code source
MSG_CARD_WEB = _("Website")
MSG_CARD_DOWNLOAD = _("Download")
MSG_CARD_SOURCE = _("Source code")

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("About")

BODY_SCRIPT = """
"""

# ---------------------------------------------------------------------------


class AboutView(swappBaseView):
    """View class responsible for populating the *about.html* page.

    This class represents the **View** component of the "About" page.
    It receives an existing :class:`HTMLTree` instance and fills it with the
    information about SPPAS and its update state. As a page, it has no
    business logic: its content is pure information, reachable from the nav
    of any app.

    """

    def __init__(self, tree: HTMLTree):
        """Initialize and populate the "About" view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate with
                     the page-specific content.
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("AboutView: tree must be an instance of HTMLTree. Got {}".format(type(tree)))
        super().__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self):
        """Override. Populate the `<head>` section of the HTML tree for CSS links.

        No page-specific stylesheet: the cards of the links it shows are
        drawn by the shared one.

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
        """Populate the tree content with the information about SPPAS.

        """
        # The information about SPPAS
        _content_section = TagNode(self._htree.body_main.identifier, None, "section")
        self._htree.body_main.append_child(_content_section)
        AboutView._append_content(_content_section)

        # Then the cards of the places SPPAS is living in, the same panel
        # as the one of the dashboard.
        _links = BaseLinksNode(self._htree.body_main.identifier, "about_links_section")
        _links.link_button("web", sppasImagesAccess.get_logo_filename("sppas-logo-v5"), MSG_CARD_WEB,
                           link="https://sppas.org/")
        _links.link_button("download", "badge-sourceforge", MSG_CARD_DOWNLOAD,
                           link="https://sourceforge.net/projects/sppas/files/")
        _links.link_button("source", "link_github", MSG_CARD_SOURCE,
                           link="https://github.com/brigitte-bigi/sppas")
        self._htree.body_main.append_child(_links)

    # -----------------------------------------------------------------------

    @staticmethod
    def _append_content(parent: TagNode):
        # Title: Program name + release. The h1 of the page is its header.
        _node = HTMLNode(parent.identifier, None, "h2", value=" ".join([sg.__name__, sg.__release__]))
        _node.set_attribute("id", "program_name")
        parent.append_child(_node)

        # Version block
        # -------------
        _article1 = TagNode(parent.identifier, None, "article", attributes={"class": "version-block"})
        parent.append_child(_article1)
        _p = TagNode(_article1.identifier, None, "p")
        _article1.append_child(_p)
        if cfg.update_info.get('update'):
            _span1 = HTMLNode(_p.identifier, None, "span", value="↻")
            _span1.set_attribute("class", "red")
            _span2 = HTMLNode(_p.identifier, None, "span", value=MSG_UPDATE)
        else:
            _span1 = HTMLNode(_p.identifier, None, "span", value="✔")
            _span1.set_attribute("class", "green")
            _span2 = HTMLNode(_p.identifier, None, "span", value=MSG_UP_TO_DATE)
        _span1.set_attribute("aria-hidden", "true")
        _p.append_child(_span1)
        _p.append_child(_span2)
        _p = HTMLNode(_article1.identifier, None, "p", value=" ".join([MSG_VERSION, sg.__version__]))
        _p.add_attribute("class", "details")
        _article1.append_child(_p)
        _a = HTMLNode(_p.identifier, None, "a", value=MSG_RELEASES_NOTES)
        _a.set_attribute("href", "https://sppas.org/book_changes.html#latest")
        _a.set_attribute("target", "_blank")
        _a.set_attribute("class", "external-link")
        _p.append_child(_a)

        # Contribute block
        # ----------------
        _article2 = TagNode(parent.identifier, None, "article")
        parent.append_child(_article2)
        _link = ' <a target="_blank" class="external-link" href="https://sppas.org/bigi/">Brigitte Bigi</a> '
        _p = HTMLNode(_article2.identifier, None, "p", value=" ".join([MSG_DEVEL_BY, _link, MSG_IN_COLLAB]))
        _article2.append_child(_p)
        _p = HTMLNode(_article2.identifier, None, "p", value=MSG_WOULD_YOU_LIKE)
        _article2.append_child(_p)
        AboutView._append_link(_p, "https://sppas.org/resources.html#contribute", MSG_CREATING_RESOURCES)

        # More links block -- was the footer of the dialog
        # ----------------
        _article3 = TagNode(parent.identifier, None, "article")
        parent.append_child(_article3)
        _p_links = TagNode(_article3.identifier, None, "p")
        AboutView._append_link(_p_links, "https://sppas.org/book_introduction.html#license", MSG_LINK_LICENSE)
        AboutView._append_link(_p_links, "https://sppas.org/resources.html", MSG_LINK_LANG)
        AboutView._append_link(_p_links, "https://sppas.org/scripting.html", MSG_LINK_SCRIPT)
        # The document of the package, served by this server: it opens in a
        # tab of its own, the page of SPPAS staying where it is.
        AboutView._append_link(_p_links, "/index.html", MSG_LINK_DOC, external=False)
        _article3.append_child(_p_links)

    # -----------------------------------------------------------------------

    @staticmethod
    def _append_link(parent: TagNode, href: str, value: str, external: bool = True):
        """Append a link, opened in a tab of its own.

        :param parent: (TagNode) the parent HTML node to append the link in
        :param href: (str) the address the link points to
        :param value: (str) the text of the link
        :param external: (bool) True for an address outside of this server

        """
        _a = HTMLNode(parent.identifier, None, "a", value=value)
        _a.set_attribute("target", "_blank")
        if external is True:
            _a.set_attribute("class", "external-link")
        _a.set_attribute("href", href)
        parent.append_child(_a)
