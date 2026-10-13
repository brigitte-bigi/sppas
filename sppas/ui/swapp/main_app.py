"""
:filename: sppas.ui.swapp.main_app.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The main class for any of the SPPAS Web-based Applications with a local server.

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
import threading

from whakerpy.httpd import HTTPDHandler
from whakerpy.httpd import BaseHTTPDServer
from whakerpy.httpd import HTTPDHandlerUtils

from sppas.core.config import cfg
from sppas.core.coreutils import sppasKeyError
from sppas.ui.agnostic import sppasCommKeys
from sppas.ui.agnostic import sppasCommServerError
from sppas.ui.swapp.swapp_core.swappsg import swapp_serverstate
from sppas.ui.swapp.swapp_core.swappsg import swapp_settings
from sppas.ui.swapp.swapp_core.swappsg import swapp_notify
from sppas.ui.swapp.swapp_core.swappsg import swapp_trace
from sppas.ui.swapp.swapp_core.swappsg import swapp_wxstate
from .main_trace_handler import swappTraceHandler
from .main_comm import swappCommServer
from .nodes.feedback.hstatus_node import swappHTMLTreeError403
from .swapp_core.swapp_dispatcher import swappDispatcher

from .swapp_core.swapps import *

# ---------------------------------------------------------------------------


class sppasWebApp:
    """Create and run any of the SPPAS web-based applications.

    """

    # Explicitly set the name of the default app
    DEFAULT_APP_NAME = "Dashboard"

    # Find the default application in the list
    DEFAULT_APP = None
    for app in WEB_APPLICATIONS:
        if app.name == DEFAULT_APP_NAME:
            DEFAULT_APP = app

    if DEFAULT_APP is None:
        raise ValueError(f"The default application with name '{DEFAULT_APP_NAME}' "
                         "was not found in the declared list of Web Applications.")

    # ---------------------------------------------------------------------------

    @staticmethod
    def get_web_app_by_name(name: str) -> swappWebApplicationInfo:
        """Retrieve a web application by its name.

        :param name: Name of the application to retrieve.
        :return: The matching swappWebApplicationInfo instance.
        :raises: KeyError: If no application with the given name exists.

        """
        for app in WEB_APPLICATIONS:
            if app.name == name:
                return app
        raise sppasKeyError("Web Applications list", name)

    # ---------------------------------------------------------------------------

    class swappHandler(HTTPDHandler):
        """A custom HTTPD request handler for SPPAS swapp.

        """

        def _response(self, content, status: int, mime_type: str = None) -> None:
            """Override. Answer the error pages of SPPAS.

            The 403 of a static file is answered by the framework, before any
            response of swapp is asked for: the content is substituted here,
            the only place the status and the content are both in hand.

            :param content: (bytes|iterator) The response content
            :param status: (int) The HTTPD status code of the response
            :param mime_type: (str) The mime type of the file response

            """
            if status == 403:
                content = swappHTMLTreeError403().serialize().encode("utf-8")
                mime_type = "text/html"

            super()._response(content, status, mime_type)

    # ---------------------------------------------------------------------------

    class swappServer(BaseHTTPDServer):
        """A custom HTTPD server for SPPAS swapp.

        """

        def create_pages(self, app_name: str = 'Dashboard'):
            """Override. Add bakeries for dynamic HTML pages of this app.

            :param app_name: (str) One of the WEB_APPLICATIONS app name

            """
            logging.debug(f"HTTPD server initialization for {app_name}...")

            # The dispatcher of the apps and the pages, shared with the WSGI service.
            self.__dispatcher = swappDispatcher(app_name)

            # Instantiate the responses the server starts with and enter the app
            # by its default page.
            self._pages.update(self.__dispatcher.create_pages())
            self._default = self.__dispatcher.get_default_page()

        # -----------------------------------------------------------------------
        # OVERRIDE
        # -----------------------------------------------------------------------

        def page_bakery(self, page_name: str, headers: dict, events: dict, has_to_return_data: bool = False) -> tuple:
            """Return the page content and response status.

            This method should be invoked after a POST request in order to
            take the events into account when baking the HTML page content.

            :param page_name: (str) Requested page name
            :param headers: (dict) The headers ot the http request
            :param events: (dict) key=event name, value=event value
            :param has_to_return_data: (bool) False by default - Boolean to know if the server return data or html page
            :return: tuple(bytes, HTTPDStatus)

            """
            logging.debug(" <<<<<<<<<<<<<<<<<<<<<<< sppasWebApp.page_bakery() >>>>>>>>>>>>>>>>>>>>>>>>>> ")
            logging.debug("  - page_name: " + page_name)
            logging.debug("  - events: " + str(events))

            # Redirections
            # ------------
            # None

            # An unknown response for yet
            # ---------------------------
            # The dispatcher asks the known bakeries which one is able to bake
            # the response, then the single provider of the generic pages.
            if page_name not in self._pages:
                self._pages[page_name] = self.__dispatcher.bake_response(page_name)

            # Process received events and bake the given page.
            return HTTPDHandlerUtils.bakery(self._pages, page_name, headers, events, has_to_return_data)

    # -----------------------------------------------------------------------

    def __init__(self, arguments: dict | None = None):
        """HTTP Server initialization.

        Create the application for the GUI of SPPAS based on httpd.
        The given arguments can contain the name of a specific application.
        By default, the Dashboard application is used.

        :param arguments: (dict) Optional arguments passed to the server.

        """
        # The applications are served by the local server.
        swapp_serverstate.local = True

        # Collect the python logging into the shared trace store: the swapp
        # server is the collector of the traces of all the SPPAS components.
        logging.getLogger().addHandler(swappTraceHandler(swapp_trace))

        self.__location = "localhost"
        self.__port = self.__port_value()
        self.__server = None
        server_address = (self.__location, self.__port)

        # Create an HTTPD server
        self.__server = sppasWebApp.swappServer(server_address, sppasWebApp.swappHandler)

        if arguments is not None and len(arguments) > 0:
            _app = None
            # Check if any known application was explicitly requested.
            # The search follows the order defined in WEB_APPLICATIONS.
            _names = list()
            for web_app in WEB_APPLICATIONS:
                _names.append(web_app.name)
                # If the argument matches the application name, use it.
                if arguments.get(web_app.name, False) is True:
                    _app = web_app
                    break
            if _app is None:
                raise sppasKeyError(_names, arguments.keys())
        else:
            # Define the application to launch. Use the default one initially.
            _app = sppasWebApp.DEFAULT_APP

        # Launch the selected application: add bakeries for dynamic HTML pages.
        self.__server.create_pages(_app.name)

        # Create a socket to communicate with the apps
        self.__socket = swappCommServer(swapp_settings.shost, swapp_settings.sport)

        # Any application event -- e.g. the shared workspace changed -- is
        # pushed to the interlocutor registered on this socket, if any.
        swapp_notify.subscribe(self.__socket.push)

    # -----------------------------------------------------------------------

    def __port_value(self):
        """Return a port value for this instance."""
        pport = swapp_settings.hport + 1
        if pport > 99:
            pport = 80
        swapp_settings.hport = pport
        return pport + (pport*100)

    # -----------------------------------------------------------------------

    def client_url(self):
        """Return the client URL of this server.

        The address names what the reader chose to be shown with: the managers
        of the client read these parameters when the page is loaded, and carry
        them to the next page. A choice that was not made is not named, and
        the pages are shown the way SPPAS is by default.

        """
        url = "http://{:s}:{:d}/".format(self.__location, self.__port)

        parameters = list()
        if len(swapp_settings.accessibility_theme) > 0:
            parameters.append("wexa_theme=" + swapp_settings.accessibility_theme)
        if len(swapp_settings.accessibility_color) > 0:
            parameters.append("wexa_color=" + swapp_settings.accessibility_color)
        if len(swapp_settings.accessibility_contrast) > 0:
            parameters.append("wexa_contrast=" + swapp_settings.accessibility_contrast)

        if len(parameters) == 0:
            return url

        return url + "?" + "&".join(parameters)

    # -----------------------------------------------------------------------

    def run(self):
        """Run the application with a main loop.

        :return: (int) Exit status (0=normal)

        """
        try:
            # Start the socket to communicate with the apps
            socket_thread = threading.Thread(target=self.__socket.start, daemon=True)
            socket_thread.start()
            # Start the main loop of the HTTP server
            self.__server.serve_forever()
            # Notice that the sppasHTTPDHandler can shut down the server --
            # allowed because it's a local application, not an internet service.
        except KeyboardInterrupt:
            # Stop the server
            self.__server.shutdown()
        finally:
            # The wx interface, if running, does not survive the web server
            # it depends on either: announce this shutdown too, while the
            # socket can still reach it -- the same BYE it sends when it
            # is the one closing.
            if swapp_wxstate.running is True:
                # Sent by the socket itself and not by the notifier: what the
                # notifier pushes is sent by a thread nobody waits for, and
                # this process is about to end. This one has to be gone
                # before it does.
                try:
                    self.__socket.send(sppasCommKeys.BYE, None)
                except sppasCommServerError as e:
                    logging.info(f"The shutdown was not announced: {e}")

            # The HTTP server is no longer serving -- whatever the exit path
            # (KeyboardInterrupt or shutdown by the handler on the 410 event):
            # the communication socket must not survive it.
            self.__socket.shutdown()

        # Save the collected traces into the log file, like the former wx
        # log window did when the application exited.
        saved = swapp_trace.save()
        logging.info(f"Traces saved into: {saved}")

        # Save current configuration
        logging.debug("Save config files.")
        cfg.save()
        swapp_settings.save()

        # Return exit status 0 = normal.
        return 0
