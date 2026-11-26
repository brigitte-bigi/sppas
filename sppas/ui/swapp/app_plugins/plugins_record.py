"""
:filename: sppas.ui.swapp.app_plugins.plugins_record.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What one request of the Plugins application holds.

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

from sppas.core.coreutils import sppasTypeError

# ---------------------------------------------------------------------------


class swappPluginsRecord:
    """What one request holds: its task, what was decided, and what is shown.

    The view serializes what was decided into the form of the page, and the
    controller parses it back at the next request: nobody holds it between
    two requests. What was decided is which plugins are selected, whether
    the options of each plugin were applied, and their values. What is to be
    shown is not serialized: it is decided by the request which shows it.

    The options of every plugin are given to the record when it is created,
    each one with its value by default: the values a page transmitted are
    set on them.

    """

    def __init__(self, options: dict | None = None):
        """Create a record.

        :param options: (dict) key=identifier of a plugin, value=its options (list of sppasOption); None for none

        """
        self.__task = ""
        # The name of the report of the runs, which the page carries while
        # they go: their results are read in it.
        self.__run = ""
        self.__options = dict()
        if options is not None:
            self.__options = options
        self.__selected = list()
        self.__applied = dict()
        for _key in self.__options:
            self.__applied[_key] = False
        self.__to_be_shown = dict()

    # -----------------------------------------------------------------------

    def serialize(self) -> dict:
        """Return what was decided, as strings a page carries.

        :return: (dict) One entry per name, each of them a string

        """
        _data = dict()
        for _key in self.__options:
            _data.update(self.serialize_plugin(_key))

        return _data

    # -----------------------------------------------------------------------

    def serialize_plugin(self, key: str) -> dict:
        """Return what was decided of one plugin, as strings a page carries.

        Whether it is selected, whether its options were applied, and the
        values of its options.

        :param key: (str) The identifier of the plugin
        :raises: KeyError: No plugin has that identifier
        :return: (dict) One entry per name, each of them a string

        """
        _data = dict()
        _data["plugins_sel_" + key] = str(key in self.__selected)
        _data["plugins_applied_" + key] = str(self.__applied[key])
        for _option in self.__options[key]:
            _data["plugins_opt_" + key + "_" + _option.get_key()] = _option.get_untypedvalue()

        return _data

    # -----------------------------------------------------------------------

    def parse(self, data: dict) -> None:
        """Fill in the record with what a page sent.

        An entry which is absent takes its default value.

        :param data: (dict) What a page sent
        :raises: sppasTypeError: The given data is not a dictionary

        """
        if isinstance(data, dict) is False:
            raise sppasTypeError(data, "dict")

        self.__task = ""
        self.__run = ""
        self.__selected = list()
        self.__to_be_shown = dict()
        if isinstance(data.get("event_bake"), str) is True:
            self.__task = data["event_bake"]
        if isinstance(data.get("plugins_report"), str) is True:
            self.__run = data["plugins_report"]

        # A plugin is selected by its switch, and the page carries whether its
        # options were applied.
        for _key in self.__options:
            if data.get("plugins_sel_" + _key) == "True":
                self.__selected.append(_key)
            self.__applied[_key] = data.get("plugins_applied_" + _key) == "True"

        # The field of an option is named after the identifier of its plugin
        # and its own: the name is built from both, and never split.
        for _key in self.__options:
            for _option in self.__options[_key]:
                _name = "plugins_opt_" + _key + "_" + _option.get_key()
                if isinstance(data.get(_name), str) is True:
                    _option.set_value(data[_name])

    # -----------------------------------------------------------------------

    def show(self, key: str, value) -> None:
        """Put one thing to be shown in the record.

        :param key: (str) What it is
        :param value: What is to be shown

        """
        self.__to_be_shown[key] = value

    # -----------------------------------------------------------------------

    def get_options(self, key: str) -> list:
        """Return the options of one plugin, every one holding its value.

        :param key: (str) The identifier of the plugin
        :raises: KeyError: No plugin has that identifier
        :return: (list of sppasOption)

        """
        return self.__options[key]

    # -----------------------------------------------------------------------

    def set_options(self, key: str, options: list) -> None:
        """Give the options of one plugin the values the given ones hold.

        :param key: (str) The identifier of the plugin
        :param options: (list of sppasOption) Options of that plugin
        :raises: KeyError: No plugin has that identifier

        """
        for _option in options:
            for _mine in self.__options[key]:
                if _mine.get_key() == _option.get_key():
                    _mine.set_value(_option.get_untypedvalue())

    # -----------------------------------------------------------------------

    def get_task(self) -> str:
        """Return the task the request asks for, empty if none (str)."""
        return self.__task

    # -----------------------------------------------------------------------

    def get_run(self) -> str:
        """Return the name of the report of the runs, empty if none (str)."""
        return self.__run

    # -----------------------------------------------------------------------

    def set_run(self, name: str) -> None:
        """Set the name of the report of the runs.

        :param name: (str) Name of the report, without its path

        """
        self.__run = str(name)

    # -----------------------------------------------------------------------

    def get_selected(self) -> list:
        """Return the identifiers of the selected plugins, in the order of the list (list of str)."""
        return self.__selected

    # -----------------------------------------------------------------------

    def select(self, key: str) -> None:
        """Select a plugin, at its place in the order of the list.

        :param key: (str) The identifier of the plugin
        :raises: KeyError: No plugin has that identifier

        """
        if key not in self.__options:
            raise KeyError(key)
        _selected = list()
        for _key in self.__options:
            if _key == key or _key in self.__selected:
                _selected.append(_key)
        self.__selected = _selected

    # -----------------------------------------------------------------------

    def unselect(self, key: str) -> None:
        """Unselect a plugin.

        :param key: (str) The identifier of the plugin

        """
        if key in self.__selected:
            self.__selected.remove(key)

    # -----------------------------------------------------------------------

    def is_applied(self, key: str) -> bool:
        """Return True if the options of a plugin were applied.

        :param key: (str) The identifier of the plugin
        :raises: KeyError: No plugin has that identifier
        :return: (bool)

        """
        return self.__applied[key]

    # -----------------------------------------------------------------------

    def set_applied(self, key: str, applied: bool) -> None:
        """Say whether the options of a plugin were applied.

        :param key: (str) The identifier of the plugin
        :param applied: (bool) They were applied
        :raises: KeyError: No plugin has that identifier

        """
        if key not in self.__applied:
            raise KeyError(key)
        self.__applied[key] = applied is True

    # -----------------------------------------------------------------------

    def get_to_be_shown(self) -> dict:
        """Return what is to be shown (dict)."""
        return self.__to_be_shown

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    task = property(get_task, None)
    run = property(get_run, set_run)
    selected = property(get_selected, None)
    to_be_shown = property(get_to_be_shown, None)
