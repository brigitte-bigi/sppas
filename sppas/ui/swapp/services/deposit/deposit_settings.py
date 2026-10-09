"""
:filename: sppas.ui.swapp.services.deposit.deposit_settings.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The values the deposit space holds to, said once.

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

import os
import tempfile

from sppas.core.coreutils import sppasTypeError
from sppas.core.coreutils import sppasValueError
from sppas.core.coreutils import NegativeValueError

# ---------------------------------------------------------------------------

MINUTE = 60.
MEGABYTE = 1024 * 1024

# ---------------------------------------------------------------------------


class swappDepositSettings:
    """Convenient class to hold the values of the deposit space.

    Each value is said here and read from here: a value written twice is a
    value which will differ from itself. Three of them are decided by SPPAS;
    the size of one file is not, the front server refusing beyond it.

    """

    def __init__(self):
        """Create the settings with the value of each entry."""
        self.__space = os.path.join(tempfile.gettempdir(), "sppas_deposit")
        self.__duration = 30. * MINUTE
        self.__signature_life = 30. * MINUTE
        self.__file_size = 10 * MEGABYTE
        self.__place_volume = 100 * MEGABYTE
        self.__places = 10

    # -----------------------------------------------------------------------

    def get_space(self) -> str:
        """Return the folder the places stand in.

        :return: (str)

        """
        return self.__space

    # -----------------------------------------------------------------------

    def set_space(self, space: str) -> None:
        """Set the folder the places stand in.

        :param space: (str) Name of the folder, with its path
        :raises: sppasTypeError: The given folder is not a string

        """
        if isinstance(space, str) is False:
            raise sppasTypeError(space, "str")

        self.__space = space

    # -----------------------------------------------------------------------

    def get_duration(self) -> float:
        """Return how long a place lasts, in seconds.

        :return: (float)

        """
        return self.__duration

    # -----------------------------------------------------------------------

    def set_duration(self, duration: int | float) -> None:
        """Set how long a place lasts, in seconds.

        :param duration: (int|float) Duration of a place
        :raises: sppasTypeError: The given duration is not a number
        :raises: NegativeValueError: The given duration is negative

        """
        self.__duration = swappDepositSettings.validate_number(duration)

    # -----------------------------------------------------------------------

    def get_signature_life(self) -> float:
        """Return how long what authorises an address lasts, in seconds.

        :return: (float) Never less than the duration of a place

        """
        return self.__signature_life

    # -----------------------------------------------------------------------

    def set_signature_life(self, life: int | float) -> None:
        """Set how long what authorises an address lasts, in seconds.

        :param life: (int|float) Life of a signature
        :raises: sppasTypeError: The given life is not a number
        :raises: NegativeValueError: The given life is negative
        :raises: sppasValueError: The given life is shorter than a place lasts

        """
        _life = swappDepositSettings.validate_number(life)
        if _life < self.__duration:
            raise sppasValueError("signature_life", life)

        self.__signature_life = _life

    # -----------------------------------------------------------------------

    def get_file_size(self) -> int:
        """Return the size one file does not exceed, in bytes.

        :return: (int)

        """
        return self.__file_size

    # -----------------------------------------------------------------------

    def set_file_size(self, size: int | float) -> None:
        """Set the size one file does not exceed, in bytes.

        :param size: (int|float) Size of one file
        :raises: sppasTypeError: The given size is not a number
        :raises: NegativeValueError: The given size is negative

        """
        self.__file_size = int(swappDepositSettings.validate_number(size))

    # -----------------------------------------------------------------------

    def get_place_volume(self) -> int:
        """Return the volume one place does not exceed, in bytes.

        :return: (int)

        """
        return self.__place_volume

    # -----------------------------------------------------------------------

    def set_place_volume(self, volume: int | float) -> None:
        """Set the volume one place does not exceed, in bytes.

        :param volume: (int|float) Volume of one place
        :raises: sppasTypeError: The given volume is not a number
        :raises: NegativeValueError: The given volume is negative

        """
        self.__place_volume = int(swappDepositSettings.validate_number(volume))

    # -----------------------------------------------------------------------

    def get_places(self) -> int:
        """Return how many places the space holds at a time.

        :return: (int)

        """
        return self.__places

    # -----------------------------------------------------------------------

    def set_places(self, places: int | float) -> None:
        """Set how many places the space holds at a time.

        :param places: (int|float) Number of places
        :raises: sppasTypeError: The given number is not a number
        :raises: NegativeValueError: The given number is negative

        """
        self.__places = int(swappDepositSettings.validate_number(places))

    # -----------------------------------------------------------------------

    @staticmethod
    def validate_number(value: int | float) -> float:
        """Return the given value if it can be one of the settings.

        :param value: (int|float) Value to be validated
        :raises: sppasTypeError: The given value is not a number
        :raises: NegativeValueError: The given value is negative
        :return: (float) The given value

        """
        if isinstance(value, (int, float)) is False:
            raise sppasTypeError(value, "int")
        if value < 0:
            raise NegativeValueError(value)

        return float(value)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    space = property(get_space, set_space)
    duration = property(get_duration, set_duration)
    signature_life = property(get_signature_life, set_signature_life)
    file_size = property(get_file_size, set_file_size)
    place_volume = property(get_place_volume, set_place_volume)
    places = property(get_places, set_places)
