"""
:filename: sppas.ui.wxapp.main_comm.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The communication server of the wx application.

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

import logging
import wx

from sppas.ui.agnostic import sppasCommServer
from sppas.ui.agnostic import sppasCommKeys

from .events import sppasCommMessageEvent

# ---------------------------------------------------------------------------


class wxappCommServer(sppasCommServer):
    """The interlocutor of the swapp UI, on the wx side.

    Receive the messages the swapp UI sends on the socket, and propagate
    each of them to the wx event loop: a sppasCommMessageEvent is posted
    to the top window, from which the panels can Bind it.

    The server runs in a daemon thread: it never touches the UI itself,
    it only posts events -- wx.PostEvent is thread-safe.

    """

    def __init__(self, host: str, port: int, app: wx.App):
        """Create the communication server of the wx application.

        :param host: (str) Host IP address
        :param port: (int) Port number
        :param app: (wx.App) The application owning the top window

        """
        super(wxappCommServer, self).__init__(host, port)
        self.__app = app

    # -----------------------------------------------------------------------

    def _prepare_response(self, key: int, value) -> str:
        """Override. Propagate the received message and acknowledge it.

        The protocol-level messages (ping, hello) are answered by the
        parent class. Any other message -- including a BYE, sent by swapp
        to announce its own shutdown -- is posted to the top window as a
        sppasCommMessageEvent.

        :param key: (int) One of the sppasCommKeys constants, sent by the client.
        :param value: (any) The value sent by the client.
        :return: (str) The response to the client, in the shared JSON envelope.

        """
        if key in (sppasCommKeys.PING, sppasCommKeys.HELLO):
            return super(wxappCommServer, self)._prepare_response(key, value)

        window = self.__app.GetTopWindow()
        if window is None:
            logging.error("No top window to propagate the received message to.")
            return self.format_message(sppasCommKeys.ERROR, "No window to notify.")

        event = sppasCommMessageEvent(-1)
        event.SetKey(key)
        event.SetValue(value)
        wx.PostEvent(window, event)

        return self.format_message(sppasCommKeys.ACK, "Message propagated.")
