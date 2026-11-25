# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.swapp_base.swapp_help_button.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application Help button of the nav of any app.

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

from sppas.ui import _

from .swapp_help import HELP_TASK
from .swapp_help import BACK_TASK
from .swapp_help import MSG_BACK

# ---------------------------------------------------------------------------

MSG_HELP = _("Help")

# The identifier of the Help button of the nav: its key clicks it by it.
HELP_BUTTON_ID = "link-help_button"

# ---------------------------------------------------------------------------


class swappHelpButton(HTMLNode):
    """The Help button of the nav of an app, the way back while the help is shown.

    It is written once, with the nav, and it keeps its identifier and its
    form whatever the view the page shows: its key does what it does. What
    it sends and what it says change with that view.

    """

    def __init__(self, parent: str, form_id: str):
        """Create the Help button of the nav of an app.

        :param parent: (str) Identifier of the node the button is appended to
        :param form_id: (str) Identifier of the form the button sends

        """
        super(swappHelpButton, self).__init__(parent, HELP_BUTTON_ID, "button")
        self.add_attribute("id", HELP_BUTTON_ID)
        self.add_attribute("type", "submit")
        self.add_attribute("form", form_id)
        self.add_attribute("name", "event_bake")
        self.add_attribute("aria-keyshortcuts", "h")
        self.add_attribute("class", "menuitem")
        self.set_back(False)

    # -----------------------------------------------------------------------

    def set_back(self, back: bool) -> None:
        """Make the button the way back from the help, or the Help button.

        :param back: (bool) True while the help is shown

        """
        _task = HELP_TASK
        _text = MSG_HELP
        _icon = "help"
        if back is True:
            _task = BACK_TASK
            _text = MSG_BACK
            _icon = "arrow-up"

        self.set_value("<span>" + _text + "</span>")
        self.set_attribute("value", _task)
        self.set_attribute("data-icon", _icon)
        self.set_attribute("aria-label", _text)
        # What the label does not say: the key doing the same thing.
        self.set_attribute("title", _text + " (h)")
