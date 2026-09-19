# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.nodes.feedback.hstatusnode.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A set of nodes to represent the HTTPD response status.

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

from sppas.core.config import sg
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import HTMLTree
from whakerpy.httpd import HTTPDStatus
from sppas.ui import _

from ...swappcore.swappsg import swapp_settings

# ---------------------------------------------------------------------------


MSG_TITLE_410 = _("Session ended")
MSG_DESCR_410 = _("You can close this tab. [...]")

# ---------------------------------------------------------------------------


class HTMLTreeStatus(HTMLTree):
    """An HTMLtree to create a page with a specific status.

    """

    def __init__(self, status, msg_title: str = "", msg: str = ""):
        """Create an HTML Tree for a status response.

        :param status: (HTTPDStatus) The status of the response.
        :param msg_title: (str) The title of the message.
        :param msg: (str) Optional parameter, a message to display any information

        """
        super(HTMLTreeStatus, self).__init__(f"tree_{status.code}")

        code_name = HTTPDStatus.HTTPD_STATUS.get(status.code, "")
        self._create_head(code_name)
        self._create_body(status, msg_title, msg, code_name)

    # -----------------------------------------------------------------------

    def _create_head(self, title, msg_title: str = "", msg: str = ""):
        """Fill-in the head element of the tree."""

        # The meta tags
        self.head.meta({"charset": "utf-8"})
        self.head.meta({"http-equiv": "X-UA-Compatible", "content": "IE=edge"})
        self.head.meta({"name": "keywords",
                        "content": "SPPAS, Brigitte, Bigi, CNRS"})
        self.head.meta({"name": "viewport",
                        "content": "width=device-width, initial-scale=1.0, user-scalable=yes"})

        # The title
        self.head.title(title)

        # The CSS is added directly into to the page
        self.add_css(swapp_settings.css + "errors.css")

    # -----------------------------------------------------------------------

    def _create_body(self, status, msg_title: str = "", msg: str = "", code_name: str = ""):
        """Fill-in the body element of the tree.

        :param status: (HTTPDStatus) The status of the response.
        :param msg_title: (str) The title of the message.
        :param msg: (str) Optional parameter, a message to display any information
        :param code_name: (str) The description of the HTTPD status.

        """
        if status.code < 300:
            code_class = "status2xx"
        elif status.code < 400:
            code_class = "status3xx"
        elif status.code < 500:
            code_class = "status4xx"
        else:
            code_class = "status5xx"

        self.body_header.set_value(f"""<h1>CODE {status.code} - {code_name}</h1>""")
        self.body_header.add_attribute("class", code_class)
        self.body_main.set_value(f"""<h2>{msg_title}</h2><p>{msg}</p> """)
        self.body_footer.set_value(f"""
                <p>Powered by <a href="https://sppas.org">SPPAS</a></p>
                <p>{sg.__copyright__}</p>
        """)

# ---------------------------------------------------------------------------


class HTMLTreeError410(HTMLTreeStatus):
    """A node to represent the 410 HTTPD response status.

    """
    def __init__(self):
        """Create the HTML410StatusNode node."""
        super(HTMLTreeError410, self).__init__(
            HTTPDStatus(410), MSG_TITLE_410, MSG_DESCR_410)

# ---------------------------------------------------------------------------


class HTMLStatusNode(HTMLNode):
    """A node to represent an HTTPD response status and a message.

    Deprecated.

    """

    def __init__(self, parent_id, identifier="und", code=200, text="", description=""):
        """Create the HTMLStatusNode node.

        :param parent_id: (str) Identifier of the parent node
        :param identifier: (str) Identifier of this node
        :param code: (int) Response status code
        :param text: (str) Optional short message text
        :param description: (str) Optional description text

        """
        super(HTMLStatusNode, self).__init__(parent_id, identifier, "section")

        # Add the actual content
        self.__create_content(code, text, description)

    # -----------------------------------------------------------------------

    def __create_content(self, code, text, description):
        """Add the HTML content.

        :param code: (int) Response status code
        :param text: (str) Optional short message text
        :param description: (str) Optional description text

        """
        code_name = HTTPDStatus.HTTPD_STATUS.get(code, "")
        node_value = f"""	
            <h1>CODE {code} - {code_name}</h1>
            <h2>{text}</h2>
            <p>{description}</p>
        """
        self.set_value(node_value)
