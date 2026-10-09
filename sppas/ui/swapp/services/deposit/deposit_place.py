"""
:filename: sppas.ui.swapp.services.deposit.deposit_place.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A place of the deposit space, and the folder it stands in.

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
import random
import shutil
import time

from sppas.core.coreutils import sppasTypeError

from .deposit_settings import swappDepositSettings

# ---------------------------------------------------------------------------


class swappPlace:
    """Convenient class to read the moment a place was made at.

    The moment is carried by the name of the place and is read from it, never
    from a disk: what a folder says is the moment it was last written into,
    which moves at every file put in the place. A name this class did not
    make carries no moment.

    """

    PREFIX = "place"
    SEPARATOR = "_"
    DRAWN = 8

    def __init__(self, name: str, settings: swappDepositSettings | None = None):
        """Create the reading of a place.

        :param name: (str) Name of the place
        :param settings: (swappDepositSettings) Values to read on, None for the default ones
        :raises: sppasTypeError: The given name is not a string

        """
        if isinstance(name, str) is False:
            raise sppasTypeError(name, "str")
        if settings is None:
            settings = swappDepositSettings()
        if isinstance(settings, swappDepositSettings) is False:
            raise sppasTypeError(settings, "swappDepositSettings")

        self.__name = name
        self.__settings = settings

    # -----------------------------------------------------------------------

    @staticmethod
    def a_name_for(moment: int | float) -> str:
        """Return the name of a place made at the given moment.

        What the name carries besides the moment is drawn, so that two places
        made in one second are two names.

        :param moment: (int|float) Moment the place is made at, in seconds
        :raises: sppasTypeError: The given moment is not a number
        :return: (str) Name of a place

        """
        if isinstance(moment, (int, float)) is False:
            raise sppasTypeError(moment, "int")

        _drawn = ""
        for _i in range(swappPlace.DRAWN):
            _drawn += random.choice("0123456789abcdef")

        return swappPlace.SEPARATOR.join((swappPlace.PREFIX, str(int(moment)), _drawn))

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the place.

        :return: (str)

        """
        return self.__name

    # -----------------------------------------------------------------------

    def moment(self) -> float:
        """Return the moment the place was made at, read from its name.

        :return: (float) Zero if the name is not one this class made

        """
        _parts = self.__name.split(swappPlace.SEPARATOR)
        if len(_parts) != 3:
            return 0.
        if _parts[0] != swappPlace.PREFIX:
            return 0.
        if _parts[1].isdigit() is False:
            return 0.
        if len(_parts[2]) != swappPlace.DRAWN:
            return 0.

        return float(_parts[1])

    # -----------------------------------------------------------------------

    def is_of_this_hour(self) -> bool:
        """Return True if the place has not outlived its duration.

        :return: (bool) False if the name is not one this class made

        """
        _moment = self.moment()
        if _moment == 0.:
            return False

        return (time.time() - _moment) <= self.__settings.duration

    # -----------------------------------------------------------------------

    name = property(get_name, None)

# ---------------------------------------------------------------------------


class swappSpaceFolder:
    """Convenient class to read and write the places on a disk.

    It is the only class of this service which touches a disk. It judges no
    bound: what it is asked to make was judged before it was called.

    """

    def __init__(self, settings: swappDepositSettings | None = None):
        """Create the access to the folder of the deposit space.

        :param settings: (swappDepositSettings) Values to read on, None for the default ones
        :raises: sppasTypeError: The given settings are not swappDepositSettings

        """
        if settings is None:
            settings = swappDepositSettings()
        if isinstance(settings, swappDepositSettings) is False:
            raise sppasTypeError(settings, "swappDepositSettings")

        self.__settings = settings

    # -----------------------------------------------------------------------

    @staticmethod
    def validate_entry(entry: str) -> str:
        """Return the given name if it names something of the space.

        A name walking a disk is refused, and never cut down to its last part.

        :param entry: (str) Name of a place or of a file
        :return: (str) The given name, or an empty one if it names nothing here

        """
        if isinstance(entry, str) is False:
            return ""
        if len(entry) == 0 or entry in (".", ".."):
            return ""
        if "/" in entry or "\\" in entry or os.sep in entry:
            return ""

        return entry

    # -----------------------------------------------------------------------

    def make_a_place(self, name: str) -> str:
        """Make the folder of a place.

        The folder is made, or the name is taken and nothing is made: it is
        not looked for first, so two requests never both pass.

        :param name: (str) Name of the place, which swappPlace made
        :raises: OSError: The folder of the space cannot be made
        :return: (str) The name of the place, or an empty one if it is taken

        """
        _name = swappSpaceFolder.validate_entry(name)
        if len(_name) == 0:
            return ""

        os.makedirs(self.__settings.space, exist_ok=True)
        try:
            os.mkdir(os.path.join(self.__settings.space, _name))
        except FileExistsError:
            return ""

        return _name

    # -----------------------------------------------------------------------

    def places(self) -> list:
        """Return the names of the places standing in the space.

        Nothing of them is opened, and the disk is asked nothing about them.

        :return: (list of str) Can be empty

        """
        _places = list()
        if os.path.isdir(self.__settings.space) is False:
            return _places

        for _entry in sorted(os.listdir(self.__settings.space)):
            if os.path.isdir(os.path.join(self.__settings.space, _entry)) is True:
                _places.append(_entry)

        return _places

    # -----------------------------------------------------------------------

    def delete(self, name: str) -> None:
        """Delete the folder of a place, and everything it holds.

        Deleting what is not there does nothing wrong.

        :param name: (str) Name of the place

        """
        _name = swappSpaceFolder.validate_entry(name)
        if len(_name) == 0:
            return

        shutil.rmtree(os.path.join(self.__settings.space, _name), ignore_errors=True)

    # -----------------------------------------------------------------------

    def make_a_file(self, place: str, name: str, content: bytes) -> bool:
        """Write a file in a place, under the name it is given.

        The file is made, or the name is taken and what stands there is left
        untouched: it is not looked for first.

        :param place: (str) Name of the place
        :param name: (str) Name the file stands under
        :param content: (bytes) Bytes of the file
        :raises: OSError: The file cannot be written
        :return: (bool) False if the name is taken, or names nothing here

        """
        _filename = self.filename_of(place, name)
        if len(_filename) == 0:
            return False
        if os.path.isdir(os.path.dirname(_filename)) is False:
            return False

        try:
            with open(_filename, "xb") as _fd:
                _fd.write(content)
        except FileExistsError:
            return False

        return True

    # -----------------------------------------------------------------------

    def files(self, place: str) -> list:
        """Return the names of the files standing in a place.

        :param place: (str) Name of the place
        :return: (list of str) Can be empty

        """
        _place = swappSpaceFolder.validate_entry(place)
        if len(_place) == 0:
            return list()

        _folder = os.path.join(self.__settings.space, _place)
        if os.path.isdir(_folder) is False:
            return list()

        _files = list()
        for _entry in sorted(os.listdir(_folder)):
            if os.path.isfile(os.path.join(_folder, _entry)) is True:
                _files.append(_entry)

        return _files

    # -----------------------------------------------------------------------

    def volume(self, place: str) -> int:
        """Return the volume of a place, in bytes.

        :param place: (str) Name of the place
        :return: (int) Zero if the place holds nothing, or is not there

        """
        _place = swappSpaceFolder.validate_entry(place)
        if len(_place) == 0:
            return 0

        _volume = 0
        for _name in self.files(_place):
            _volume += os.path.getsize(os.path.join(self.__settings.space, _place, _name))

        return _volume

    # -----------------------------------------------------------------------

    def read(self, place: str, name: str) -> bytes:
        """Return the bytes of a file of a place.

        :param place: (str) Name of the place
        :param name: (str) Name of the file
        :return: (bytes) Empty if the file is not there

        """
        _filename = self.filename_of(place, name)
        if len(_filename) == 0:
            return b""

        try:
            with open(_filename, "rb") as _fd:
                return _fd.read()
        except OSError:
            return b""

    # -----------------------------------------------------------------------

    def filename_of(self, place: str, name: str) -> str:
        """Return the name of a file of a place, with its path.

        :param place: (str) Name of the place
        :param name: (str) Name of the file
        :return: (str) Empty if the place or the name names nothing here

        """
        _place = swappSpaceFolder.validate_entry(place)
        _name = swappSpaceFolder.validate_entry(name)
        if len(_place) == 0 or len(_name) == 0:
            return ""

        return os.path.join(self.__settings.space, _place, _name)
