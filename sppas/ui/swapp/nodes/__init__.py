"""
:filename: sppas.ui.swapp.nodes.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The reusable HTML nodes of the swapp package.

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

from .inputs.hcheckbox import swappHTMLCheckboxNode
from .buttons.hbutton import swappHTMLButton
from .buttons.hbutton import swappHTMLLink
from .buttons.hbutton import swappLinkButtonNode
from .dialogs.hdialog import swappHTMLModalDialog
from .dialogs.hmessages import swappConfirmDialog
from .dialogs.hmessages import swappInformationDialog
from .dialogs.hmessages import swappWarnDialog
from .dialogs.hmessages import swappErrorDialog
from .dialogs.hmessages import swappYesNoDialog
from .layout.hheader import swappHeader
from .layout.hfooter import swappFooter
from .feedback.progress import swappProgressBar

# ---------------------------------------------------------------------------


__all__ = (
    "swappHTMLCheckboxNode",
    "swappHTMLButton",
    "swappHTMLLink",
    "swappLinkButtonNode",
    "swappHTMLModalDialog",
    "swappConfirmDialog",
    "swappInformationDialog",
    "swappWarnDialog",
    "swappErrorDialog",
    "swappYesNoDialog",
    "swappHeader",
    "swappFooter",
    "swappProgressBar"
)
