"""
:filename: sppas.ui.swapp.app_dashboard.nodes.agree_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The agreement dialog of the SPPAS Dashboard Application.

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

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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


MSG_INFO = _("By using SPPAS, you are encouraged to mention it")
MSG_AGREE = _("I agree")

# ---------------------------------------------------------------------------


class swappAgreementDialog(HTMLNode):
    """A dialog for the user to accept the license requirements.

    """

    ID = "agreement_dialog"

    def __init__(self, parent_id):
        super(swappAgreementDialog, self).__init__(parent_id, swappAgreementDialog.ID, "dialog")
        self.add_attribute("id", self.identifier)
        self.add_attribute("role", "alertdialog")
        self.add_attribute("aria-labelledby", "agree_p")
        self.add_attribute("class", "info")

        agree_p = HTMLNode(self.identifier, "agree_p", "p", value=MSG_INFO)
        self.append_child(agree_p)

        agree_button = HTMLNode(self.identifier, "agree_button", "button", value=MSG_AGREE)
        agree_button.add_attribute("id", "agree_button")
        agree_button.add_attribute("class", "action-button")
        self.append_child(agree_button)
