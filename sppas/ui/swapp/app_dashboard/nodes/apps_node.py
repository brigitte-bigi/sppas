"""
:filename: sppas.ui.swapp.app_dashboard.apps_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The apps section of the SPPAS Dashboard Application.

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
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import EmptyNode

from sppas.ui import _
from sppas.ui.swapp.nodes import LinkButtonNode

# ---------------------------------------------------------------------------


MSG_LAUNCH = _("Launch")

# ---------------------------------------------------------------------------


class AppsNode(HTMLNode):
    """The list of the applications of the dashboard application.

    A list, because the Dashboard offers a choice between applications.
    Not articles: a card means nothing outside the page, it is the way in
    to an app, not a content standing by itself.

    """

    ID = "apps_section"

    # -----------------------------------------------------------------------

    def __init__(self, parent_id):
        super(AppsNode, self).__init__(parent_id, AppsNode.ID, "ul")
        self.add_attribute("id", self.identifier)
        self.add_attribute("class", "cards-panel")
        self.add_attribute("class", "apps-panel")

    # -----------------------------------------------------------------------

    def create_app_card(self, ident: str, name: str, icon_name: str, text: str, link: str = "",
                        enable: bool = True, busy: bool = False, theme_name: str = ""):
        """A specific card to represent the card of an app to launch.

        :param ident: (str) Stable technical identifier of the card, used to
            build the ids of its HTML nodes. It must be locale-independent:
            the JS references these ids (e.g. "desktop_button"), so it is
            never derived from the translated name.
        :param name: (str) The short name of the application.
        :param icon_name: (str) Name of an image representing the application
        :param text: (str) Text description of the application
        :param link: (str) Link to the application
        :param enable: (bool) The feature is installed: False dims the
            whole card, matching what a missing feature already looks like.
        :param busy: (bool) The app is already running elsewhere: only its
            Launch button is disabled, exactly as the click that launched
            it already did, client-side -- a later re-bake of this same
            page must render the identical result, not a different one.
        :param theme_name: (str) The theme the application brings, if any:
            the launch button carries it, and the client then leaves the
            theme of this page behind instead of handing it over.

        """
        ident = ident.lower().replace(" ", "_")
        article = HTMLNode(self.identifier, ident+"_article", "li")
        article.add_attribute("class", "card")
        article.add_attribute("class", "app")
        if enable is False:
            article.add_attribute("class", "app-disabled")
        self.append_child(article)

        # Define the background image
        attributes = dict()
        attributes["class"] = "app-background-img"
        attributes["src"] = icon_name
        attributes["alt"] = name + " logo"
        img = EmptyNode(article.identifier, ident+"_img", "img", attributes=attributes)
        article.append_child(img)

        # Define the content of the card: a container and a button
        content = HTMLNode(article.identifier, ident + "_content", "div")
        content.add_attribute("class", "app-content | flow")
        article.append_child(content)

        # Container for a title and a description
        container = HTMLNode(content.identifier, ident + "_container", "div")
        container.add_attribute("class", "app-container | flow")
        content.append_child(container)

        # - title
        title = HTMLNode(container.identifier, ident + "_title", "h2", value=name)
        title.add_attribute("id", ident + "_title")
        title.add_attribute("class", "app-title")
        container.append_child(title)

        # - description
        descr = HTMLNode(container.identifier, ident + "_descr", "p", value=text)
        descr.add_attribute("class", "app-description")
        container.append_child(descr)

        # Launch button
        if enable is False:
            _b = HTMLNode(content.identifier, ident + "_button", "button", value=MSG_LAUNCH)
            _b.add_attribute("class", "action-button app-button")
            _b.add_attribute("disabled", None)
        else:
            if link.endswith(".html"):
                # The link is handled by the dashboard manager to propagate contrast&theme.
                _b = LinkButtonNode(content.identifier, ident + "_button", link)
                _b.set_value(MSG_LAUNCH)
                _b.add_attribute("class", "action-button app-button")
                # Overrides role. It's a link, but it acts like a button (launch an app).
                _b.add_attribute("role", "button")
                # button = HTMLNode(content.identifier, ident + "_button", "a", value=MSG_LAUNCH, attributes={
                #     'href': link,
                #     'role': "button",
                #     'target': "_blank",
                #     'class': "app-button",
                #     "id": ident + "_button"
                # })
            else:
                # The button is not a link, it's an action handled by the JS DashboardManager()
                _b = HTMLNode(content.identifier, ident + "_button", "button", value=MSG_LAUNCH)
                _b.add_attribute("class", "action-button app-button")
                _b.add_attribute("id", ident + "_button")
                if busy is True:
                    _b.add_attribute("disabled", None)

        if len(theme_name) > 0:
            _b.add_attribute("data-theme", theme_name)

        content.append_child(_b)
