# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.services.files.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The init file of the provision of files package

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

from .files_feeding import swappDataFiles
from .files_feeding import swappDataFeeding
from .files_workspace import swappWorkspaceFiles
from .files_handing import swappAppExchange
from .files_record import swappFilesRecord
from .files_view import swappDepositView
from .files_view import swappDeliveryView
from .files_acceptance import swappDepositAcceptance
from .files_place import swappFilePlace
from .files_delivery import swappResultDelivery
from .files_chooser import swappFileChooser
from .files_provision import swappFileProvision
from .files_controller import swappFilesController
from .files_manager import swappFilesManager

# -----------------------------------------------------------------------

__all__ = (
    "swappDataFiles",
    "swappDataFeeding",
    "swappWorkspaceFiles",
    "swappAppExchange",
    "swappFilesRecord",
    "swappDepositView",
    "swappDeliveryView",
    "swappDepositAcceptance",
    "swappFilePlace",
    "swappResultDelivery",
    "swappFileChooser",
    "swappFileProvision",
    "swappFilesController",
    "swappFilesManager"
)
