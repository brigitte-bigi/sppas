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

from .fieldsets import swappSetupFieldsets

# ---------------------------------------------------------------------------


class swappSetupController:

    def __init__(self, model, view, page_name: str = "setup.html"):
        """Initialize the controller with a model and a view.

        :param model: (swappSetupModel) The model managing the applications.
        :param view: (swappSetupView) The view managing the HTML structure.
        :param page_name: (str) Name of the HTML page this controller is managing

        """
        self.__model = model
        self.__view = view
        self.__fieldsets = swappSetupFieldsets(self.__model.installer, page_name)

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
        self.__fieldsets = swappSetupFieldsets(self.__model.installer, page_name)

        # Assign the fieldsets to the view
        self.__view.set_fieldsets(self.__fieldsets)

    # -----------------------------------------------------------------------

    def is_installation_running(self) -> bool:
        return self.__model.is_installation_running()

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
        return self.__fieldsets.get_current_identifier()

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
        if self.__fieldsets.get_current() == current_index:
            cur = self.__fieldsets.browse_previous()
            self.__view.update_header_breadcrumb(cur)
            self.update_tree_content(actions=True, install=False)
            return True

        return False

    # -----------------------------------------------------------------------

    def handle_next_fieldset(self, current_index: int):
        """Process a browse event: next of prev action.

        :param current_index: (int) The current fieldset index
        :raises: HTMLincompleteFieldset: Some required checkbox is not checked
        :return: (bool) Success or not

        """
        # does the client re-ask the same page and is sending the data
        # of the previously posted request???
        if self.__fieldsets.get_current() == current_index:
            self.__fieldsets[current_index].validate()
            cur = self.__fieldsets.browse_next()

            if self.__fieldsets.get_current_identifier() == "install_field":
                if self.__model.is_installation_running() is False:
                    # Update the main content for the fieldset and actions
                    self.update_tree_content(actions=False, install=True)
                    # Create the progress and start to install
                    progress = self.__fieldsets[cur].create_progress()
                    self.__model.installation_start(progress)
            else:
                # Update the main content for the fieldset and actions
                # cur = self.__fieldsets.browse_next()
                can_install = self.__fieldsets.get_current_identifier() == "install_field"
                self.update_tree_content(actions=True, install=can_install)

            # Update the header content for the breadcrumb
            self.__view.update_header_breadcrumb(cur)
            return True

        return False

    # -----------------------------------------------------------------------

    def handle_complete_event(self) -> bool:
        """Process the given event coming from the POST of install.

        """
        field = self.__fieldsets[self.__fieldsets.get_current()]
        # The JS of the page informed the installation is completed,
        if hasattr(field, "completed") and callable(getattr(field, "completed")):
            field.completed(self.__model.errors, self.__model.installer)
            self.update_tree_content(actions=True, install=False)
            return True

        return False

    # -----------------------------------------------------------------------

    def handle_feature_event(self, feature_name: str) -> dict:
        """Process a feature event: enable or disable a feature in the page.

        :param feature_name: (str) Name of the checked feature element
        :return: (dict[str, bool] or None)

        """
        field = self.__fieldsets[self.__fieldsets.get_current()]
        self.__model.enable_feature(feature_name)
        return field.process_event(feature_name)

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
        field = self.__fieldsets[self.__fieldsets.get_current()]
        self.__view.update_tree_content(field, actions, install)
