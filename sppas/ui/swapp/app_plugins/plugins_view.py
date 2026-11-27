"""
:filename: sppas.ui.swapp.app_plugins.plugins_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The view of the Plugins application.

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
from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_view import swappBaseView
from ..swapp_core.swappsg import swapp_settings

from .plugins_record import swappPluginsRecord
from .plugslist import swappPluginsList
from .plugslist import swappPluginRunPanel

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Plugins")
MSG_INSTALL = _("Install")
MSG_DELETE = _("Delete")
MSG_INSTALLED = _("Plugin successfully installed in folder {:s}.")
MSG_NOT_INSTALLED = _("Plugin '{:s}' can't be installed due to the following error:\n{!s:s}")
MSG_DELETED = _("Plugin {:s} was successfully deleted.")
MSG_NOT_DELETED = _("Plugin '{:s}' can't be deleted due to the following error:\n{!s:s}")
MSG_NO_PLUGINS = _("No plugin installed.")
MSG_TO_DELETE = _("Select the plugin to delete:")
MSG_WAITING = _("Waiting for the archive in the selection window...")
MSG_NOT_PERFORMED = _("The plugins could not be run.")
MSG_REPORT_UNAVAILABLE = _("The report is not available...\nError is: {:s}")
MSG_STOPPED = _("These runs stopped before their last file: {:s}")
MSG_NO_DOMAIN = _("No plugin can be listed.")
MSG_FILES = _("Add files")
MSG_PLUGINS = _("Plugins")
MSG_RUNS = _("Run of the plugins")
MSG_RUN = _("Let's go!")
MSG_RUN_MISSING = _("No plugin is selected.")
MSG_MISSING = {
    "running": _("A run is going: wait until it is over."),
    "plugin": MSG_RUN_MISSING,
    "applied": _("The options of these plugins were not applied: {:s}"),
    "files": _("No file was chosen.")
}
MSG_RESET = _("Reset")
MSG_INTRO = _("Plugins runs on your files programs added to SPPAS. Add the files, select the plugins, "
              "set their options, then click Let's go!. What each plugin did with each file is given in "
              "the results.")

# How often the page asks where the runs stand, in milliseconds: the local
# server answers at once, a distant one is asked less often.
INTERVAL_LOCAL_MS = 200
INTERVAL_DISTANT_MS = 1000

# The script of the page, filled in with the folder of the scripts.
BODY_SCRIPT = """
        import {{ PluginsManager, SwappOptions }} from '/{js}sppas.js';
        import SwappFiles from '/{js}swapp_files.js';

        // The managers drive the sections of the page: they are started when
        // the page shows them, and not while it shows the help.
        if (document.getElementById('plugins_files_section') !== null) {{
            const swappFiles = new SwappFiles();
            swappFiles.handleSwappFilesOnLoad();
            // The windows of the options, which the service of the options
            // offers: their listeners are attached before the ones of the page.
            const swappOptions = new SwappOptions('plugins_form', 'plugins_options_');
            swappOptions.handleSwappOptionsOnLoad();
            const pluginsManager = new PluginsManager({interval});
            pluginsManager.handlePluginsManagerOnLoad();
        }}
"""

# ---------------------------------------------------------------------------


class swappPluginsView(swappBaseView):
    """View class responsible for populating the page of Plugins.

    It builds the header and the nav of the page, and the main content from
    a record: it decides nothing, and shows what it is given.

    """

    def __init__(self, tree: HTMLTree, form_id: str):
        """Initialize and populate the Plugins view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate
        :param form_id: (str) Identifier of the form which carries the record of the app
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappPluginsView: tree must be an instance of HTMLTree. "
                            "Got {} instead.".format(type(tree)))
        # Set before the base view populates the nav with it.
        self.__form_id = form_id
        # The section the container of the provision of files is written in.
        self.__files = None
        # The container of the options of the plugin which is set, and what
        # the page writes of a plugin in its form.
        self.__options = None
        self.__values = dict()
        # The section of the plugins.
        self.__plugins = None
        # The section of the runs, None when there is none; and what is said
        # in the dialog of information and in the one of the errors.
        self.__run = None
        self.__info = ""
        self.__error = ""
        super(swappPluginsView, self).__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self, *args, **kwargs):
        """Override. Add the sheet of Plugins."""
        super()._populate_head_css(*args, **kwargs)
        self._htree.head.link("stylesheet", swapp_settings.css + "app_plugins.css", link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page."""
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _form_id(self) -> str:
        """Override. Return the identifier of the form which carries the record of the app."""
        return self.__form_id


    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section.

        The page asks where the runs stand at the interval of the server
        which serves it.

        """
        _interval = INTERVAL_DISTANT_MS
        if swapp_settings.served_locally is True:
            _interval = INTERVAL_LOCAL_MS
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT.format(js=swapp_settings.js, interval=_interval))

    # -----------------------------------------------------------------------

    def populate_tree_content(self, record: swappPluginsRecord) -> None:
        """Populate the main content of the page from what the record says is to be shown.

        :param record: (swappPluginsRecord) What is to be shown

        """
        _shown = record.to_be_shown

        # The form of the page: every button and every switch of the page is
        # tied to it by its attribute "form". What was decided is carried in
        # it, hidden, but the selection of a plugin, which its switch carries:
        # the next request rebuilds the record from all of it.
        _form = TagNode(self._htree.body_main.identifier, None, "form",
                        attributes={"id": self.__form_id, "method": "post"})
        self._htree.body_main.append_child(_form)
        _data = record.serialize()
        for _name in _data:
            if _name.startswith("plugins_sel_") is False:
                _form.append_child(EmptyNode(_form.identifier, None, "input",
                                             attributes={"type": "hidden", "name": _name, "value": _data[_name]}))

        self._htree.body_main.append_child(HTMLNode(self._htree.body_main.identifier, None, "p",
                                                    value=MSG_INTRO))

        # The sections of the page, in their order: the files, the plugins,
        # and the results, when there are some.
        self.__files = self.__append_section("plugins_files_section", MSG_FILES)
        _plugins = self.__append_section("plugins_section", MSG_PLUGINS)
        self.__plugins = _plugins
        # Installing and deleting a plugin happen where SPPAS runs on the
        # machine of the person, and nowhere else: above the cards, as above
        # the list in the desktop interface.
        if swapp_settings.served_locally is True:
            _p = TagNode(_plugins.identifier, None, "p")
            _plugins.append_child(_p)
            # Installing asks the file chooser of the machine for the archive.
            _p.append_child(HTMLNode(_p.identifier, None, "button", value=MSG_INSTALL,
                                     attributes={"type": "submit", "id": "plugins_install", "form": self.__form_id,
                                                 "name": "event_bake", "value": "plugins_install"}))
            # Deleting is done in a dialog, where the plugin is chosen among
            # the installed ones.
            _p.append_child(HTMLNode(_p.identifier, None, "button", value=MSG_DELETE,
                                     attributes={"type": "button", "id": "plugins_delete",
                                                 "aria-haspopup": "dialog", "aria-controls": "plugins_delete_dialog"}))
            # The selection window may open behind the browser, and the page
            # would seem to do nothing: while the server waits for what is
            # chosen in it, the page says so, with a progress which has no
            # end. It is hidden until the button is pressed.
            _waiting = TagNode(_plugins.identifier, None, "div",
                               attributes={"id": "plugins_waiting", "role": "status", "hidden": None})
            _plugins.append_child(_waiting)
            _waiting.append_child(HTMLNode(_waiting.identifier, None, "p", value=MSG_WAITING,
                                           attributes={"id": "plugins_waiting_text"}))
            _waiting.append_child(HTMLNode(_waiting.identifier, None, "progress",
                                           attributes={"aria-labelledby": "plugins_waiting_text"}))
            self.__append_delete(_plugins, _shown.get("plugins", list()))
        # The container of the options of the plugin which is set stands in
        # the dialog of that plugin.
        self.__options = _shown.get("options", None)
        self.__values = _shown.get("values", dict())
        _plugins.append_child(swappPluginsList(_plugins.identifier,
                                               _shown.get("plugins", list()),
                                               _shown.get("readmes", dict()),
                                               record.selected,
                                               _shown.get("configured", ""),
                                               self.__options,
                                               self.__form_id))
        # What starts the runs is disabled while no plugin is selected.
        _attributes = {"type": "submit", "class": "action-button", "form": self.__form_id,
                       "name": "event_bake", "value": "plugins_run"}
        _class = "plugins-missing hidden"
        if len(record.selected) == 0:
            _attributes["disabled"] = None
            _attributes["aria-describedby"] = "plugins_run_state"
            _class = "plugins-missing"
        _plugins.append_child(HTMLNode(_plugins.identifier, None, "button", value=MSG_RUN,
                                       attributes=_attributes))
        # A reset is a reset: the decisions and the files go together, so it
        # is asked of the server.
        _plugins.append_child(HTMLNode(_plugins.identifier, None, "button", value=MSG_RESET,
                                       attributes={"type": "submit", "form": self.__form_id,
                                                   "name": "event_bake", "value": "plugins_reset"}))
        # What says no plugin is selected is always written, and hidden when
        # one is: selecting a plugin in the page makes no request.
        _plugins.append_child(HTMLNode(_plugins.identifier, None, "p", value=MSG_RUN_MISSING,
                                       attributes={"id": "plugins_run_state", "class": _class}))
        # The runs: while they go, their progress and the names the page
        # follows them by; once over, their results, plugin by plugin.
        self.__run = None
        if _shown.get("running", False) is True or "results" in _shown:
            self.__run = self.__append_section("plugins_run_section", MSG_RUNS)
            self.__run.append_child(swappPluginRunPanel(self.__run.identifier, self.__form_id, record.run,
                                                        _shown.get("process", ""),
                                                        _shown.get("results", list()),
                                                        _shown.get("addresses", dict())))

        # What stands in the way of a start is said in the dialog of
        # information, and so is what came of installing or deleting a
        # plugin; what the domain of the plugins refused is said in the
        # dialog of the errors.
        self.append_alert_dialogs(self._htree.body_main)
        self.__info = ""
        self.__error = ""
        _errors = list()
        if _shown.get("not_performed", False) is True:
            _errors.append(MSG_NOT_PERFORMED)
        if "unavailable" in _shown:
            _errors.append(MSG_REPORT_UNAVAILABLE.format(_shown["unavailable"]))
        if "stopped" in _shown:
            _errors.append(MSG_STOPPED.format(", ".join(_shown["stopped"])))
        if "no_archive" in _shown:
            _errors.append(_shown["no_archive"])
        if "not_installed" in _shown:
            _errors.append(MSG_NOT_INSTALLED.format(_shown["not_installed"][0], _shown["not_installed"][1]))
        if "not_deleted" in _shown:
            _errors.append(MSG_NOT_DELETED.format(_shown["not_deleted"][0], _shown["not_deleted"][1]))
        _dialog = self._htree.body_main.get_child("error_dialog")
        for _text in _errors:
            _dialog.append_child(HTMLNode(_dialog.identifier, None, "p", value=_text))
        self.__error = " ".join(_errors)

        _said = list()
        if "installed" in _shown:
            _said.append(MSG_INSTALLED.format(_shown["installed"]))
        if "deleted" in _shown:
            _said.append(MSG_DELETED.format(_shown["deleted"]))
        for _missing in _shown.get("missing", list()):
            _text = MSG_MISSING[_missing]
            if _missing == "applied":
                _text = _text.format(", ".join(_shown.get("not_applied", list())))
            _said.append(_text)
        if len(_said) > 0:
            _dialog = self._htree.body_main.get_child("info_dialog")
            for _text in _said:
                _dialog.append_child(HTMLNode(_dialog.identifier, None, "p", value=_text))
            self.__info = " ".join(_said)

    # -----------------------------------------------------------------------

    def populate_unavailable(self) -> None:
        """Populate the main content of the page when no plugin can be listed.

        The domain of the plugins could not be created: it is said in the
        dialog of the errors.

        """
        self.append_alert_dialogs(self._htree.body_main)
        _dialog = self._htree.body_main.get_child("error_dialog")
        _dialog.append_child(HTMLNode(_dialog.identifier, None, "p", value=MSG_NO_DOMAIN))
        self.__error = MSG_NO_DOMAIN

    # -----------------------------------------------------------------------

    def get_files(self) -> TagNode | None:
        """Return the section the container of the provision of files is written in, None before the page is built."""
        return self.__files

    # -----------------------------------------------------------------------

    def get_options(self):
        """Return the container of the options of the plugin which is set, None when none is set."""
        return self.__options

    # -----------------------------------------------------------------------

    def get_values(self) -> dict:
        """Return what the page writes of a plugin in its form, empty if nothing (dict)."""
        return self.__values

    # -----------------------------------------------------------------------

    def get_plugins(self) -> TagNode | None:
        """Return the section of the plugins, None before the page is built."""
        return self.__plugins

    # -----------------------------------------------------------------------

    def get_run(self) -> TagNode | None:
        """Return the section of the runs, None when there is none."""
        return self.__run

    # -----------------------------------------------------------------------

    def get_info(self) -> str:
        """Return what is said in the dialog of information, empty if nothing (str)."""
        return self.__info

    # -----------------------------------------------------------------------

    def get_error(self) -> str:
        """Return what is said in the dialog of the errors, empty if nothing (str)."""
        return self.__error

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __append_delete(self, parent: TagNode, plugins: list) -> None:
        """Append the dialog where the plugin to delete is chosen among the installed ones.

        :param parent: (TagNode) The section of the plugins
        :param plugins: (list of sppasPluginParam) The installed plugins

        """
        _dialog = TagNode(parent.identifier, "plugins_delete_dialog", "dialog",
                          attributes={"id": "plugins_delete_dialog", "class": "hidden-alert",
                                      "aria-labelledby": "plugins_delete_dialog_h"})
        parent.append_child(_dialog)
        _dialog.append_child(HTMLNode(_dialog.identifier, None, "h2", value=MSG_DELETE,
                                      attributes={"id": "plugins_delete_dialog_h"}))
        if len(plugins) == 0:
            _dialog.append_child(HTMLNode(_dialog.identifier, None, "p", value=MSG_NO_PLUGINS))
            return

        _fieldset = TagNode(_dialog.identifier, None, "fieldset")
        _dialog.append_child(_fieldset)
        _fieldset.append_child(HTMLNode(_fieldset.identifier, None, "legend", value=MSG_TO_DELETE))
        for _plugin in plugins:
            _key = _plugin.get_key()
            _p = TagNode(_fieldset.identifier, None, "p")
            _fieldset.append_child(_p)
            _p.append_child(EmptyNode(_p.identifier, None, "input",
                                      attributes={"type": "radio", "id": "plugins_to_delete_" + _key,
                                                  "name": "plugins_to_delete", "value": _key,
                                                  "form": self.__form_id}))
            _p.append_child(HTMLNode(_p.identifier, None, "label", value=_key,
                                     attributes={"for": "plugins_to_delete_" + _key}))
        _dialog.append_child(HTMLNode(_dialog.identifier, None, "button", value=MSG_DELETE,
                                      attributes={"type": "submit", "class": "action-button", "form": self.__form_id,
                                                  "name": "event_bake", "value": "plugins_delete"}))

    # -----------------------------------------------------------------------

    def __append_section(self, identifier: str, title: str) -> TagNode:
        """Append a section of the page, under its title, and return it.

        :param identifier: (str) Identifier of the section
        :param title: (str) Its title
        :return: (TagNode) The section

        """
        _section = TagNode(self._htree.body_main.identifier, identifier, "section",
                           attributes={"id": identifier, "class": "panel"})
        self._htree.body_main.append_child(_section)
        _section.append_child(HTMLNode(_section.identifier, None, "h2", value=title))

        return _section

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    files = property(get_files, None)
    options = property(get_options, None)
    values = property(get_values, None)
    plugins = property(get_plugins, None)
    run = property(get_run, None)
    info = property(get_info, None)
    error = property(get_error, None)
