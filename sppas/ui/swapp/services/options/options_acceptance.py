"""
:filename: sppas.ui.swapp.services.options.options_acceptance.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Say whether a value suits the kind of an option.

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

from sppas.src.structs.baseoption import strtobool

# ---------------------------------------------------------------------------


class swappValueAcceptance:
    """Say whether a value suits the option it is given for.

    It is given an option and a value, and it answers. It reads no disk,
    holds no set and knows no page, and it judges nothing of what a value
    means: two values which contradict each other are both accepted.

    """

    def accepts(self, option, value) -> bool:
        """Return True if the value suits the kind of the option.

        :param option: (sppasOption) The option the value is given for
        :param value: (str) The value which was given
        :return: (bool)

        """
        _kind = option.get_type()
        _given = str(value).strip()

        if _kind == "bool":
            return strtobool(_given) != -1
        if _kind == "int":
            return swappValueAcceptance.__is_a(int, _given)
        if _kind == "float":
            return swappValueAcceptance.__is_a(float, _given)

        return True

    # -----------------------------------------------------------------------

    def what_is_expected(self, option) -> str:
        """Return what a value for the option has to be, said in a few words.

        :param option: (sppasOption) The option a value is given for
        :return: (str)

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __is_a(number, given: str) -> bool:
        """Return True if the given string is written as such a number.

        :param number: (type) Either int or float
        :param given: (str) What was given
        :return: (bool)

        """
        try:
            number(given)
        except ValueError:
            return False

        return True
