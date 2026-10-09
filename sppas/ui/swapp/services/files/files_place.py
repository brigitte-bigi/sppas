"""
:filename: sppas.ui.swapp.services.files.files_place.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The place the deposit API gives, and what is written in it.

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

from ..deposit.deposit_space import swappDepositSpace

# ---------------------------------------------------------------------------


class swappFilePlace:
    """Ask the deposit API for a place, and write the files in it.

    It is the only class of this service which calls that API, so it is the
    only one to be read again the day it changes. Nothing is decided here: a
    bound, a refusal and an hour are relayed as they were given.

    """

    def __init__(self, api: swappDepositSpace | None = None):
        """Create the access to the deposit API.

        :param api: (swappDepositSpace) The deposit API, None for a new one
        :raises: sppasTypeError: The given API is not a swappDepositSpace

        """
        if api is None:
            api = swappDepositSpace()
        if isinstance(api, swappDepositSpace) is False:
            raise sppasTypeError(api, "swappDepositSpace")

        self.__api = api
        self.__when = 0.

    # -----------------------------------------------------------------------

    def what_is_accepted(self) -> dict:
        """Return what the deposit API accepts.

        :return: (dict) The size of one file, the volume and the number of places

        """
        _size, _volume, _deposits = self.__api.what_is_accepted()

        _accepted = dict()
        _accepted["size"] = _size
        _accepted["volume"] = _volume
        _accepted["deposits"] = _deposits

        return _accepted

    # -----------------------------------------------------------------------

    def ask_for_a_place(self) -> str:
        """Return the place the deposit API gives.

        When it is refused, the hour at which there will be room is kept, to
        be said by when_there_will_be_room().

        :raises: OSError: The folder of the space cannot be made
        :return: (str) Empty when no place is given

        """
        _place, self.__when = self.__api.ask_for_a_place()

        return _place

    # -----------------------------------------------------------------------

    def when_there_will_be_room(self) -> tuple:
        """Return whether a place was refused, and when to come back.

        :return: (tuple) Whether the last place asked for was refused, and in how many seconds

        """
        return (self.__when > 0., self.__when)

    # -----------------------------------------------------------------------

    def put(self, place: str, name: str, content: bytes) -> bool:
        """Write a file in a place, under the name it is given.

        :param place: (str) Place the deposit API gave
        :param name: (str) Name the file stands under
        :param content: (bytes) Bytes of the file
        :raises: OSError: The file cannot be written
        :return: (bool) False when the deposit API refused it

        """
        _given, _reason = self.__api.put(place, name, content)

        return _given

    # -----------------------------------------------------------------------

    def why_not(self, place: str, name: str, content: bytes) -> str:
        """Return why the deposit API refuses a file, and write nothing.

        :param place: (str) Place the deposit API gave
        :param name: (str) Name the file would stand under
        :param content: (bytes) Bytes of the file
        :return: (str) Empty when the deposit API accepts it

        """
        _given, _reason = self.__api.put(place, name, content)

        return _reason

    # -----------------------------------------------------------------------

    def address_of(self, place: str, name: str) -> str:
        """Return the address a file of a place is reached at.

        :param place: (str) Place the deposit API gave
        :param name: (str) Name of the file
        :return: (str) Empty when the place is out of date or holds no such file

        """
        return self.__api.address_of(place, name)

    # -----------------------------------------------------------------------

    def path_of(self, place: str, name: str) -> str:
        """Return where a file of a place stands, with its path.

        :param place: (str) Place the deposit API gave
        :param name: (str) Name of the file
        :return: (str) Empty when the place is out of date or holds no such file

        """
        return self.__api.path_of(place, name)

    # -----------------------------------------------------------------------

    def serve(self, address: str) -> bytes:
        """Return the bytes an address names.

        :param address: (str) Address to be served
        :return: (bytes) Empty when there is nothing to give

        """
        return self.__api.serve(address)
