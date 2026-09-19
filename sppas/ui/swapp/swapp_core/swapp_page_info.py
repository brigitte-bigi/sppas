"""
:filename: sppas.ui.swapp.swapp_core.swapp_page_info.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: This is the SPPAS Web-based page information.

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

from dataclasses import dataclass
from typing import Type

from sppas.core.coreutils import sppasTypeError

# ---------------------------------------------------------------------------


@dataclass
class swappWebPageInfo:
    """Store metadata for a generic web page.

    :param recipe: (type) The ResponseRecipe class which bakes the page.
        It describes its page with the page(), name() and icon() class
        methods. Typically inherits from a BaseResponseRecipe class.
    :param show: (bool) Indicates whether the page gets a link button in
        the "Find out more" section of the Dashboard.

    """
    recipe: Type
    show: bool

    def __post_init__(self):
        if isinstance(self.recipe, type) is False and hasattr(self.recipe, "page") is False:
            raise sppasTypeError(type(self.recipe).__name__, "BaseResponseRecipe")
        if isinstance(self.show, bool) is False:
            raise sppasTypeError(type(self.show).__name__, "bool")
