"""
:filename: sppas.ui.swapp.swapp_core.swapp_exc.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary: Utilities for SPPAS Web-based applications.

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

    Copyright (C) 2011-2023 Brigitte Bigi
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

from sppas.core.coreutils import error

# -----------------------------------------------------------------------


class swappHTMLIncompleteFieldset(ValueError):
    """:ERROR 0977:.

    The input field '{:s}' is not completed.

    """

    def __init__(self, field_name):
        self._status = 977
        self.parameter = error(self._status) + \
                         (error(self._status, "globals")).format(field_name)

    def __str__(self):
        return repr(self.parameter)

    def get_status(self):
        return self._status

    status = property(get_status, None)
