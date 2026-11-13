"""
:filename: sppas.ui.swapp.services.options.options_request.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What is asked of the provision of files for one option.

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

# ---------------------------------------------------------------------------


class swappFileRequest:
    """The request for a file of the person, and the option it is for."""

    def __init__(self, option: str):
        """Create the request of a file for one option.

        :param option: (str) Key of the option the file is asked for

        """
        self.__option = option

    # -----------------------------------------------------------------------

    def get_option(self) -> str:
        """Return the key of the option the file is asked for (str)."""
        return self.__option

    option = property(get_option, None)
