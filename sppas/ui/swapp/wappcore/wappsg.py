"""
:filename: sppas.ui.swapp.wappsg.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary: This is the SPPAS Web-based application global' variables.

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

import logging

from sppas.src.wkps.appwkpm import sppasWkpsManager
from sppas.src.wkps.wio import sppasWJSON

from sppas.core.config import sppasHeartbeat

from sppas.ui.agnostic import sppasCommKeys
from sppas.ui.agnostic import sppasCommClient
from sppas.ui.agnostic import sppasCommNotifier
from sppas.ui.agnostic import sppasCommServerError
from sppas.ui.swapp.main_settings import sppasWebAppSettings
from sppas.ui.swapp.main_trace_store import swappTraceStore

# -----------------------------------------------------------------------


# Instantiate the application settings
wapp_settings = sppasWebAppSettings()

# Instantiate the workspaces manager
wapp_wkps = sppasWkpsManager()

# Instantiate the application events notifier
wapp_notify = sppasCommNotifier()

# Instantiate the shared store of the trace/info records: the swapp server
# is the collector of the traces of all the SPPAS components.
wapp_trace = swappTraceStore()

# -----------------------------------------------------------------------


class sppasWxAppState:
    """Shared state reported by the wx interface interlocutor.

    The state is updated by the communication server, from the messages of
    the wxapp interlocutor: "running" says whether the wx interface gave a
    recent sign of life, "workspace_name" comes from its WKP_CHANGED
    messages, the display name of its current workspace at the time it was
    sent.

    "running" is not a flag somebody has to clear: it is the freshness of
    the last sign of life. The wx interface announces itself periodically,
    and a crash or a kill stops the signs -- which is the only report a
    dead interface is able to make. Assigning True is a sign of life,
    assigning False is the announced end.

    The name is not an identifier: a workspace is renamed by moving its
    file, and swapp does not track the same workspace across a rename by
    matching names -- it only displays the last one wx reported.

    """

    # The wx interface signs every 30 seconds: three missed signs and it is
    # considered gone.
    HEARTBEAT_MAX_AGE = 90.

    def __init__(self):
        self.__heartbeat = sppasHeartbeat(sppasWxAppState.HEARTBEAT_MAX_AGE)
        self.workspace_name = ""
        # The port the interface is listening to, announced in its HELLO:
        # it is what allows to ask it directly whether it is still there.
        self.port = None
        # An exit was asked for, and this interface has not answered yet.
        # While it is waiting, the web interface does nothing else: an exit
        # of SPPAS is an exit of both of them, or of none.
        self.exit_pending = False
        # The interface granted the exit. The web application is not ended
        # here: it ends by serving its last page, the one saying the session
        # is over, and the page is asked for by the reader's browser.
        self.exit_granted = False

    # -----------------------------------------------------------------------

    def get_running(self) -> bool:
        """Return True if the wx interface gave a recent sign of life."""
        return self.__heartbeat.alive()

    # -----------------------------------------------------------------------

    def set_running(self, value: bool) -> None:
        """Store a sign of life, or the announced end.

        :param value: (bool) True is a sign of life, False the end

        """
        if bool(value) is True:
            self.__heartbeat.ping()
        else:
            self.__heartbeat.forget()

    running = property(get_running, set_running)


# Instantiate the shared state of the wx interface
wapp_wxstate = sppasWxAppState()

# -----------------------------------------------------------------------


def notify_wkp_changed() -> None:
    """Notify the observers that the shared workspace changed.

    The workspace of the manager is serialized and published with the
    WKP_CHANGED event key. Without any observer -- no local server, or
    no other UI -- nothing happens.

    """
    wjson = sppasWJSON()
    wjson.set(wapp_wkps.data)
    wapp_notify.notify(sppasCommKeys.WKP_CHANGED, wjson.serialize())

# -----------------------------------------------------------------------


def wx_is_running() -> bool:
    """Return True if the wx interface answers right now.

    The periodic sign of life is what keeps the shared state fresh, but
    waiting for it to fade is not an answer for a user in front of a
    button: the interface is asked directly, and its silence is immediate.
    Both UIs run on the same machine, so the question costs nothing.

    :return: (bool) True if the wx interface answered

    """
    if wapp_wxstate.port is None:
        return False

    client = sppasCommClient(wapp_settings.shost, wapp_wxstate.port)
    try:
        client.request(client.format_request(sppasCommKeys.PING,
                                             {"source": "swapp"}))
    except sppasCommServerError:
        # The address stays: it is the last one the interface announced,
        # and a silence is not a reason to forget where to ask again.
        wapp_wxstate.running = False
        return False

    wapp_wxstate.running = True
    return True

# -----------------------------------------------------------------------


def request_wx_exit() -> int:
    """Ask the wx interface whether it accepts to close.

    The interface answers its verdict when it has one right away -- nothing
    opened, nothing modified -- and an acknowledgement when it has to ask
    its own reader: the verdict then comes later, in a message of its own.
    A silence is an interface which is not there any more, and an interface
    which is not there does not hold an exit back.

    :return: (int) EXIT_OK, EXIT_NO, or ACK when the verdict comes later

    """
    if wapp_wxstate.port is None:
        return sppasCommKeys.EXIT_OK

    client = sppasCommClient(wapp_settings.shost, wapp_wxstate.port)
    try:
        answer = client.request(
            client.format_request(sppasCommKeys.EXIT_REQUEST, {"source": "swapp"}))
        key, value = sppasCommClient.parse_message(answer)
    except Exception as e:
        logging.info(f"The wx interface was not asked about the exit: {e}")
        wapp_wxstate.running = False
        return sppasCommKeys.EXIT_OK

    if key in (sppasCommKeys.EXIT_OK, sppasCommKeys.EXIT_NO):
        return key

    return sppasCommKeys.ACK

# -----------------------------------------------------------------------


def notify_show_page(page_name: str) -> None:
    """Ask the other UI to show one of its pages.

    The page is named with the vocabulary of the wx interface -- the names
    of its book: "page_files", "page_annotate", "page_analyze",
    "page_editor", "page_convert", "page_plugins". Without any observer --
    no local server, or no other UI -- nothing happens: it is up to the
    caller to launch the interface instead.

    :param page_name: (str) The name of the page to show

    """
    wapp_notify.notify(sppasCommKeys.SHOW_PAGE, page_name)
