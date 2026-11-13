"""
:filename: sppas.ui.swapp.app_setup.setup_controller.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Setup Controller of the MVC paradigm: manage the view ans the model.

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

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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

from sppas.ui.swapp.swapp_core.swapp_exc import swappHTMLIncompleteFieldset

from .fieldsets import swappSetupFieldsets

# ---------------------------------------------------------------------------

# What has to be accepted in a fieldset before the next one is shown, and
# what is said when it is not.
REQUIRED = {"home_field": ("check_ref", "check_prod"), "license_field": ("check_license",)}
MSG_REQUIRED = {"home_field": "Accept citation", "license_field": "Accept License"}

# The name of the checkbox of a feature is made of its name, between these.
FEATURE_PREFIX = "feature_"
INPUT_SUFFIX = "_input"

# The types of features, in the order of their fieldsets.
FEATURE_TYPES = ("deps", "lang", "annot", "spin")

# ---------------------------------------------------------------------------


class swappSetupController:
    """Controller of the Setup: where the person is, and what she chose.

    It holds the index of the fieldset which is shown. What is accepted and
    what is to be installed are held by the model, and by the model only: a
    fieldset is written from it each time it is shown.

    """

    def __init__(self, model, view, page_name: str = "setup.html"):
        """Initialize the controller with a model and a view.

        :param model: (swappSetupModel) The model managing the applications.
        :param view: (swappSetupView) The view managing the HTML structure.
        :param page_name: (str) Name of the HTML page this controller is managing

        """
        self.__model = model
        self.__view = view
        self.__current = 0
        self.__fieldsets = swappSetupFieldsets(self.__model, page_name)

        # Assign the fieldsets to the view
        self.__view.set_fieldsets(self.__fieldsets)

    # -----------------------------------------------------------------------

    def reset(self, page_name: str = "setup.html"):
        """Reset the model, the view and members.

        :param page_name: (str) Name of the HTML page this controller is managing

        """
        # Reset the model -- the installer
        self.__model.reset()

        # The wizard pages are fieldset tags
        self.__current = 0
        self.__fieldsets = swappSetupFieldsets(self.__model, page_name)

        # Assign the fieldsets to the view
        self.__view.set_fieldsets(self.__fieldsets)

    # -----------------------------------------------------------------------

    def is_installation_running(self) -> bool:
        return self.__model.is_installation_running()

    # -----------------------------------------------------------------------

    def is_installation_next(self) -> bool:
        """Return True if the installation starts at the next browse action.

        :return: (bool) The next fieldset is the installation one

        """
        install_index = self.__fieldsets.get_index_from_name("install_field")
        return self.__current + 1 == install_index

    # -----------------------------------------------------------------------

    def get_progress_values(self) -> tuple:
        """Get the current progress values.

        :return: (tuple) Percent, Header, Text

        """
        if self.__model.is_installation_running() is True:
            p = self.__fieldsets.get_progress()
            if p is not None:
                return p.get_percent(), p.get_header(), p.get_text()

        return 100, "Installation completed.", ""

    # -----------------------------------------------------------------------

    def get_current_fieldset_id(self):
        return self.__fieldsets.get_identifier(self.__current)

    def get_fieldset_id(self, idx):
        return self.__fieldsets.get_identifier(idx)

    # -----------------------------------------------------------------------
    # Handle an event
    # -----------------------------------------------------------------------

    def handle_prev_fieldset(self, current_index: int) -> bool:
        """Browse to the previous fieldset.

        :param current_index: (int) The current fieldset index
        :return: (bool) Success

        """
        # Does the client re-ask the same page and is sending the data
        # of the previously posted request???
        if self.__current == current_index:
            self.__current = max(0, self.__current - 1)
            self.__view.update_header_breadcrumb(self.__current)
            self.update_tree_content(actions=True, install=self.is_installation_next())
            return True

        return False

    # -----------------------------------------------------------------------

    def handle_next_fieldset(self, current_index: int):
        """Process a browse event: next of prev action.

        :param current_index: (int) The current fieldset index
        :raises: swappHTMLIncompleteFieldset: What the fieldset requires is not accepted
        :return: (bool) Success or not

        """
        # does the client re-ask the same page and is sending the data
        # of the previously posted request???
        if self.__current == current_index:
            self.__validate(current_index)
            self.__current = min(self.__current + 1, len(self.__fieldsets) - 1)
            cur = self.__current

            if self.get_current_fieldset_id() == "install_field":
                if self.__model.is_installation_running() is False:
                    # Update the main content for the fieldset and actions
                    self.update_tree_content(actions=False, install=True)
                    # Create the progress and start to install
                    progress = self.__fieldsets[cur].create_progress()
                    self.__model.installation_start(progress)
            else:
                # Update the main content for the fieldset and actions
                can_install = self.is_installation_next()
                self.update_tree_content(actions=True, install=can_install)

            # Update the header content for the breadcrumb
            self.__view.update_header_breadcrumb(cur)
            return True

        return False

    # -----------------------------------------------------------------------

    def handle_complete_event(self) -> bool:
        """Process the given event coming from the POST of install.

        """
        field = self.__fieldsets[self.__current]
        # The JS of the page informed the installation is completed,
        if hasattr(field, "completed") and callable(getattr(field, "completed")):
            field.completed(self.__model.errors, self.__model.installer)
            self.update_tree_content(actions=True, install=False)
            return True

        return False

    # -----------------------------------------------------------------------

    def handle_feature_event(self, event_name: str) -> dict:
        """Process the click on a checkbox: a feature, or an acceptance.

        The model is what changes. What is returned is the state the page
        has to show: the one of the checkbox, and the one of every feature
        of the same type, enabling a feature being able to change another.

        :param event_name: (str) Name of the checkbox which was clicked
        :return: (dict[str, bool]) Empty when the checkbox is unknown

        """
        _states = dict()
        if event_name.endswith(INPUT_SUFFIX) is False:
            return _states
        _name = event_name[:-len(INPUT_SUFFIX)]

        if _name.startswith(FEATURE_PREFIX) is True:
            _feature = _name[len(FEATURE_PREFIX):]
            _installer = self.__model.installer
            for _type in FEATURE_TYPES:
                _features = _installer.features_ids(_type)
                if _feature in _features:
                    self.__model.enable_feature(_feature)
                    for _other in _features:
                        _states[FEATURE_PREFIX + _other + INPUT_SUFFIX] = _installer.enable(_other)

        else:
            for _required in REQUIRED.values():
                if _name in _required:
                    _states[event_name] = self.__model.accept(_name)

        return _states

    # -----------------------------------------------------------------------
    # Manage the tree
    # -----------------------------------------------------------------------

    def update_tree_content(self,
                            actions: bool = True,
                            install: bool = True):
        """Update the tree content depending on the actual fieldset.

        :param actions: (bool) Whether the actions bar should be appended
        :param install: (bool) Whether the button "Install" is displayed or not

        """
        field = self.__fieldsets[self.__current]
        self.__view.update_tree_content(field, actions, install)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __validate(self, index: int) -> None:
        """Verify that what the fieldset of the given index requires is accepted.

        :param index: (int) Index of a fieldset
        :raises: swappHTMLIncompleteFieldset: Something it requires is not accepted

        """
        _identifier = self.__fieldsets.get_identifier(index)
        for _name in REQUIRED.get(_identifier, tuple()):
            if self.__model.is_accepted(_name) is False:
                logging.error("Checkbox validation failed.")
                raise swappHTMLIncompleteFieldset(MSG_REQUIRED[_identifier])
