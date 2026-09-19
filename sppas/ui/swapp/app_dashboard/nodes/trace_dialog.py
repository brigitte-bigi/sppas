"""
:filename: sppas.ui.swapp.app_dashboard.nodes.trace_dialog.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The dialog inviting the user to open the Journal tab.

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

# The long version of the message is in the "po" files.
MSG_CHECK = _("Please check the Journal tab regularly.")
MSG_OPEN = _("Open the Journal")

# ---------------------------------------------------------------------------


class swappTraceInfoDialog(HTMLNode):
    """A dialog inviting the user to open -- and keep -- the Journal tab.

    The dialog replaces the permanent log window of the wx interface: it
    is baked into the Dashboard whenever the trace page gives no sign of
    life. Its single button opens the named tab of the trace page, so the
    user either has the tab, or has this message telling to open it.

    """

    ID = "trace_dialog"

    def __init__(self, parent_id):
        super(swappTraceInfoDialog, self).__init__(parent_id, swappTraceInfoDialog.ID, "dialog")
        self.add_attribute("id", self.identifier)
        self.add_attribute("role", "alertdialog")
        self.add_attribute("aria-labelledby", "trace_dialog_p")
        self.add_attribute("class", "info")

        check_p = HTMLNode(self.identifier, "trace_dialog_p", "p", value=MSG_CHECK)
        self.append_child(check_p)

        open_button = HTMLNode(self.identifier, "trace_dialog_button", "button", value=MSG_OPEN)
        open_button.add_attribute("id", "trace_dialog_button")
        open_button.add_attribute("class", "action-button")
        open_button.add_attribute("data-href", "journal.html")
        open_button.add_attribute("data-target", "sppas_infos")
        self.append_child(open_button)
