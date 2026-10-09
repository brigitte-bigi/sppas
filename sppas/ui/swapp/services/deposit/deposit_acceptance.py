"""
:filename: sppas.ui.swapp.services.deposit.deposit_acceptance.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What the deposit space accepts, answered on numbers.

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

from sppas.core.coreutils import sppasTypeError

from .deposit_settings import swappDepositSettings

# ---------------------------------------------------------------------------


class swappSpaceAcceptance:
    """Answer whether a size, a volume or a number of places is accepted.

    It reads no disk and writes nothing: it is given a number and answers on
    the values of the settings. The number of places it answers on is counted
    by whoever asks, after the forgetting.

    """

    def __init__(self, settings: swappDepositSettings | None = None):
        """Create the acceptance of the deposit space.

        :param settings: (swappDepositSettings) Values to answer on, None for the default ones
        :raises: sppasTypeError: The given settings are not swappDepositSettings

        """
        if settings is None:
            settings = swappDepositSettings()
        if isinstance(settings, swappDepositSettings) is False:
            raise sppasTypeError(settings, "swappDepositSettings")

        self.__settings = settings

    # -----------------------------------------------------------------------

    def what_is_accepted(self) -> tuple:
        """Return the size of one file, the volume of one place, the places.

        :return: (tuple) Three values, as the settings hold them

        """
        return (self.__settings.file_size,
                self.__settings.place_volume,
                self.__settings.places)

    # -----------------------------------------------------------------------

    def accepts_size(self, size: int | float) -> bool:
        """Return True if a file of the given size is accepted.

        :param size: (int|float) Size of one file, in bytes
        :raises: sppasTypeError: The given size is not a number
        :return: (bool) False beyond the size one file may be

        """
        if isinstance(size, (int, float)) is False:
            raise sppasTypeError(size, "int")

        return size <= self.__settings.file_size

    # -----------------------------------------------------------------------

    def accepts_volume(self, volume: int | float) -> bool:
        """Return True if a place holding the given volume is accepted.

        :param volume: (int|float) Volume of one place, in bytes
        :raises: sppasTypeError: The given volume is not a number
        :return: (bool) False beyond the volume one place may hold

        """
        if isinstance(volume, (int, float)) is False:
            raise sppasTypeError(volume, "int")

        return volume <= self.__settings.place_volume

    # -----------------------------------------------------------------------

    def accepts_one_more_place(self, places: int) -> bool:
        """Return True if a place can be made while the space holds the given ones.

        :param places: (int) Number of places standing, counted after the forgetting
        :raises: sppasTypeError: The given number is not a number
        :return: (bool) False when the space already holds as many places as it may

        """
        if isinstance(places, (int, float)) is False:
            raise sppasTypeError(places, "int")

        return places < self.__settings.places
