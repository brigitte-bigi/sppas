"""
:filename: sppas.core.config.heartbeat.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary: The last sign of life of something announcing itself.

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

    Copyright (C) 2011-2026 Brigitte Bigi
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

from __future__ import annotations
import time
import threading

# ---------------------------------------------------------------------------


class sppasHeartbeat:
    """The last sign of life of something which announces itself.

    Whatever announces itself periodically -- a page displaying the traces,
    the wx interface, any other interlocutor -- is known to be there by the
    freshness of its last sign of life, and by nothing else. A crash, a kill
    or a closed tab stops the signs: the silence is the answer. Nothing has
    to announce a death nobody is left alive to announce.

    :Example:
    >>> beat = sppasHeartbeat(max_age=90.)
    >>> beat.ping()
    >>> beat.alive()
    True

    """

    def __init__(self, max_age: float = 40.):
        """Create a sppasHeartbeat instance.

        :param max_age: (float) Age of the last sign of life, in seconds,
        above which the interlocutor is considered gone.

        """
        self.__max_age = float(max_age)
        self.__seen = None
        self.__lock = threading.Lock()

    # -----------------------------------------------------------------------

    def get_max_age(self) -> float:
        """Return the age above which the interlocutor is considered gone."""
        return self.__max_age

    # -----------------------------------------------------------------------

    def ping(self) -> None:
        """Store the time of a sign of life."""
        with self.__lock:
            self.__seen = time.time()

    # -----------------------------------------------------------------------

    def forget(self) -> None:
        """Drop the last sign of life: the interlocutor announced its end."""
        with self.__lock:
            self.__seen = None

    # -----------------------------------------------------------------------

    def alive(self, max_age: float | None = None) -> bool:
        """Return True if the last sign of life is recent enough.

        :param max_age: (float) Override the age given at creation
        :return: (bool)

        """
        if max_age is None:
            max_age = self.__max_age
        with self.__lock:
            if self.__seen is None:
                return False
            return (time.time() - self.__seen) < max_age

    # -----------------------------------------------------------------------

    def age(self) -> float | None:
        """Return the age of the last sign of life, or None."""
        with self.__lock:
            if self.__seen is None:
                return None
            return time.time() - self.__seen
