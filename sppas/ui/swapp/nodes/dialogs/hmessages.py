# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.nodes.dialogs.hmessages.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Modal dialogs for messages in swapp.

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

    Copyright (C) 2011-2023  Brigitte Bigi, CNRS
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

from sppas.ui import _

from .hdialog import swappHTMLModalDialog

# ----------------------------------------------------------------------------


MSG_HEADER_ERROR = _("Error")
MSG_HEADER_WARNING = _("Warning")
MSG_HEADER_QUESTION = _("Question")
MSG_HEADER_INFO = _("Information")
MSG_MESSAGE = _("Message")

# -----------------------------------------------------------------------


class swappBaseMessageDialog(swappHTMLModalDialog):
    """Represent a modal dialog tree root element to display a message.

    """

    def __init__(self, parent, message, title, style="information"):
        """Create an HTML node with <div> element and its content.

        """
        super(swappBaseMessageDialog, self).__init__(parent, None)

        # Fill-in the header
        if style == "error":
            if title is None:
                title = MSG_HEADER_ERROR
        elif style == "warning":
            if title is None:
                title = MSG_HEADER_WARNING
        elif style == "question":
            if title is None:
                title = MSG_HEADER_QUESTION
        else:
            if title is None:
                title = MSG_HEADER_INFO
        self.set_title(title)

        # Fill-in the content
        txt = HTMLNode(self.content_node.identifier, None, "p", value=message)
        self.content_node.append_child(txt)

        # Fill-in the action
        self._create_action_buttons()

    # -----------------------------------------------------------------------

    def _create_action_buttons(self):
        """Override to create the buttons and bind events."""
        raise NotImplementedError

# ---------------------------------------------------------------------------
# Information/Warning/Error: only one action to say "ok"!
# ---------------------------------------------------------------------------


class swappInformationDialog(swappBaseMessageDialog):
    """Represent a modal dialog tree root element to display an information.

    """

    def __init__(self, parent, message):
        """Create an HTML node with <div> element and its content.

        """
        super(swappInformationDialog, self).__init__(parent, message, None, style="information")

    # -----------------------------------------------------------------------

    def _create_action_buttons(self):
        """Overriden. Create an Okay button.

        """
        js = "document.getElementById('" + self.identifier + "').style.display='none';"
        self.add_action("close", onclick=js)

# ---------------------------------------------------------------------------


class swappWarnDialog(swappBaseMessageDialog):
    """Represent a modal dialog tree root element to display a warning msg.

    """

    def __init__(self, parent, message):
        """Create an HTML node with <div> element and its content.

        """
        super(swappWarnDialog, self).__init__(parent, message, None, style="warning")

    # -----------------------------------------------------------------------

    def _create_action_buttons(self):
        """Overriden. Create an Okay button."""
        js = "document.getElementById('" + self.identifier + "').style.display='none';"
        self.add_action("close", onclick=js)

# ---------------------------------------------------------------------------


class swappErrorDialog(swappBaseMessageDialog):
    """Represent a modal dialog tree root element to display an error msg.

    """

    def __init__(self, parent, message):
        """Create an HTML node with <div> element and its content.

        """
        super(swappErrorDialog, self).__init__(parent, message, None, style="error")

    # -----------------------------------------------------------------------

    def _create_action_buttons(self):
        """Overriden. Create an Okay button."""
        js = "document.getElementById('" + self.identifier + "').style.display='none';"
        self.add_action("close", onclick=js)

# ---------------------------------------------------------------------------
# Question: possibly more than one action to answer the question.
# ---------------------------------------------------------------------------


class swappYesNoDialog(swappBaseMessageDialog):
    """Represent a modal dialog tree root element to display a question.

    """

    def __init__(self, parent, message):
        """Create an HTML node with <div> element and its content.

        """
        super(swappYesNoDialog, self).__init__(parent, message, None, style="question")

    # -----------------------------------------------------------------------

    def _create_action_buttons(self):
        """Overriden. Create an Okay button."""
        js = "document.getElementById('" + self.identifier + "').style.display='none';"
        self.add_action("no", onclick=js)
        self.add_action("yes", onclick=js)

# ---------------------------------------------------------------------------


class swappConfirmDialog(swappBaseMessageDialog):
    """Represent a modal dialog tree root element to display a confirmation.

    """

    def __init__(self, parent, message):
        """Create an HTML node with <div> element and its content.

        """
        super(swappConfirmDialog, self).__init__(parent, message, None, style="question")

    # -----------------------------------------------------------------------

    def _create_action_buttons(self):
        """Overriden. Create an Okay button."""
        js = "document.getElementById('" + self.identifier + "').style.display='none';"
        self.add_action("cancel", onclick=js)
        self.add_action("okay", onclick=js)
