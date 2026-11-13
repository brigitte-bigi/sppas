# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.services.options.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The init file of the service of the options package

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

from .options_acceptance import swappValueAcceptance
from .options_set import swappOptionSet
from .options_request import swappFileRequest
from .options_file import swappFileForOption
from .options_record import swappOptionsRecord
from .options_view import swappOptionsView
from .options_controller import swappOptionsController
from .options_manager import swappOptionsManager

# -----------------------------------------------------------------------

__all__ = (
    "swappValueAcceptance",
    "swappOptionSet",
    "swappFileRequest",
    "swappFileForOption",
    "swappOptionsRecord",
    "swappOptionsView",
    "swappOptionsController",
    "swappOptionsManager"
)
