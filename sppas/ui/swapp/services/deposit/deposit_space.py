"""
:filename: sppas.ui.swapp.services.deposit.deposit_space.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A place for the files which have to travel.

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

import time

from sppas.core.coreutils import sppasTypeError

from .deposit_settings import swappDepositSettings
from .deposit_acceptance import swappSpaceAcceptance
from .deposit_place import swappPlace
from .deposit_place import swappSpaceFolder
from .deposit_address import swappFileAddress

# ---------------------------------------------------------------------------

MSG_NO_ROOM = "Every place is taken."
MSG_OUT_OF_DATE = "This place is out of date."
MSG_SIZE = "This file is beyond the size one file may be."
MSG_VOLUME = "This file is beyond the volume one place may hold."
MSG_NAME_TAKEN = "A file of this name already stands in this place."

# ---------------------------------------------------------------------------


class swappDepositSpace:
    """Give a place where files may stand, and forget what is out of date.

    It holds nothing between two calls: the space is read again at every one
    of them, so two callers in two processes see one space without knowing of
    each other. Every operation begins by forgetting the places which have
    outlived their duration, which no caller asks for and none is told of.

    """

    def __init__(self, settings: swappDepositSettings | None = None):
        """Create the deposit space.

        :param settings: (swappDepositSettings) Values to hold to, None for the default ones
        :raises: sppasTypeError: The given settings are not swappDepositSettings

        """
        if settings is None:
            settings = swappDepositSettings()
        if isinstance(settings, swappDepositSettings) is False:
            raise sppasTypeError(settings, "swappDepositSettings")

        self.__settings = settings
        self.__acceptance = swappSpaceAcceptance(settings)
        self.__folder = swappSpaceFolder(settings)
        self.__address = swappFileAddress(settings)

    # -----------------------------------------------------------------------

    def what_is_accepted(self) -> tuple:
        """Return the size of one file, the volume of one place, the places.

        :return: (tuple) Three values, which depend on no place and on no file

        """
        self.forget()

        return self.__acceptance.what_is_accepted()

    # -----------------------------------------------------------------------

    def ask_for_a_place(self) -> tuple:
        """Return a place of its own, or when there will be room.

        :raises: OSError: The folder of the space cannot be made
        :return: (tuple) The name of an empty place and zero, or an empty name and an hour

        """
        self.forget()

        _places = self.__folder.places()
        if self.__acceptance.accepts_one_more_place(len(_places)) is False:
            return ("", self.__when_there_will_be_room(_places))

        _name = ""
        while len(_name) == 0:
            _name = self.__folder.make_a_place(swappPlace.a_name_for(time.time()))

        return (_name, 0.)

    # -----------------------------------------------------------------------

    def put(self, place: str, name: str, content: bytes) -> tuple:
        """Write a file in a place, under the name it is given.

        The size and the volume are judged before anything is written, so a
        file which is refused leaves nothing in the place.

        :param place: (str) Name of the place
        :param name: (str) Name the file stands under
        :param content: (bytes) Bytes of the file
        :raises: OSError: The file cannot be written
        :return: (tuple) Whether it stands there, and why it does not

        """
        self.forget()

        if swappPlace(place, self.__settings).is_of_this_hour() is False:
            return (False, MSG_OUT_OF_DATE)
        if self.__acceptance.accepts_size(len(content)) is False:
            return (False, MSG_SIZE)
        if self.__acceptance.accepts_volume(self.__folder.volume(place) + len(content)) is False:
            return (False, MSG_VOLUME)
        if self.__folder.make_a_file(place, name, content) is False:
            return (False, MSG_NAME_TAKEN)

        return (True, "")

    # -----------------------------------------------------------------------

    def address_of(self, place: str, name: str) -> str:
        """Return the address a file of a place is reached at.

        :param place: (str) Name of the place
        :param name: (str) Name of the file
        :return: (str) Empty if the place is out of date, or holds no such file

        """
        self.forget()

        if swappPlace(place, self.__settings).is_of_this_hour() is False:
            return ""
        if name not in self.__folder.files(place):
            return ""

        return self.__address.address_of(place, name)

    # -----------------------------------------------------------------------

    def path_of(self, place: str, name: str) -> str:
        """Return where a file of a place stands, with its path.

        A caller which has to read a file where it was written is given it,
        and no other name of the machine is ever answered.

        :param place: (str) Name of the place
        :param name: (str) Name of the file
        :return: (str) Empty if the place is out of date, or holds no such file

        """
        self.forget()

        if swappPlace(place, self.__settings).is_of_this_hour() is False:
            return ""
        if name not in self.__folder.files(place):
            return ""

        return self.__folder.filename_of(place, name)

    # -----------------------------------------------------------------------

    def serve(self, address: str) -> bytes:
        """Return the bytes an address names.

        Nothing at all is answered when the place is out of date, when the
        address names no file, and when it names something of the machine
        which is not a file of a place: the three are one answer.

        :param address: (str) Address to be served
        :return: (bytes) Empty when there is nothing to give

        """
        self.forget()

        _place, _name = self.__address.what_it_names(address)
        if len(_place) == 0:
            return b""
        if swappPlace(_place, self.__settings).is_of_this_hour() is False:
            return b""

        return self.__folder.read(_place, _name)

    # -----------------------------------------------------------------------

    def forget(self) -> None:
        """Delete every place which has outlived its duration.

        It answers nobody: no caller asks for it, and a caller whose place
        went is not told.

        """
        for _name in self.__folder.places():
            if swappPlace(_name, self.__settings).is_of_this_hour() is False:
                self.__folder.delete(_name)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __when_there_will_be_room(self, places: list) -> float:
        """Return in how many seconds the oldest place will have run out.

        :param places: (list of str) Names of the places standing in the space
        :return: (float) More than zero, no place outliving its duration

        """
        _oldest = time.time()
        for _name in places:
            _moment = swappPlace(_name, self.__settings).moment()
            if _moment > 0. and _moment < _oldest:
                _oldest = _moment

        _left = _oldest + self.__settings.duration - time.time()
        if _left <= 0.:
            return 1.

        return _left
