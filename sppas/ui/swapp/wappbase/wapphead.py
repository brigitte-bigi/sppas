# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.wappbase.wapphead.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application ResponseRecipe.

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
from whakerpy.htmlmaker import HTMLHeadNode

from sppas.ui.swapp.wappcore.wappsg import wapp_settings

# ---------------------------------------------------------------------------


CSS_MIME_TYPE = "text/css"
JS_MIME_TYPE = "application/javascript"

# The set of icons SPPAS brings to the manager of Whakerexa, written
# "name:base:file1,file2,...". An icon is a small interchangeable sign asked
# for by a name: the set names the drawings SPPAS carries, and a name it does
# not carry is answered by the reference set of the framework.
# The loader reads an absolute path as it is, and only prefixes a relative
# one with data-base: the set says where it stands, from the root served.
# It is declared empty as long as the framework answers every name asked for:
# a drawing of its own is one more file in this list.
ICONS_SET_NAME = "icons"
ICONS_SET_FILES = ""
ICONS_SET = f"{ICONS_SET_NAME}:/{wapp_settings.icons}:{ICONS_SET_FILES}"

# The theme of SPPAS, declared to the loader: it is registered before the
# manager reads the address, so that ?wexa_theme=swapp is answered, and it
# stands before the themes of the repository in the cycle of the button.
THEME_NAME = "swapp"
THEME_SET = f"{THEME_NAME}:/{wapp_settings.css}main_swapp_theme.css"

# What the client announces a choice of the reader with. An empty value is
# the way a page of SPPAS is shown by default: the manager of the theme says
# so when the cycle of the button comes back to its beginning.
# The themes are the one SPPAS brings and the ones the loader adds because
# none of the framework's is named. A theme outside of this list belongs to
# an application, and is never kept as a preference.
THEME_NAMES = ("", THEME_NAME, "wexa_theme", "aurora", "highcontrast")
COLOR_NAMES = ("", "dark")
CONTRAST_NAMES = ("", "contrast")

# ---------------------------------------------------------------------------


class swappHeadNode(HTMLHeadNode):
    """Node for the head of each page.

    """

    def __init__(self, parent, title: str = "SPPAS"):
        """Create the head node.

        """
        super(swappHeadNode, self).__init__(parent)
        self.reset(title)

    # -----------------------------------------------------------------------

    def reset(self, title: str):
        """Reset the head to its default values.

        :param title: The title of the page to be added into the head.

        """
        # Delete the existing list of children
        self.clear_children()

        # The default meta tags
        self.meta({"charset": "utf-8"})
        self.meta({"http-equiv": "X-UA-Compatible", "content": "IE=edge"})
        self.meta({"name": "viewport",
                   "content": "width=device-width, initial-scale=1.0, user-scalable=yes"})

        # Add the given title
        title_node = HTMLNode(self.identifier, "title", "title", value=title)
        self.append_child(title_node)

        # Add the CSS style, from Whakerexa
        self.link(rel="stylesheet", href=wapp_settings.wexa_statics + "css/wexa.css", link_type=CSS_MIME_TYPE)
        self.link(rel="stylesheet", href=wapp_settings.wexa_statics + "css/layout.css", link_type=CSS_MIME_TYPE)
        self.link(rel="stylesheet", href=wapp_settings.wexa_statics + "css/button.css", link_type=CSS_MIME_TYPE)
        self.link(rel="stylesheet", href=wapp_settings.wexa_statics + "css/menu.css", link_type=CSS_MIME_TYPE)
        # Every page baking a message dialog needs it, and a sheet of the
        # framework is loaded before the sheets of SPPAS, never after.
        self.link(rel="stylesheet", href=wapp_settings.wexa_statics + "css/dialog.css", link_type=CSS_MIME_TYPE)

        print_css = HTMLNode(self.identifier, None, "link")
        print_css.add_attribute("rel", "stylesheet")
        print_css.add_attribute("href", wapp_settings.wexa_statics + "css/print.css")
        print_css.add_attribute("type", CSS_MIME_TYPE)
        print_css.add_attribute("media", "print")
        self.append_child(print_css)

        # Add the javascript, from Whakerexa. The loader chooses by itself
        # between the modules and the bundle, and declares the icon sets: a
        # name of an icon then answers, whatever the way the page is served.
        # The files are listed so that a name the set does not carry falls
        # back on the one of Whakerexa without any request.
        loader = HTMLNode(self.identifier, None, "script")
        loader.add_attribute("src", "/" + wapp_settings.wexa_statics + "js/wexa.loader.js")
        loader.add_attribute("data-base", "/" + wapp_settings.wexa_statics)
        # The buttons carrying a data-href: the loader hands them to
        # handleLinksWithParameters() once the framework is there. A page
        # cannot do it itself any more -- its own script runs first.
        loader.add_attribute(
            "data-links",
            "link-trace_button,link-sppas_button,link-feedback_button")
        loader.add_attribute("data-icons", ICONS_SET)
        loader.add_attribute("data-icons-default", ICONS_SET_NAME)
        loader.add_attribute("data-icons-fallback", ICONS_SET_NAME)
        loader.add_attribute("data-themes", THEME_SET)
        # The theme of SPPAS. What the reader chose is named in the address,
        # and the manager of the client applies it over this one.
        loader.add_attribute("data-default", THEME_NAME)
        self.append_child(loader)

        # Held for the applications inserting themselves into SPPAS: a
        # spin-off brings its theme with add_theme(), and the format of the
        # declaration stays where it is written.
        self.__loader = loader

    # -----------------------------------------------------------------------

    def add_theme(self, name: str, href: str) -> None:
        """Add a theme to the ones the page cycles through.

        The theme is declared before the ones already there: it is the one
        the page is shown with when it is also named as the default. The
        themes of Whakerexa are added by its loader, after all of them.

        :param name: (str) The name the theme answers to
        :param href: (str) Its address, from the root of the served files

        """
        declared = self.__loader.get_attribute_value("data-themes")
        self.__loader.set_attribute("data-themes",
                                    f"{name}:{href},{declared}")

    # -----------------------------------------------------------------------

    def set_default_theme(self, name: str) -> None:
        """Name the theme the page is shown with when the address names none.

        :param name: (str) The name of one of the declared themes

        """
        self.__loader.set_attribute("data-default", name)
