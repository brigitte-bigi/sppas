# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.swapp_base.swapp_help.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application view of the help of any app.

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
import html
import logging
import os

from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.ui import _

from ..swapp_core.swappsg import swapp_settings

# ---------------------------------------------------------------------------

MSG_BACK = _("Back")
MSG_NO_HELP = _("The help of this application is not written yet.")

# The task asking for the help of an app, the same for every app.
HELP_TASK = "swapp_help"

# The task going back from the help to the default view of the app.
BACK_TASK = "swapp_back"

# The identifier of the view of the help, in the main content of the page.
HELP_ID = "swapp_help"

# The identifier of the form of the Help button of an app which has no form.
HELP_FORM_ID = "swapp_help_form"

# ---------------------------------------------------------------------------


class swappHelpNode(TagNode):
    """The view of the help of an app: the way back, and the document of the app.

    The help is a view of the app, asked for with the form of the app. What
    that form transmitted is carried by the form of the help, hidden, and is
    sent with the way back: the app answers it with its default view, and
    the help changes nothing of what the app holds.

    """

    def __init__(self, parent: str, document: str, form_id: str, fields: dict):
        """Create the view of the help of an app.

        :param parent: (str) Identifier of the node the help is appended to
        :param document: (str) Path of the document of the app, relative to swapp, empty if it has none
        :param form_id: (str) Identifier of the form of the app, empty if it has none
        :param fields: (dict) What the form of the app transmitted, by name

        """
        super(swappHelpNode, self).__init__(parent, HELP_ID, "section", attributes={"id": HELP_ID})

        # The form of the help takes the identifier of the form of the app:
        # the Help button of the nav, which is tied to it, is tied to a form
        # while the help is shown too.
        _attributes = {"method": "post"}
        if len(form_id) > 0:
            _attributes["id"] = form_id
        _form = TagNode(self.identifier, None, "form", attributes=_attributes)
        self.append_child(_form)

        _back = TagNode(_form.identifier, None, "button",
                        attributes={"type": "submit", "name": "event_bake", "value": BACK_TASK,
                                    "data-icon": "arrow-up"})
        _form.append_child(_back)
        _back.append_child(HTMLNode(_back.identifier, None, "span", value=MSG_BACK))

        # A value is written as it was sent: its quotes are escaped, or the
        # attribute would end at the first one.
        for _name in fields:
            _value = html.escape(str(fields[_name]), quote=True)
            _form.append_child(EmptyNode(_form.identifier, None, "input",
                                         attributes={"type": "hidden", "name": _name, "value": _value}))

        self.append_child(swappHelpNode.__document(self.identifier, document))

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __document(parent: str, document: str) -> HTMLNode:
        """Return the document of the app, or what is said in its place.

        The file is written as it is: it is HTML already, and turning it into
        nodes would only be a way of losing it.

        :param parent: (str) Identifier of the node the document is appended to
        :param document: (str) Path of the document, relative to swapp, empty if the app has none
        :return: (HTMLNode)

        """
        if len(document) == 0:
            return HTMLNode(parent, None, "p", value=MSG_NO_HELP)

        filename = os.path.join(swapp_settings.base_dir, document)
        if os.path.isfile(filename) is False:
            msg = f"Document {document} not found (filename: {filename})."
            logging.error(msg)
            return HTMLNode(parent, None, "p", value=msg)

        with open(filename, "r", encoding="utf-8") as fp:
            return HTMLNode(parent, None, "div", value=fp.read())
