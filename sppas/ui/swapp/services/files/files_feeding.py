"""
:filename: sppas.ui.swapp.services.files.files_feeding.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The data of the files a person feeds, and their place.

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
from sppas.core.coreutils import sppasValueError
from sppas.core.coreutils import NegativeValueError
from sppas.core.coreutils import sppasUnicode

# ---------------------------------------------------------------------------


class swappDataFeeding:
    """Represent the data of a feeding: a name, a size and a content.

    The three values are checked when the data is created: a name is not a
    path, a size is a whole number of bytes, and a content can be empty.

    """

    def __init__(self, name: str, size: int | float, content: bytes | str = ""):
        """Create the data of one feeding.

        :param name: (str) Name of the file, without any path
        :param size: (int|float) Size of the file, in bytes, a whole number
        :param content: (bytes|str) Bytes of the file, empty if there is none
        :raises: sppasTypeError: The name, the size or the content is of a wrong type
        :raises: sppasValueError: The name is empty or is a path, or the size is not whole
        :raises: NegativeValueError: The size is negative

        """
        self.__name = swappDataFeeding.validate_name(name)
        self.__size = swappDataFeeding.validate_size(size)
        self.__content = swappDataFeeding.validate_content(content)

    # -----------------------------------------------------------------------

    @staticmethod
    def validate_name(name: str) -> str:
        """Return the given name if a file can be written under it.

        A name is not a path: a name walking a disk is refused, and never
        cut down to its last part.

        :param name: (str) Name to be validated
        :raises: sppasTypeError: The given name is not a string
        :raises: sppasValueError: The given name is empty, or is a path
        :return: (str) The given name, without its surrounding spaces

        """
        if isinstance(name, str) is False:
            raise sppasTypeError(name, "str")

        _filename = sppasUnicode(name).unicode().strip()
        if len(_filename) == 0:
            raise sppasValueError("name", name)
        if _filename in (".", "..") or "/" in _filename or "\\" in _filename:
            raise sppasValueError("name", name)

        return _filename

    # -----------------------------------------------------------------------

    @staticmethod
    def validate_size(size: int | float) -> int:
        """Return the given size if it can be the size of a file.

        A size is counted in bytes, so it is a whole number. A number with
        decimals is refused, and never cut down to its integer part.

        :param size: (int|float) Size to be validated, in bytes
        :raises: sppasTypeError: The given size is not a number
        :raises: sppasValueError: The given size is not a whole number
        :raises: NegativeValueError: The given size is negative
        :return: (int) The given size

        """
        if isinstance(size, (int, float)) is False:
            raise sppasTypeError(size, "int")
        if int(size) < 0:
            raise NegativeValueError(size)
        if size != int(size):
            raise sppasValueError("size", size)

        return int(size)

    # -----------------------------------------------------------------------

    @staticmethod
    def validate_content(content: bytes | str) -> bytes | str:
        """Return the given content if it can be the content of a file.

        :param content: (bytes|str) Content to be validated
        :raises: sppasTypeError: The given content is neither bytes nor a string
        :return: (bytes|str) The given content

        """
        if isinstance(content, (bytes, str)) is False:
            raise sppasTypeError(content, "bytes")

        return content

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the file, without any path (str)."""
        return self.__name

    # -----------------------------------------------------------------------

    def get_size(self) -> int:
        """Return the size of the file, in bytes (int)."""
        return self.__size

    # -----------------------------------------------------------------------

    def get_content(self) -> bytes | str:
        """Return the bytes of the file.

        :return: (bytes|str) Empty if the content was not given

        """
        return self.__content

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    name = property(get_name, None)
    size = property(get_size, None)
    content = property(get_content, None)

# ---------------------------------------------------------------------------


class swappDataFiles:
    """Represent the data of the fed files, and the place for them.

    The files are held in the order they were added, and their volume is
    summed on demand. A file is added or removed, and nothing else is done
    to it.

    """

    def __init__(self, place: str = ""):
        """Create the data of the fed files, with no file in it.

        :param place: (str) Place given for the files, empty if there is none

        """
        self.__place = ""
        self.__files = list()
        self.set_place(place)

    # -----------------------------------------------------------------------

    def feed(self, name: str, size: int | float, content: bytes | str = "") -> int:
        """Add a file.

        Only the types of the given values are verified.

        :param name: (str) Name of the file, without any path
        :param size: (int|float) Size of the file, in bytes, a whole number
        :param content: (bytes|str) Bytes of the file, if they are known
        :return: (int) Volume of the files, in bytes

        """
        self.__files.append(swappDataFeeding(name, size, content))
        return self.volume()

    # -----------------------------------------------------------------------

    def take_back(self, name: str) -> int:
        """Remove a file.

        Removing a file which was never added does nothing.

        :param name: (str) Name of the file to remove
        :raises: sppasTypeError: The given name is not a string
        :return: (int) Volume of the files, in bytes

        """
        if isinstance(name, str) is False:
            raise sppasTypeError(name, "str")

        for _a_file in reversed(self.__files):
            if _a_file.name == name:
                self.__files.remove(_a_file)

        return self.volume()

    # -----------------------------------------------------------------------

    def volume(self) -> int:
        """Return the volume of the files, in bytes.

        :return: (int) Sum of the sizes, zero if there is no file

        """
        _volume = 0
        for _a_file in self.__files:
            _volume += _a_file.size

        return _volume

    # -----------------------------------------------------------------------

    def get_place(self) -> str:
        """Return the place of the files.

        :return: (str) Empty if no place was given

        """
        return self.__place

    # -----------------------------------------------------------------------

    def set_place(self, place: str) -> None:
        """Set the place of the files.

        :param place: (str) Place given for the files
        :raises: sppasTypeError: The given place is not a string

        """
        if isinstance(place, str) is False:
            raise sppasTypeError(place, "str")

        self.__place = place.strip()

    # -----------------------------------------------------------------------

    def get_files(self) -> list:
        """Return the files, in the order they were added.

        :return: (list of swappDataFeeding) Can be empty

        """
        return self.__files

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    place = property(get_place, set_place)
    files = property(get_files, None)
