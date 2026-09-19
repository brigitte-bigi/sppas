"""
:filename: test_trace_store.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test the socket communication of swapp with the other UI.

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

import unittest

from sppas.ui.agnostic import sppasCommKeys
from sppas.ui.agnostic import COMM_PROTOCOL_VERSION

from sppas.ui.swapp.main_comm import sppasWappCommServer
from sppas.ui.swapp.swappcore.swappsg import swapp_wxstate
from sppas.ui.swapp.swappcore.swappsg import wx_is_running

# ---------------------------------------------------------------------------


class TestInterlocutorGone(unittest.TestCase):
    """What happens to the state when the other UI does not answer."""

    def setUp(self):
        # A port nothing is listening to: a push to it fails, exactly as it
        # does when the wx interface crashed.
        self.server = sppasWappCommServer("127.0.0.1", 61999)
        self.hello = {"source": "wxapp", "version": COMM_PROTOCOL_VERSION,
                      "port": 61998}

    def tearDown(self):
        swapp_wxstate.running = False
        swapp_wxstate.port = None

    # -----------------------------------------------------------------------

    def test_hello_registers(self):
        """The handshake registers the interlocutor and the shared state."""
        self.server._prepare_response(sppasCommKeys.HELLO, self.hello)
        self.assertEqual(self.hello, self.server.get_interlocutor())
        self.assertTrue(swapp_wxstate.running)

    def test_bye_unregisters(self):
        """The announced shutdown un-registers it."""
        self.server._prepare_response(sppasCommKeys.HELLO, self.hello)
        self.server._prepare_response(sppasCommKeys.BYE, None)
        self.assertIsNone(self.server.get_interlocutor())
        self.assertFalse(swapp_wxstate.running)

    def test_push_to_a_gone_interlocutor(self):
        """An interlocutor which does not answer is un-registered too.

        This is the crash of the wx interface: no BYE is ever sent, and the
        state it left behind must not outlive it.

        """
        self.server._prepare_response(sppasCommKeys.HELLO, self.hello)
        self.assertTrue(swapp_wxstate.running)

        # Nothing is listening on the announced port: the push fails
        self.server.push(sppasCommKeys.SHOW_PAGE, "page_files")

        self.assertFalse(swapp_wxstate.running)
        # the announced address stays: a silence is not a reason to forget
        # where to ask again
        self.assertEqual(self.hello["port"], swapp_wxstate.port)

    def test_ping_is_a_sign_of_life(self):
        """A ping of the wx interface keeps the shared state alive."""
        swapp_wxstate.running = False
        self.assertFalse(swapp_wxstate.running)

        self.server._prepare_response(sppasCommKeys.PING, {"source": "wxapp"})
        self.assertTrue(swapp_wxstate.running)

    def test_ping_of_another_source(self):
        """A ping of anything else says nothing about the wx interface."""
        swapp_wxstate.running = False
        self.server._prepare_response(sppasCommKeys.PING, {"source": "test.html"})
        self.assertFalse(swapp_wxstate.running)

    def test_asked_directly_without_a_port(self):
        """Nothing was ever announced: there is nobody to ask."""
        swapp_wxstate.port = None
        self.assertFalse(wx_is_running())

    def test_asked_directly_and_silent(self):
        """An interface which does not answer is gone, right now.

        This is what a user in front of the launch button needs: the
        answer of the interface itself, not the fading of its last sign.

        """
        self.server._prepare_response(sppasCommKeys.HELLO, self.hello)
        self.assertTrue(swapp_wxstate.running)
        self.assertEqual(self.hello["port"], swapp_wxstate.port)

        # Nothing is listening on the announced port
        self.assertFalse(wx_is_running())
        self.assertFalse(swapp_wxstate.running)
        self.assertEqual(self.hello["port"], swapp_wxstate.port)

    def test_push_without_interlocutor(self):
        """Without any interlocutor, a push is dropped and nothing raises."""
        self.server.push(sppasCommKeys.SHOW_PAGE, "page_files")
        self.assertIsNone(self.server.get_interlocutor())
