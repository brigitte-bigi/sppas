# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_test.tests_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The index of the tests: one button per test.

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


"""

from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import TagNode

from sppas.ui.swapp.nodes import swappHTMLButton
from sppas.ui.swapp.swapp_base.swapp_view import swappBaseView

# ---------------------------------------------------------------------------

MSG_TITLE = "Tests of swapp"
MSG_BACK = "Tests"
MSG_INTRO = ("Each button leads to the page of one test. A test shows a "
             "component as an application shows it, and nothing of it is "
             "built here.")

# ---------------------------------------------------------------------------


class swappTestsBaseView(swappBaseView):
    """Populate the fixed part of any page of the tests.

    Every page of this app is framed as the pages of SPPAS are: the same
    header, the same nav, the same footer. What differs from one to the next
    is its title and what it starts once it is loaded.

    """

    def __init__(self, tree: HTMLTree, title: str, script: str = ""):
        """Populate the fixed part of the page.

        :param tree: (HTMLTree) The tree of the page
        :param title: (str) What the header of the page shows
        :param script: (str) What the page starts once it is loaded
        :raises: TypeError: The given tree is not an HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappTestsBaseView: tree must be an instance of "
                            "HTMLTree. Got {}".format(type(tree)))
        self.__script = script
        super().__init__(tree, title)

    # -----------------------------------------------------------------------

    def _populate_head_css(self):
        """Override. No stylesheet of its own: a test brings none."""
        pass

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
        self.append_trace_link_button(self._htree.body_nav)

    # -----------------------------------------------------------------------

    def append_back_link_button(self, parent: HTMLNode) -> HTMLNode:
        """Create and append the button leading back to the index of the tests.

        The page of a test is reached from the index and leads back to it: the
        button of the nav which leads home leads to the Dashboard, which is
        another place. The index itself does not carry this button, having
        nowhere of its own to go back to.

        :param parent: (HTMLNode) The node the button is appended in
        :return: (HTMLNode) The button

        """
        _button = HTMLNode(parent.identifier, None, "button",
                           value="<span>" + MSG_BACK + "</span>")
        _button.add_attribute("id", "link-tests_button")
        _button.add_attribute("aria-label", MSG_BACK)
        _button.add_attribute("title", MSG_BACK)
        _button.add_attribute("type", "button")
        _button.add_attribute("data-href", "test.html")
        _button.add_attribute("data-target", "_self")
        _button.add_attribute("class", "menuitem")
        parent.append_child(_button)
        self._htree.head.add_links("link-tests_button")

        return _button

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section."""
        if len(self.__script) == 0:
            return

        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(self.__script)

# ---------------------------------------------------------------------------


class swappTestsView:
    """Build the index of the tests in the main of the page.

    It is given the tests and shows them. It decides nothing: which tests
    exist is the model\'s, and what a test does is its page\'s.

    """

    def __init__(self, parent):
        """Create the view of the index.

        :param parent: (HTMLNode) The node of the page the index is built in

        """
        self.__parent = parent

    # -----------------------------------------------------------------------

    def populate_tree_content(self, tests: list) -> None:
        """Build one button per test, with what it is for.

        :param tests: (list) The recipes of the tests to be shown

        """
        self.__parent.clear_children()

        _h2 = HTMLNode(self.__parent.identifier, None, "h2", value=MSG_TITLE)
        self.__parent.append_child(_h2)
        _p = HTMLNode(self.__parent.identifier, None, "p", value=MSG_INTRO)
        self.__parent.append_child(_p)

        _ul = TagNode(self.__parent.identifier, None, "ul")
        self.__parent.append_child(_ul)

        for _recipe in tests:
            self.__append_test(_ul, _recipe)

    # -----------------------------------------------------------------------

    def __append_test(self, parent: TagNode, recipe) -> None:
        """Build the button of one test, and what it is for.

        :param parent: (TagNode) The list the test is appended to
        :param recipe: (class) What bakes the page of the test

        """
        from .tests_model import swappTestsModel

        _li = TagNode(parent.identifier, None, "li")
        parent.append_child(_li)

        _button = swappHTMLButton(_li.identifier,
                                  identifier=swappTestsModel.button_of(recipe))
        _button.add_attribute("data-href", "/" + recipe.page())
        _button.add_attribute("data-target", "_self")
        _button.add_attribute("class", "action-button")
        _button.set_text(None, recipe.name())
        _li.append_child(_button)

        _p = HTMLNode(_li.identifier, None, "p", value=recipe.description())
        _li.append_child(_p)
