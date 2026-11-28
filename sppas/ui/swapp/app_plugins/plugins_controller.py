"""
:filename: sppas.ui.swapp.app_plugins.plugins_controller.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The controller of the Plugins application.

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

from sppas.core.coreutils import sppasTypeError

from ..services.options import swappOptionsManager
from ..swapp_base.swapp_process import PROCESS_FIELD
from ..swapp_core.swappsg import swapp_settings

from .plugins_record import swappPluginsRecord
from .plugins_view import swappPluginsView

# ---------------------------------------------------------------------------

# The task which shows the options of a plugin carries its identifier, which
# is the identifier of their dialog as well: the container of the service of
# the options is appended to it.
OPTIONS_TASK = "plugins_options_"

# ---------------------------------------------------------------------------


class swappPluginsController:
    """Read the task a request carries, and answer it.

    It is called once per request, and holds nothing afterward. What is
    installed is shown at every request, each plugin with the README which
    comes with it, and the options of the plugin which is set.

    """

    def __init__(self, model, view: swappPluginsView):
        """Create the controller with what it is given.

        :param model: (swappPluginsModel) The model of Plugins
        :param view: (swappPluginsView) The view of Plugins
        :raises: sppasTypeError: The given view is not a swappPluginsView

        """
        if isinstance(view, swappPluginsView) is False:
            raise sppasTypeError(view, "swappPluginsView")
        self.__model = model
        self.__view = view
        self.__record = swappPluginsRecord()
        self.__options = None
        # The plugin whose options are set, empty if none.
        self.__configured = ""

    # -----------------------------------------------------------------------

    def handle(self, events: dict) -> None:
        """Do the task the events of a request ask for.

        :param events: (dict) What a page sent

        """
        # The options of every plugin, each one with its value by default:
        # the record sets on them what the page transmitted.
        _options = dict()
        for _plugin in self.__model.plugins():
            _options[_plugin.get_key()] = self.__model.options_of(_plugin.get_key())
        self.__record = swappPluginsRecord(_options)
        self.__record.parse(events)

        # The options of a plugin are handed to the service of the options,
        # which shows and checks them. Applying them validates the plugin:
        # their values are taken back, they are applied, and it is selected.
        # Giving them up invalidates it: they are no longer applied, and it
        # is not selected.
        self.__options = None
        self.__configured = ""
        if self.__record.task.startswith(OPTIONS_TASK) is True:
            _key = self.__record.task[len(OPTIONS_TASK):]
            if self.__model.one(_key) is not None:
                self.__configured = _key
                self.__options = swappOptionsManager(OPTIONS_TASK + _key, self.__record.get_options(_key))
                self.__options.consumes(events)
                if "options_validate" in events:
                    self.__record.set_options(_key, self.__options.options_for_app())
                    self.__record.set_applied(_key, True)
                    self.__record.select(_key)
                elif "options_close" in events:
                    self.__record.set_applied(_key, False)
                    self.__record.unselect(_key)

        elif self.__record.task == "plugins_run":
            self.__start(events)

        elif self.__record.task == "plugins_complete":
            self.__complete()

        # Installing and deleting a plugin happen where SPPAS runs on the
        # machine of the person, and nowhere else.
        elif self.__record.task == "plugins_install" and swapp_settings.served_locally is True:
            self.__install()

        elif self.__record.task == "plugins_delete" and swapp_settings.served_locally is True:
            self.__remove(events.get("plugins_to_delete", ""))

        # The runs which are going are the ones the page follows, whatever
        # it asked: while their process goes, the page shows their progress.
        _process = events.get(PROCESS_FIELD, "")
        if isinstance(_process, str) is True and self.__model.is_running(_process) is True:
            self.__record.show("running", True)
            self.__record.show("process", _process)

    # -----------------------------------------------------------------------

    def is_running(self) -> bool:
        """Return True if the request which was handled started the runs (bool)."""
        return self.__record.to_be_shown.get("running", False) is True

    # -----------------------------------------------------------------------

    def say_not_performed(self) -> None:
        """Have it said that the plugins could not be run: what was asked raised."""
        self.__record.show("not_performed", True)

    # -----------------------------------------------------------------------

    def has_installed(self) -> bool:
        """Return True if the request which was handled installed a plugin (bool)."""
        return "installed" in self.__record.to_be_shown

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build its tree from the record.

        The plugins which are installed and their README are shown, and the
        options of the plugin which is set, with what the page writes of that
        plugin.

        """
        _plugins = self.__model.plugins()
        _readmes = dict()
        for _plugin in _plugins:
            _readmes[_plugin.get_key()] = self.__model.readme(_plugin.get_key())
        self.__record.show("plugins", _plugins)
        self.__record.show("readmes", _readmes)

        if len(self.__configured) > 0:
            self.__record.show("configured", self.__configured)
            self.__record.show("options", self.__options.container())
            self.__record.show("values", self.__record.serialize_plugin(self.__configured))

        self.__view.populate_tree_content(self.__record)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __start(self, events: dict) -> None:
        """Start the runs of the selected plugins, when nothing stands in the way.

        One start at a time for one person: the page carries the name of the
        process of the runs she started, and a process which has not ended
        refuses another start. Otherwise, what is missing is said: a plugin
        selected, the options of each selected plugin applied, a file chosen.

        :param events: (dict) What the page sent

        """
        _process = events.get(PROCESS_FIELD, "")
        if isinstance(_process, str) is True and self.__model.is_running(_process) is True:
            self.__record.show("missing", ["running"])
            return

        _missing = list()
        if len(self.__record.selected) == 0:
            _missing.append("plugin")
        _not_applied = list()
        for _key in self.__record.selected:
            if self.__record.is_applied(_key) is False:
                _not_applied.append(self.__model.one(_key).get_name())
        if len(_not_applied) > 0:
            _missing.append("applied")
            self.__record.show("not_applied", _not_applied)
        if len(self.__model.files_for()) == 0:
            _missing.append("files")
        if len(_missing) > 0:
            self.__record.show("missing", _missing)
            return

        _options = dict()
        for _key in self.__record.selected:
            _options[_key] = self.__record.get_options(_key)
        _report, _process = self.__model.start(self.__record.selected, _options)
        self.__record.run = _report
        self.__record.show("running", True)
        self.__record.show("process", _process)

    # -----------------------------------------------------------------------

    def __complete(self) -> None:
        """Show the runs and their results, as their report gives them."""
        try:
            _runs = self.__model.the_run(self.__record.run)
        except ValueError as e:
            logging.error(str(e))
            self.__record.show("unavailable", str(e))
            return

        # The files are given back with the copy of the files this request
        # carries.
        self.__model.give_back(self.__record.run)
        self.__record.show("results", _runs)

        # The runs are asked for once their process has ended: a run which
        # holds fewer results than files stopped, and will get no more.
        _stopped = list()
        for _run in _runs:
            if _run.is_over() is False:
                _plugin = self.__model.one(_run.plugin)
                if _plugin is None:
                    _stopped.append(_run.plugin)
                else:
                    _stopped.append(_plugin.get_name())
        if len(_stopped) > 0:
            self.__record.show("stopped", _stopped)

        # Where the person is not on the machine which wrote them, each
        # produced file is reached at an address: the page leads to it.
        _addresses = dict()
        for _run in _runs:
            for _result in _run.results:
                for _produced in _result.produced:
                    _address = self.__model.address_of(_produced)
                    if len(_address) > 0:
                        _addresses[_produced] = _address
        self.__record.show("addresses", _addresses)

    # -----------------------------------------------------------------------

    def __install(self) -> None:
        """Install the plugin of the archive the person designates, and say what came of it."""
        _archive = self.__model.choose_archive()
        if len(_archive) == 0:
            _why = self.__model.why_no_archive()
            if len(_why) > 0:
                self.__record.show("no_archive", _why)
            return
        try:
            self.__record.show("installed", self.__model.install(_archive))
        except Exception as e:
            self.__record.show("not_installed", (_archive, str(e)))

    # -----------------------------------------------------------------------

    def __remove(self, plugin_id: str) -> None:
        """Remove the plugin the person chose, and say what came of it.

        :param plugin_id: (str) Identifier of the plugin, empty when none was chosen

        """
        if isinstance(plugin_id, str) is False or self.__model.one(plugin_id) is None:
            return
        try:
            self.__model.remove(plugin_id)
            self.__record.show("deleted", plugin_id)
        except Exception as e:
            self.__record.show("not_deleted", (plugin_id, str(e)))
