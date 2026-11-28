"""
:filename: test_deposit_middleware.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test the middleware serving the files an app of swapp produced.

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
import os
import tempfile
import unittest

from whakerpy.httpd.hsignedurl import SignedURL

from sppas.ui.swapp.services.files.files_place import swappFilePlace
from sppas.ui.swapp.swapp_core.swapp_deposit_middleware import swappDepositMiddleware

# ---------------------------------------------------------------------------

# What a server protects the addresses of the deposit with.
SIGNED_URL = {"secret": "a secret for the tests only",
              "ttl": 1800,
              "protect": [{"prefix": "/deposit/", "suffix": ""}],
              "query_keys": {"ts": "ts", "sig": "sig"}}

# ---------------------------------------------------------------------------


class TestDepositMiddleware(unittest.TestCase):
    """A file an app produced is served at a signed address, and nowhere else."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        _json = os.path.join(self.folder.name, "swapp.json")
        with open(_json, "w") as fd:
            json.dump({"WhakerPy": {"blacklist": [], "signed_url": SIGNED_URL,
                                    "pagespath": "html", "pages": {}}}, fd)
        self.passed = list()
        self.middleware = swappDepositMiddleware(self.application, _json)

        place = swappFilePlace()
        name = place.ask_for_a_place()
        place.put(name, "a-phon.TextGrid", b"produced")
        self.address = place.address_of(name, "a-phon.TextGrid")
        self.signer = SignedURL()
        self.signer.configure({"signed_url": SIGNED_URL})

    def tearDown(self):
        self.folder.cleanup()

    # -----------------------------------------------------------------------

    def application(self, environ, start_response):
        """The application the middleware wraps."""
        self.passed.append(environ["PATH_INFO"])
        start_response("200 OK", [])
        return [b"page"]

    def request(self, path: str, query: str = "") -> tuple:
        """Return the status and the content the middleware answers."""
        answered = dict()

        def start_response(status, headers, exc_info=None):
            answered["status"] = status

        content = b"".join(self.middleware({"PATH_INFO": path, "QUERY_STRING": query}, start_response))
        return answered["status"], content

    # -----------------------------------------------------------------------

    def test_a_signed_address_is_served(self):
        """The file is given to whoever holds its signed address."""
        path, query = self.signer.sign(self.address, 1800).split("?", 1)
        self.assertEqual(("200 OK", b"produced"), self.request(path, query))
        self.assertEqual(0, len(self.passed))

    def test_an_address_without_signature_is_not(self):
        """Without its signature, the address is answered as one which names no file."""
        self.assertEqual(("404 Not Found", b""), self.request(self.address))

    def test_a_wrong_signature_is_not(self):
        """With a signature which is not the one of the address, nothing is served either."""
        path, query = self.signer.sign(self.address, 1800).split("?", 1)
        self.assertEqual(("404 Not Found", b""), self.request(path, query.replace("sig=", "sig=0")))

    def test_another_address_is_the_application(self):
        """Any other request is answered by the application it wraps."""
        self.assertEqual(("200 OK", b"page"), self.request("/convert.html"))
        self.assertEqual(["/convert.html"], self.passed)


if __name__ == "__main__":
    unittest.main()
