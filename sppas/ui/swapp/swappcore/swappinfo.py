"""
:filename: sppas.ui.swapp.swappinfo.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: This is the SPPAS Web-based application information.

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

    Copyright (C) 2011-2026 Brigitte Bigi
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
class swappWebApplicationInfo:
    """Store metadata for a web application.

    :param name: (str) Identifier name used to refer to the application.
    :param bakery: (type) The class used to represent or launch the
        application. Typically inherits from a WebSiteData class.
    :param show: (bool) Indicates whether the app should appear in the GUI.

    """
    name: str
    bakery: Type
    show: bool

    def __post_init__(self):
        if isinstance(self.name, str) is False:
            raise sppasTypeError(type(self.name).__name__, "string")
        if isinstance(self.bakery, type) is False and hasattr(self.bakery, "bake_response") is False:
            raise sppasTypeError(type(self.bakery).__name__, "WebSiteData")
        if isinstance(self.show, bool) is False:
            raise sppasTypeError(type(self.show).__name__, "bool")
