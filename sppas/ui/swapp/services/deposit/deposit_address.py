"""
:filename: sppas.ui.swapp.services.deposit.deposit_address.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The address a file of a place is reached at.

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
from .deposit_place import swappSpaceFolder

# ---------------------------------------------------------------------------


class swappFileAddress:
    """Make the address of a file of a place, and read what one names.

    An address leads to a file of a place and to nothing else of the machine:
    it is made of a place and of a name, and both are read again when it is
    followed. What authorises it is verified by the front of the machine,
    which holds the secret; this class neither holds it nor reads it.

    """

    PREFIX = "/deposit/"

    def __init__(self, settings: swappDepositSettings | None = None):
        """Create the addresses of the deposit space.

        :param settings: (swappDepositSettings) Values to read on, None for the default ones
        :raises: sppasTypeError: The given settings are not swappDepositSettings

        """
        if settings is None:
            settings = swappDepositSettings()
        if isinstance(settings, swappDepositSettings) is False:
            raise sppasTypeError(settings, "swappDepositSettings")

        self.__settings = settings

    # -----------------------------------------------------------------------

    def address_of(self, place: str, name: str) -> str:
        """Return the address a file of a place is reached at.

        It does not verify that the file stands there: that is asked of the
        folder of the space before.

        :param place: (str) Name of the place
        :param name: (str) Name of the file
        :return: (str) Empty if the place or the name names nothing of the space

        """
        _place = swappSpaceFolder.validate_entry(place)
        _name = swappSpaceFolder.validate_entry(name)
        if len(_place) == 0 or len(_name) == 0:
            return ""

        return swappFileAddress.PREFIX + _place + "/" + _name

    # -----------------------------------------------------------------------

    def what_it_names(self, address: str) -> tuple:
        """Return the place and the name an address names.

        :param address: (str) Address to be read
        :return: (tuple) Two empty names if it names nothing of the space

        """
        if isinstance(address, str) is False:
            return ("", "")
        if address.startswith(swappFileAddress.PREFIX) is False:
            return ("", "")

        _parts = address[len(swappFileAddress.PREFIX):].split("/")
        if len(_parts) != 2:
            return ("", "")

        _place = swappSpaceFolder.validate_entry(_parts[0])
        _name = swappSpaceFolder.validate_entry(_parts[1])
        if len(_place) == 0 or len(_name) == 0:
            return ("", "")

        return (_place, _name)

    # -----------------------------------------------------------------------

    def signature_life(self) -> float:
        """Return how long what authorises an address lasts, in seconds.

        :return: (float) Never less than the duration of a place

        """
        return self.__settings.signature_life
