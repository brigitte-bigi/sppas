"""
:filename: sppas.ui.swapp.main_comm.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The communication server of the web application.

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

from __future__ import annotations
import logging
import threading

from sppas.src.wkps.wio import sppasWJSON
from sppas.ui.agnostic import sppasCommServer
from sppas.ui.agnostic import sppasCommClient
from sppas.ui.agnostic import sppasCommKeys
from sppas.ui.agnostic import sppasCommServerError

from .wappcore.wappsg import wapp_wkps
from .wappcore.wappsg import wapp_wxstate
from .wappcore.wappsg import wapp_trace
from .wappcore.wappsg import notify_wkp_changed
from .main_trace_store import swappTraceStore

# ---------------------------------------------------------------------------


class sppasWappCommServer(sppasCommServer):
    """The interlocutor of the wx UI, on the swapp side.

    Receive the messages the wx UI sends on the socket. The HELLO message
    registers the interlocutor -- in particular the port of its own
    communication server: it is what makes the full-duplex possible, with
    the send() method creating a client toward that port.

    """

    def __init__(self, host: str, port: int):
        """Create the communication server of the web application.

        :param host: (str) Host IP address
        :param port: (int) Port number

        """
        super(sppasWappCommServer, self).__init__(host, port)
        # The interlocutor declared by the last received HELLO, or None.
        # Keys: "source" (str), "version" (int), "port" (int).
        self.__interlocutor = None

    # -----------------------------------------------------------------------

    def get_interlocutor(self) -> dict | None:
        """Return the registered interlocutor, or None.

        :return: (dict|None) The value of the last received HELLO message.

        """
        return self.__interlocutor

    # -----------------------------------------------------------------------

    def send(self, key: int, value) -> str:
        """Send a message to the interface which announced itself.

        The port is the one of the shared state: it is the single place
        saying where the other UI listens, so that asking it whether it is
        there and sending it a message never disagree.

        :param key: (int) One of the sppasCommKeys constants
        :param value: (any) A JSON-serializable object
        :raises: sppasCommServerError: Nobody to send to, or sending failed.
        :return: (str) The response of the interlocutor -- JSON envelope.

        """
        if wapp_wxstate.port is None:
            raise sppasCommServerError("No interface announced itself to send to.")

        client = sppasCommClient(self.host, wapp_wxstate.port)
        request = client.format_request(key, value)
        return client.request(request)

    # -----------------------------------------------------------------------

    def _prepare_response(self, key: int, value) -> str:
        """Override. Register the interlocutor and answer the messages.

        The HELLO and BYE messages register/un-register the interlocutor.
        The WKP_CHANGED message stores the received workspace into the
        shared state -- the workspaces manager of the web application.

        :param key: (int) One of the sppasCommKeys constants, sent by the client.
        :param value: (any) The value sent by the client.
        :return: (str) The response to the client, in the shared JSON envelope.

        """
        if key == sppasCommKeys.PING:
            # A ping is the sign of life of the interlocutor: the wx
            # interface signs periodically, and its silence is the only
            # report a crashed interface is able to make.
            if isinstance(value, dict) is True and value.get("source", "") == "wxapp":
                wapp_wxstate.running = True

        if key == sppasCommKeys.HELLO:
            if isinstance(value, dict) is True and "port" in value:
                self.__interlocutor = value
                logging.info(f"Interlocutor registered: {value}")
                # The shared state allows the Dashboard to disable the launch
                # of a second wx instance: only one is allowed.
                if value.get("source", "") == "wxapp":
                    wapp_wxstate.running = True
                    wapp_wxstate.port = value["port"]
                # The interlocutor starts with its own workspace: publish the
                # shared one, so that both UIs work on the same data.
                notify_wkp_changed()
            else:
                logging.warning(f"HELLO received without a port. Not registered: {value}")

        if key == sppasCommKeys.BYE:
            self.__interlocutor = None
            wapp_wxstate.running = False
            wapp_wxstate.port = None
            logging.info("Interlocutor un-registered.")
            # An interface which leaves while an exit waits for its answer
            # has answered: it is gone, and nothing holds the exit back.
            if wapp_wxstate.exit_pending is True:
                self.__grant_exit()

        if key == sppasCommKeys.EXIT_OK:
            logging.info("The wx interface accepts the exit.")
            self.__grant_exit()

        if key == sppasCommKeys.EXIT_NO:
            logging.info("The wx interface refuses the exit.")
            wapp_wxstate.exit_pending = False

        if key == sppasCommKeys.WKP_CHANGED:
            # The serialized workspace carries its own internal identifier
            # (a uuid, see sppasWorkspace), unrelated to its display name:
            # the sender sends the name alongside, in the same envelope.
            # The name is not used as an identifier -- it is only stored
            # for display, exactly as reported by the interlocutor.
            wapp_wxstate.workspace_name = value["name"]
            wjson = sppasWJSON()
            wjson.parse(value["workspace"])
            wapp_wkps.data = wjson
            logging.info("Workspace received and stored into the shared state.")
            return self.format_message(sppasCommKeys.ACK, "Workspace stored.")

        if key == sppasCommKeys.TRACE:
            if isinstance(value, dict) is True:
                wapp_trace.append(
                    value.get("levelno", 0),
                    value.get("levelname", ""),
                    value.get("message", ""),
                    value.get("source", "wxapp"),
                    swappTraceStore.origin_of(value.get("pathname", ""), value.get("name", "")),
                    value.get("created"))
            return self.format_message(sppasCommKeys.ACK, "Trace stored.")

        return super(sppasWappCommServer, self)._prepare_response(key, value)

    # -----------------------------------------------------------------------

    @staticmethod
    def __grant_exit() -> None:
        """Note that the exit was granted, and end nothing.

        The web application ends by serving its last page -- the one saying
        the session is over -- and a page is served to a browser which asks
        for it. Stopping the server from here would leave the reader in
        front of a page whose server is already gone.

        :return: (None)

        """
        wapp_wxstate.exit_pending = False
        wapp_wxstate.exit_granted = True

    # -----------------------------------------------------------------------

    def push(self, key: int, value) -> None:
        """Push an event to the registered interlocutor, if any.

        Tolerant version of send(): when there is no interlocutor -- the
        other UI is not running -- the event is dropped, with a log only.
        This is the observer the application subscribes to the notifier.

        The sending is done by a thread of its own, and nothing waits for it.
        The notifier is called while an answer is owed -- to the HELLO of the
        interlocutor, or to an HTTP request -- and a sending made here would
        hold that answer until it comes back: the interlocutor waiting for it
        would give up first, and would believe nobody is there.

        :param key: (int) One of the sppasCommKeys constants
        :param value: (any) A JSON-serializable object

        """
        sender = threading.Thread(target=self.__send_and_forget,
                                  args=(key, value), daemon=True)
        sender.start()

    # -----------------------------------------------------------------------

    def __send_and_forget(self, key: int, value) -> None:
        """Send an event to the interlocutor and report to the journal only.

        :param key: (int) One of the sppasCommKeys constants
        :param value: (any) A JSON-serializable object

        """
        try:
            self.send(key, value)
            logging.debug(f"Event {sppasCommKeys.name_of(key)} pushed to the interlocutor.")
        except sppasCommServerError as e:
            logging.info(f"Event {sppasCommKeys.name_of(key)} not pushed: {e}")
            # An interlocutor which does not answer any more is gone: it
            # crashed, or it was killed. Un-register it, so that the state
            # it left behind does not outlive it.
            if wapp_wxstate.running is True:
                wapp_wxstate.running = False
                logging.info("The interface does not answer any more.")
