"""
:filename: sppas.ui.swapp.swapp_core.swapp_deposit_middleware.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The WSGI middleware serving the files an app of swapp produced.

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

from whakerpy.httpd.hsignedurl import SignedURL
from whakerpy.webapp import WebSiteData

from ..services.deposit.deposit_address import swappFileAddress
from ..services.files import swappResultDelivery

# ---------------------------------------------------------------------------


class swappDepositMiddleware:
    """Serve the files an app produced, at the addresses of the deposit.

    It wraps the WSGI application of a server of swapp: a request for an
    address of the deposit is answered here, before the application, and
    every other request is the application's. What signs the address is
    verified as WhakerPy verifies it for a page, with "signed_url" of the
    JSON of the server: an address whose signature is missing, wrong or out
    of date is answered as one which names no file -- nothing at all.

    """

    def __init__(self, application, json_filename: str):
        """Create a swappDepositMiddleware instance.

        :param application: (callable) The WSGI application to wrap
        :param json_filename: (str) The JSON configuration file of the server

        """
        self.__application = application
        self.__signed_url = SignedURL()
        self.__signed_cfg = self.__signed_url.configure({"signed_url": WebSiteData(json_filename).signed_url})

    # -----------------------------------------------------------------------

    def __call__(self, environ, start_response):
        """Answer a request for an address of the deposit, or pass it on.

        :param environ: (dict) WSGI environment dictionary with request data
        :param start_response: (callable) Function to start the HTTP response
        :return: (list) Response content to send back to the client

        """
        _path = environ.get("PATH_INFO", "")
        if _path.startswith(swappFileAddress.PREFIX) is False:
            return self.__application(environ, start_response)

        _bytes = b""
        if self.__is_signed(_path, environ.get("QUERY_STRING", "")) is True:
            _bytes = swappResultDelivery().serve(_path)

        if len(_bytes) == 0:
            start_response("404 Not Found",
                           [("Content-Type", "text/plain; charset=utf-8"),
                            ("Content-Length", "0")])
            return [b""]

        start_response("200 OK",
                       [("Content-Type", "application/octet-stream"),
                        ("Content-Length", str(len(_bytes)))])
        return [_bytes]

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __is_signed(self, path: str, query_string: str) -> bool:
        """Return True if what signs the address of a file lets it be served.

        An address no protection names needs no signature.

        :param path: (str) The address of the file
        :param query_string: (str) What follows the address
        :return: (bool)

        """
        _ttl = self.__signed_cfg.get("ttl", None)
        if _ttl is None:
            return True
        if self.__signed_url.match_protect(path, self.__signed_cfg.get("protect", [])) is False:
            return True

        return self.__signed_url.verify(path, query_string, _ttl)
