"""
:filename: sppas.ui.agnostic.appcom_base.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Base class to communicate on a socket between swapp and wxapp.

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

import json

from sppas.core import sppasError

# ---------------------------------------------------------------------------

# Version of the communication protocol, announced in the HELLO message.
COMM_PROTOCOL_VERSION = 2

# ---------------------------------------------------------------------------


class sppasCommKeys:
    """The shared vocabulary of the messages exchanged on the socket.

    Both UIs (swapp and wxapp) use these named constants as the "key" of
    every message, in both directions. The integer value is what travels
    on the wire; the name is what appears in the code and in the logs.

    """

    # Control messages, sent by a client
    STOP = 0     # ask the server to stop listening
    PING = 1     # are you alive? expects ACK
    HELLO = 2    # handshake. value = {"source": str, "version": int, "port": int}
    BYE = 3      # the interlocutor announces its shutdown

    # Response messages, sent back by a server
    ACK = 10     # request understood and processed. value = response payload
    ERROR = 11   # request failed. value = human-readable message

    # Application messages, sent in both directions
    WKP_CHANGED = 20   # the workspace changed. value = its serialized dict
    TRACE = 21         # a python logging record. value = its serialized dict
    SHOW_PAGE = 22     # show a page of the interface. value = its name

    # An exit asked for by one interface, and answered by the other. The
    # asked one answers its verdict right away when it has one, and an ACK
    # when it has to ask its own reader: the verdict is then sent later,
    # as a message of its own.
    EXIT_REQUEST = 23  # do you accept to close? expects EXIT_OK/EXIT_NO/ACK
    EXIT_OK = 24       # the interface accepts to close
    EXIT_NO = 25       # the interface refuses to close

    # -----------------------------------------------------------------------

    @staticmethod
    def name_of(key: int) -> str:
        """Return the constant name of a key value, for the logs.

        :param key: (int) The value of one of the constants of this class.
        :return: (str) The constant name, or the value itself if unknown.

        """
        for name, value in vars(sppasCommKeys).items():
            if name.isupper() is True and value == key:
                return name
        return str(key)

# ---------------------------------------------------------------------------


class sppasCommServerError(sppasError):
    """Raised when a socket is not listening."""

    def __init__(self, error) -> None:
        self._status = 40
        self.parameter = f":ERROR 40: Server error: {error}"
        self.error = error

# ---------------------------------------------------------------------------


class sppasCommServerAddressError(sppasError):
    """Raised when a socket error occurs."""

    def __init__(self, host: str, port) -> None:
        self._status = 42
        self.parameter = f":ERROR 42: Invalid host {host} or port {port}."
        self.host = host
        self.port = port

# ---------------------------------------------------------------------------


class sppasCommServerDataError(sppasError):
    """Raised when received data are not valid"""

    def __init__(self, error) -> None:
        self._status = 44
        self.parameter = f":ERROR 44: Invalid received data: {error}"
        self.error = error

# ---------------------------------------------------------------------------


class sppasCommunication:
    """Base class for communication in a socket.

    """

    def __init__(self, host: str, port: int):
        """Initialize sppasCommunication with all parameters.

        :param host: (str) Host IP address
        :param port: (int) Port number

        """
        # Server address
        self.__host = ""
        self.__port = 0
        self.set_host(host)
        self.set_port(port)

    # -----------------------------------------------------------------------
    # Getters and setters
    # -----------------------------------------------------------------------

    # -------------------- HOST --------------------

    def get_host(self) -> str:
        """Get the host IP address."""
        return self.__host

    def set_host(self, value: str) -> None:
        """Set the host IP address."""
        if isinstance(value, str) is False:
            raise TypeError("host must be a string")
        self.__host = value

    host = property(get_host, set_host)

    # -------------------- PORT --------------------

    def get_port(self) -> int:
        """Get the port number."""
        return self.__port

    def set_port(self, value: int) -> None:
        """Set the port number."""
        if isinstance(value, int) is False:
            raise TypeError("port must be an integer")
        self.__port = value

    port = property(get_port, set_port)

    # -----------------------------------------------------------------------
    # The message envelope, shared by both directions
    # -----------------------------------------------------------------------

    @staticmethod
    def format_message(key: int, value) -> str:
        """Create the serialized JSON envelope of a message.

        The same envelope is used for the requests and for the responses.

        :param key: (int) One of the sppasCommKeys constants
        :param value: (any) A JSON-serializable object
        :raises: TypeError: Invalid key type
        :return: (str) The ready-to-send JSON string

        """
        if isinstance(key, int) is False:
            raise TypeError("message key must be an integer")

        data = dict()
        data["key"] = key
        data["value"] = value

        return json.dumps(data, ensure_ascii=False)

    # -----------------------------------------------------------------------

    @staticmethod
    def parse_message(data: str):
        """Parse the serialized JSON envelope of a message.

        :param data: (str) A received JSON string
        :raises: sppasCommServerDataError: Missing or invalid envelope field
        :raises: json.JSONDecodeError: The received data can't be parsed
        :return: (tuple) The (key, value) of the message

        """
        parsed = json.loads(data)

        if "key" not in parsed:
            raise sppasCommServerDataError("'key' key missing in received data.")
        if "value" not in parsed:
            raise sppasCommServerDataError("'value' key missing in received data.")
        if isinstance(parsed["key"], int) is False:
            raise sppasCommServerDataError("key must be an integer in received data.")

        return parsed["key"], parsed["value"]

