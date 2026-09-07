# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.pages.help_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application View of the help page of an app.

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
import os

from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import HTMLNode

from sppas.ui.swapp.wappbase.wappview import swappBaseView
from sppas.ui.swapp.wappcore.wappsg import wapp_settings

# ---------------------------------------------------------------------------


# The Book is an extra: it is imported by the pages needing it, exactly as
# the ThemeManager is -- see wappview.py.
BODY_SCRIPT = (
    "const Book = (await import(window.WEXA_JS_PATH + '/extras/book.js')).Book;"
    "const book = new Book('main-content');"
    "book.fillTable();"
)

# ---------------------------------------------------------------------------


class HelpView(swappBaseView):
    """View class responsible for populating the help page of any app.

    The document of an app is written by hand, as a fragment holding what
    the "main" of the page displays. This view builds everything around it:
    the head, the menu, the footer -- the very things a hand-written page
    would have to copy, and to update at each new version of Whakerexa.

    """

    def __init__(self, tree: HTMLTree, title: str, css: str = ""):
        """Initialize and populate the help view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate.
        :param title: (str) Title of the documented app.
        :param css: (str) Filename of the stylesheet of the documented app
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("HelpView: tree must be an instance of HTMLTree. "
                            "Got {}".format(type(tree)))
        # Set before the base view populates the head with it.
        self.__css = css
        super().__init__(tree, title)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def populate_tree_content(self, document: str) -> tuple:
        """Populate the tree content with the document of the app.

        The file is written into the "main" as it is: it is HTML already,
        and turning it into nodes would only be a way of losing it.

        :param document: (str) Path of the document, relative to swapp
        :return: (tuple) The status code and its message

        """
        filename = os.path.join(wapp_settings.base_dir, document)
        if os.path.exists(filename) is False or os.path.isfile(filename) is False:
            return 404, f"Document {document} not found (filename: {filename})."

        with open(filename, "r", encoding="utf-8") as fp:
            self._htree.body_main.set_value(fp.read())

        return 200, ""

    # -----------------------------------------------------------------------
    # Override the base view
    # -----------------------------------------------------------------------

    def _populate_head_css(self, *args, **kwargs):
        """Override. The document is written with the Book extra.

        The stylesheet of the documented app is loaded too: a document shows
        the very elements of its app -- a card, a link -- and they are drawn
        by that sheet, not by the shared one.

        """
        self._htree.head.link("stylesheet", wapp_settings.wexa_statics + "css/extras/book.css",
                              link_type="text/css")
        if len(self.__css) > 0:
            self._htree.head.link("stylesheet", wapp_settings.css + self.__css,
                                  link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_nav(self):
        """Override. Populate the nav area of the help page.

        """
        from whakerpy.htmlmaker import TagNode

        _s = TagNode(self._htree.body_nav.identifier, None, "section")
        self.append_pin_button(_s)
        self.append_accessibility_buttons(_s)
        self._htree.body_nav.append_child(_s)

        self.append_home_link_button(self._htree.body_nav, self._home_target())
        self.append_trace_link_button(self._htree.body_nav)

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. The table of contents is built by the Book extra.

        """
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT)
