"""
:filename: sppas.ui.swapp.services.files.files_delivery.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The address of a produced file, and what it serves.

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

from .files_place import swappFilePlace

# ---------------------------------------------------------------------------


class swappResultDelivery:
    """Give the address of a produced file, and serve what it names.

    An address leads to the file it names and to nothing else of the machine,
    and it lives as long as the file does: both are answered by the place the
    file stands in.

    Nothing calls this class yet. Where the files stand already, a produced
    file is reached where it was written and no address is made -- which is
    what the organisational model says of PF5 in that case. The address of a
    produced file, and the hour at which it goes, are what the deposit brings
    with it: they are to be asked for when the files have to be brought, and
    put in the record under "reachable_until", which the delivery view shows
    already.

    """

    def __init__(self, place: swappFilePlace | None = None):
        """Create the delivery of the produced files.

        :param place: (swappFilePlace) The places of the deposit API, None for a new one
        :raises: sppasTypeError: The given place is not a swappFilePlace

        """
        if place is None:
            place = swappFilePlace()
        if isinstance(place, swappFilePlace) is False:
            raise sppasTypeError(place, "swappFilePlace")

        self.__place = place

    # -----------------------------------------------------------------------

    def address_of(self, place: str, name: str) -> str:
        """Return the address a produced file is reached at.

        :param place: (str) Place the file stands in
        :param name: (str) Name of the file
        :return: (str) Empty when the file is not reached at any address

        """
        return self.__place.address_of(place, name)

    # -----------------------------------------------------------------------

    def serve(self, address: str) -> bytes:
        """Return the bytes an address names.

        Nothing at all is answered when the file is out of date and when the
        address names none: the two are one answer.

        :param address: (str) Address to be served
        :return: (bytes) Empty when there is nothing to give

        """
        return self.__place.serve(address)
