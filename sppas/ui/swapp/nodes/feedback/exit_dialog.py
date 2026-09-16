# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.nodes.feedback.exit_dialog.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The dialog shown while the exit waits for the other interface.

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

from whakerpy.htmlmaker import HTMLNode

from sppas.ui import _

# ---------------------------------------------------------------------------

MSG_WAIT = _("SPPAS is waiting for your answer in the Desktop window.")

# ---------------------------------------------------------------------------


class ExitWaitDialog(HTMLNode):
    """A dialog shown while an exit waits for the answer of the Desktop.

    An exit of SPPAS is the exit of both interfaces, or of none. While the
    Desktop asks its own reader, this dialog is what the web interface
    shows, and it carries no button: there is nothing to decide here.
    It is baked into every Dashboard and shown by the periodic poll, so
    that a second tab and a reloaded page find the same state -- the one
    of the server, not the one of the page which asked.

    """

    ID = "exit_dialog"

    def __init__(self, parent_id):
        super(ExitWaitDialog, self).__init__(parent_id, ExitWaitDialog.ID, "dialog")
        self.add_attribute("id", self.identifier)
        self.add_attribute("role", "alertdialog")
        self.add_attribute("aria-labelledby", "exit_dialog_p")
        self.add_attribute("class", "hidden-alert info")

        wait_p = HTMLNode(self.identifier, "exit_dialog_p", "p", value=MSG_WAIT)
        self.append_child(wait_p)
