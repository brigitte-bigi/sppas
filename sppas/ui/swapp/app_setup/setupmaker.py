"""
:filename: sppas.ui.swapp.app_setup.setupmaker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The web-based application "Setup" of SPPAS.

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

from whakerpy.htmlmaker import HTMLTree

from sppas.core.config import sg
from sppas.core.config import lgs
from sppas.core.coreutils import sppasLogFile
from sppas.ui import _

from ..wappbase.wappresponse import swappBaseResponse
from ..nodes.feedback.hstatusnode import HTMLTreeError410

from .setup_model import SetupModel
from .setup_view import SetupView
from .setup_controller import SetupController

# -----------------------------------------------------------------------


MSG_TITLE =  f"SPPAS {sg.__release__} Setup"

# -----------------------------------------------------------------------


class SetupResponseRecipe(swappBaseResponse):
    """The setup.html HTTPD response bakery.

    This application setup allows to install several external programs
    SPPAS is requiring in order to enable some of its features.

    For a good UX when installing:
        1. Queue up the long-running requested installation task
        2. Respond immediately so user can get back to his/her busy life
        3. Handle the long-running task out of process
        4. Allow the user to check the status of the long-running task
        5. Notify the user when the task status is changed or is completed

    HTTP status used by this response recipe baking system:
        - 200 OK.
        - 202 Accepted: The request has been accepted for processing,
          but the processing has not been completed.
        - 205 Reset Content
        - 410 Gone

    The SetupResponseRecipe acts as the web adapter for the Setup MVC components.

    It connects the internal application logic (controller, model, and view)
    with the HTTP serving layer. The controller manages the application state
    and event logic independently of any web framework, while the view defines
    how data and UI components are structured in the HTML tree. The
    SetupResponseRecipe is responsible for translating user events into
    controller actions, updating the view, and returning the appropriate HTTP
    response (status codes and data payloads). In this architecture, the
    controller never depends on WhakerPy or any other HTTP API, which allows
    the MVC core to remain portable across server implementations.

    """

    def __init__(self, name: str = "Setup",
                 tree: HTMLTree | None = None,
                 title: str = MSG_TITLE):
        """Create a SetupResponseRecipe.

        :param name: (str) The identifier name of the recipe to create.
        :param tree: (HTMLTree | None) An existing HTML tree to use.
        :param title: (str) The title of the HTML page, for the <head> element.

        """
        # Fix logging
        log_report = sppasLogFile(pattern="install_ui")
        lgs.file_handler(log_report.get_filename(), with_stream=True)

        # Create the "base" page content
        super(SetupResponseRecipe, self).__init__(name, tree, title)

        # Create and initialize all members
        self.__model = SetupModel()
        self.__view = SetupView(self._htree)
        self.__controller = SetupController(self.__model, self.__view, self.page())

    # -----------------------------------------------------------------------
    # OVERRIDE METHODS FROM Whakerpy -- Create une UI
    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Override. Return the HTML page name."""
        return "setup.html"

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Override. Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        self._data = dict()
        self._status.code = 200

        # Other events are received one-by-one
        if "event_bake" in events:

            # --- Action event to proceed to the installation ---
            if events["event_bake"] == "reset":
                self.__controller.reset()

            # --- Progress event to complete ---
            elif events["event_bake"] == "complete":
                self.__process_complete_event()

            # --- Action events to got out ---
            elif events["event_bake"] == "close":
                self._status.code = 410

            else:
                logging.error("Unknown event_bake={:s}".format(events["event_bake"]))
                self._status.code = 205  # Reset Content

        # Received events from a request manager post which is waiting for
        # the server response, filled in self._data.
        elif "event_name" in events:

            # --- Action events to browse fields ---
            if events["event_name"] == "prev_fieldset":
                field = events.get("event_value", "")
                self.__process_prev_fieldset_event(field)

            elif events["event_name"] == "next_fieldset":
                field = events.get("event_value", "")
                self.__process_next_fieldset_event(field)

            # --- Progress event to update the page ---
            elif events["event_name"] == "update":
                self.__process_update_event()

            # --- Unknown event_name ---
            else:
                self._data = {"error": f"Internal Server Error: Unknown event name {events['event_name']}"}
                self._status.code = 401
                logging.error(f"Internal Server Error: Unknown event name {events['event_name']}")

            return False

        elif "check_name" in events:

            # Other possible events (checkboxes)
            event_value = events["check_name"]

            # --- Feature events to choose what to install ---
            # The event is some data posted via requests.js
            if event_value.startswith("feature_"):
                feature_name = event_value.split("_")[1]
                checkbox_to_change = self.__controller.handle_feature_event(feature_name)
                if checkbox_to_change is not None:
                    self._data = checkbox_to_change
                # ignore else: event not handled
                self.status.code = 200

            else:
                # Communicate the event to the controller
                self._status.code = self.__controller.handle_feature_event(event_value)

            return False

        elif len(events) > 0:
            self._data = {"error": f"Internal Server Error: Unknown event name {events}"}
            self._status.code = 401
            logging.error(f"Internal Server Error: Unknown event name {events}")

        return True

    # -----------------------------------------------------------------------

    def __process_update_event(self):
        """Process the given event coming from the POST of install.

        """
        logging.debug(" ******* Setup update event ******* ")
        self._data["percent"], self._data["header"], self._data["text"] = (
            self.__controller.get_progress_values())

        self._status.code = 202
        if self._data["percent"] >= 100:
            self._status.code = 200

    # -----------------------------------------------------------------------

    def __process_complete_event(self):
        """Process the given event coming from the POST of install.

        """
        # The JS of the page informed the installation is completed,
        logging.debug(" ******* Setup complete event ******* ")
        _success = self.__controller.handle_complete_event()
        if _success is True:
            self.__update_data("install_field")
            self._status.code = 200
            logging.info("Installation completed.")
        else:
            logging.error("Installation is not running but current page is invalid.")
            self._data = {"error": "Internal server error: Installation is completed but current page is invalid."}
            self._status.code = 401

    # -----------------------------------------------------------------------

    def __process_prev_fieldset_event(self, event_value: str):
        """Process prev action.

        :param event_value: (str) The current page index

        """
        try:
            _idx = int(event_value)
            _prev_fieldset_id = self.__controller.get_fieldset_id(_idx)
            _success = self.__controller.handle_prev_fieldset(_idx)
            if _success is True:
                self.__update_data(_prev_fieldset_id)
                self._status.code = 200
            else:
                self._data = {"info": "It seems the browser re-asked the same page twice!"}
                self._status.code = 401

        except ValueError:
            self._data = {"error": "Internal Server Error: Invalid fieldset index. Can't access the previous page."}
            self._status.code = 401

    # -----------------------------------------------------------------------

    def __process_next_fieldset_event(self, event_value: str):
        """Process a browse event: next of prev action.

        :param event_value: (str) The current page index

        """
        try:
            _idx = int(event_value)
            _prev_fieldset_id = self.__controller.get_fieldset_id(_idx)
            _success = self.__controller.handle_next_fieldset(_idx)
            if _success is True:
                if self.__controller.get_fieldset_id(_idx) == "install_field":
                    # HTTP 202 - Accepted: The installation started.
                    self._status.code = 202
                else:
                    self._status.code = 200
                self.__update_data(_prev_fieldset_id)
            else:
                self._data = {"info": "It seems the browser re-asked the same page twice!"}
                self._status.code = 401

        except Exception as e:
            self._data = {"error": str(e)}
            self._status.code = 401

    # -----------------------------------------------------------------------
    # Baking the page
    # -----------------------------------------------------------------------

    def __update_data(self,
                      prev_fieldset_id: str):
        """Update the data depending on the actual fieldset.

        :param prev_fieldset_id: (str) ID of the fieldset for which the content has
            to be replaced in the page.

        """
        # Update the header content for the breadcrumb
        self._data["header-content"] = self._htree.body_header.serialize()

        # Update the fieldset
        _current_fieldset_id = self.__controller.get_current_fieldset_id()
        _node = self._htree.body_main.get_child(_current_fieldset_id)
        if _node is not None:
            self._data[prev_fieldset_id] = _node.serialize()
        else:
            logging.error(f"The fieldset ID '{_current_fieldset_id}' is not in the tree.")

        # Re-create the action buttons to enable/disable or change its buttons,
        # and to associate the right fieldset index.
        actions = self._htree.body_main.get_child("actions_section")
        actions_id = None if actions is None else actions.identifier
        self._data[actions_id] = self._htree.body_main.get_child(actions_id).serialize()

    # -----------------------------------------------------------------------

    def _bake(self):
        """Override. Create the dynamic page content in HTML.

        It replaces the current HTMLTree if status is 410 or update the
        content of the current HTMLTree.

        """
        # Define this page content: a form with a header, fieldsets and actions.
        self.comment("Body content")
        self.__view.update_accessibility()

        if self._status.code == 410:
            # The 410 is "Gone" response sent when the requested content has been
            # permanently deleted from server, with no forwarding address.
            self._htree = HTMLTreeError410()

        elif self._status.code in (200, 205):
            self.__controller.update_tree_content(actions=True, install=False)

        elif self._status.code == 202:
            # Installation started
            self.__controller.update_tree_content(actions=False, install=True)

        else:
            msg = f"Unexpected status '{self._status.code}' while baking the page content."
            logging.error(msg)
            p = self._htree.element("p")
            p.set_value(msg)
