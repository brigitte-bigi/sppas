"""
:filename: sppas.ui.swapp.main_wsgi.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The main class for any of the SPPAS Web-based Applications with Uwsgi service.

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

The WSGI server is searching for an "application(environ, start_response)"
function. It is invoked every time a request is received by either POST,
or GET, or any other method.

Test locally the site with:
> uwsgi --http :9090 --wsgi-file wsgi.py

"""

# ---------------------------------------------------------------------------
# Import of python standard libraries
# ---------------------------------------------------------------------------


from __future__ import annotations
import os
import sys
import logging

from whakerpy.httpd import BaseResponseRecipe
from whakerpy.webapp import WebSiteData

# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------


HERE = os.path.dirname(os.path.abspath(__file__))
SPPAS = os.path.join(HERE, "SPPAS5")
JSON = os.path.join(HERE, "swapp.json")

# SPPAS 5.0 requires 'SPPAS' environment variable to find resources and to fix wkps/logs/trash.
os.environ['SPPAS'] = SPPAS

# Add directories into the PYTHONPATH allowing Python to find our own packages.
sys.path.append(SPPAS)
sys.path.append(HERE)

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------


# Define the log level for output messages
# LOG_LEVEL = 1     # Debug level
LOG_LEVEL = 15   # Info level
# Name of the file for logger messages -- for local use. Gandi doesn't care!
LOG_FILENAME = "wsgi.log"
if LOG_LEVEL < 10:
    LOG_FILENAME = "wsgi_debug.log"

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Save logs into a file: create file logger
file_log = logging.FileHandler(HERE + "/" + LOG_FILENAME, mode='a', encoding="utf-8", delay=False)
file_log.setFormatter(formatter)
file_log.setLevel(LOG_LEVEL)

# Add this file logger to the logging system
logging.getLogger().addHandler(file_log)
logging.getLogger().setLevel(LOG_LEVEL)

# ----------------------------------------------------------------------------
# Environment variables
# ----------------------------------------------------------------------------


# This website is in English by default.
LANG = "en_US"
# Definition of lang, required by wsgi service
os.environ['LC_ALL'] = "en_US.UTF-8"
os.environ['LC_LANG'] = "en_EN.UTF-8"

# Define the filepath of this wsgi.py file. Can be used to get the path of
# the project directory with: os.getenv("INSTANCE_ROOT").
os.environ["INSTANCE_ROOT"] = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------
# Bakery system for WhakerPy
# ----------------------------------------------------------------------------

class SPPASWebData(WebSiteData):
    """Parse the swapp.json file, store data and create the bakery system.

    """

    def __init__(self, json_filename: str | None = None) -> None:
        """Create a SPPASWebData instance.

        :param json_filename: (str) The JSON configuration file of swapp

        """
        super(SPPASWebData, self).__init__(json_filename)

        # The dispatcher of the apps and the pages, shared with the local server.
        self.__dispatcher = swappDispatcher()

    # -----------------------------------------------------------------------

    def bake_response(self, page_name: str, default: str = "") -> BaseResponseRecipe:
        """Return the bakery system to create the requested page dynamically.

        :param page_name: (str) Name of the page to bake.
        :param default: (str) Default value for the page name if the page does not exist.
        :return: (BaseResponseRecipe)

        """
        logging.info(f"Requested page name: {page_name}")

        return self.__dispatcher.bake_response(page_name, default)


# ----------------------------------------------------------------------------
# Error pages of SPPAS for the wsgi service
# ----------------------------------------------------------------------------


class SPPASErrorMiddleware:
    """Substitute the error pages of SPPAS for the ones of the framework.

    The 403 of a static file is answered before any response of swapp is
    asked for: the status and the content are returned together, and the
    local server substitutes its own page where it writes the response.
    The wsgi service has no such place -- what the application does with
    the request is private to it -- so the status is read as it goes out,
    and the content is substituted there.

    """

    def __init__(self, application):
        """Create a SPPASErrorMiddleware instance.

        :param application: (callable) The wsgi application to wrap

        """
        self.__application = application

    # -----------------------------------------------------------------------

    def __call__(self, environ, start_response):
        """Answer the request, with the error pages of SPPAS.

        :param environ: (dict) WSGI environment dictionary with request data
        :param start_response: (callable) Function to start the HTTP response
        :return: (list) Response content to send back to the client

        """
        substituted = dict()

        def ignore_write(data):
            """Discard what the application writes for a substituted page."""
            pass

        def catch_response(status, headers, exc_info=None):
            """Start the response, with the page of SPPAS for a known status.

            The third argument is given to the server only when the
            application gives one: a server is not required to accept it.

            """
            code = int(status.split()[0])
            if code != 403:
                if exc_info is None:
                    return start_response(status, headers)
                return start_response(status, headers, exc_info)

            body = swappHTMLTreeError403().serialize().encode("utf-8")
            substituted["body"] = body

            kept = list()
            for name, value in headers:
                if name.lower() not in ("content-length", "content-type"):
                    kept.append((name, value))
            kept.append(("Content-Type", "text/html; charset=utf-8"))
            kept.append(("Content-Length", str(len(body))))

            if exc_info is None:
                start_response(status, kept)
            else:
                start_response(status, kept, exc_info)

            return ignore_write

        content = self.__application(environ, catch_response)

        if "body" not in substituted:
            return content

        # The content of the framework is not served: the application is
        # given the chance to release what it had opened for it.
        if hasattr(content, "close") is True:
            content.close()

        return [substituted["body"]]


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------


try:
    # Path to the main JSON configuration, required by WhakerPy.
    # -----------------------------------------------------
    if os.path.exists(JSON) is False:
        raise Exception(f"The expected JSON configuration file {JSON} wasn't found.")

    # Turn the UI made by SPPAS in English language
    # ---------------------------------------------
    from sppas.core.config import set_language
    set_language(LANG[:2])

    # Get the dispatcher of the apps and the pages
    # --------------------------------------------
    # The registries it reads import every app of swapp: the language and the
    # log level are fixed before, the messages of their interface are
    # translated at import time and the apps in development are declared on
    # the log level.
    from sppas.ui.swapp.swapp_core.swapp_dispatcher import swappDispatcher
    from sppas.ui.swapp.nodes.feedback.hstatus_node import swappHTMLTreeError403

    # Launch the application, as mandatory by UWSGI service
    # -----------------------------------------------------
    from whakerpy import WSGIApplication

    application = SPPASErrorMiddleware(WSGIApplication(
        default_path="",
        default_filename="dashboard.html",
        web_page_maker=SPPASWebData,
        default_web_json=JSON
    ))

except Exception as e:

    import traceback

    logging.error(str(e))
    logging.error(traceback.format_exc())
    msg_error = traceback.format_exc().replace("\n", "<br>")

    def _load_500_html(lang='en'):
        """Load the 500 HTML file with language fallback."""
        lang = (lang or 'en').split(',')[0].split('-')[0].strip().lower() or 'en'

        candidates = [
            os.path.join(HERE, 'statics', 'errors', f'500_{lang}.html'),
            os.path.join(HERE, 'statics', 'errors', '500_en.html'),
        ]

        for filename in candidates:
            if os.path.isfile(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as fd:
                        return fd.read()
                except OSError:
                    pass

        return """<!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <title>Error 500</title>
    </head>
    <body>
    <h1>500 Internal Server Error</h1>
    <p>{ERROR}</p>
    </body>
    </html>
    """

    def application(environ, start_response):
        html_500 = _load_500_html(LANG[:2]).replace('{ERROR}', msg_error)
        body = html_500.encode('utf-8')

        start_response(
            '500 Internal Server Error',
            [
                ('Content-Type', 'text/html; charset=utf-8'),
                ('Content-Length', str(len(body)))
            ]
        )

        return [body]

