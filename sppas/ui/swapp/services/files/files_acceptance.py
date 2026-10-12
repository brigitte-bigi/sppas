"""
:filename: sppas.ui.swapp.services.files.files_acceptance.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What SPPAS reads, and what the deposit API accepts.

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

from sppas.core.config import sppasExtensionsSettings
from sppas.core.coreutils import sppasTypeError
from sppas.src.anndata.aio import extensions as annot_extensions
from sppas.src.imgdata import image_extensions
from sppas.ui import _
from sppas.src.videodata import video_extensions

from .files_place import swappFilePlace

# ---------------------------------------------------------------------------

MSG_NAME_TAKEN = _("This name is already taken.")

# The first bytes of a file which is run instead of being read.
EXECUTABLES = (b"MZ", b"\x7fELF", b"#!", b"\xca\xfe\xba\xbe", b"\xcf\xfa\xed\xfe")

# ---------------------------------------------------------------------------


class swappDepositAcceptance:
    """Answer whether a file can be deposited, and say why it cannot.

    It knows what SPPAS reads, which is said by the settings of SPPAS and by
    the packages which read the files. The bounds are not its own: they are
    asked of the deposit API and relayed as they were given.

    """

    def __init__(self, place: swappFilePlace | None = None):
        """Create the acceptance of what is deposited.

        :param place: (swappFilePlace) The places of the deposit API, None for a new one
        :raises: sppasTypeError: The given place is not a swappFilePlace

        """
        if place is None:
            place = swappFilePlace()
        if isinstance(place, swappFilePlace) is False:
            raise sppasTypeError(place, "swappFilePlace")

        self.__place = place

    # -----------------------------------------------------------------------

    @staticmethod
    def extensions() -> list:
        """Return the extensions of the files SPPAS reads.

        :return: (list of str) In lower case, the dot included

        """
        _extensions = list()
        with sppasExtensionsSettings() as _settings:
            for _ext in _settings.AUDIO:
                _extensions.append(_ext.lower())
        for _ext in image_extensions:
            _extensions.append(_ext.lower())
        for _ext in video_extensions:
            _extensions.append(_ext.lower())
        for _ext in annot_extensions:
            _extensions.append(_ext.lower())

        return _extensions

    # -----------------------------------------------------------------------

    def what_is_accepted(self) -> dict:
        """Return the bounds of the deposit API, and what SPPAS reads.

        :return: (dict) It depends on no file and on no deposit

        """
        _accepted = self.__place.what_is_accepted()
        _accepted["extensions"] = swappDepositAcceptance.extensions()

        return _accepted

    # -----------------------------------------------------------------------

    def accepts(self, name: str, feeding) -> tuple:
        """Answer on the name of a file, and say why it is refused.

        :param name: (str) Name of the file, without any path
        :param feeding: (swappDataFiles) The files fed so far
        :raises: sppasTypeError: The given name is not a string
        :return: (tuple) Whether it is accepted, and why it is not

        """
        if isinstance(name, str) is False:
            raise sppasTypeError(name, "str")

        for _fed in feeding.files:
            if _fed.name == name:
                return (False, MSG_NAME_TAKEN)

        return (True, "")

    # -----------------------------------------------------------------------

    def accepts_size(self, size: int | float) -> bool:
        """Answer on the size of a file.

        :param size: (int|float) Size of one file, in bytes
        :return: (bool) False beyond what the deposit API accepts

        """
        return size <= self.__place.what_is_accepted()["size"]

    # -----------------------------------------------------------------------

    def accepts_volume(self, volume: int | float) -> bool:
        """Answer on the volume of what is to be sent.

        :param volume: (int|float) Volume of one deposit, in bytes
        :return: (bool) False beyond what the deposit API accepts

        """
        return volume <= self.__place.what_is_accepted()["volume"]

    # -----------------------------------------------------------------------

    def accepts_one_more_deposit(self) -> tuple:
        """Answer on the number of deposits, and say when to come back.

        Neither the answer nor the hour is invented here: both are what the
        deposit API said when a place was last asked for.

        :return: (tuple) Whether a deposit can be made, and in how many seconds it can

        """
        _refused, _when = self.__place.when_there_will_be_room()

        return (_refused is False, _when)

    # -----------------------------------------------------------------------

    def accepts_content(self, content: bytes) -> bool:
        """Answer on the bytes of a file.

        A file which is run instead of being read is refused, and it is said
        by its bytes and never by its name.

        :param content: (bytes) The first bytes of the file are enough
        :raises: sppasTypeError: The given content is not bytes
        :return: (bool) False when the bytes say an executable or a script

        """
        if isinstance(content, bytes) is False:
            raise sppasTypeError(content, "bytes")

        for _said in EXECUTABLES:
            if content.startswith(_said) is True:
                return False

        return True
