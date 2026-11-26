"""
:filename: sppas.ui.swapp.app_plugins.plugins_run.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The runs of the plugins, and their report.

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
import json
import os

from sppas.core.config import paths
from sppas.core.config import sg

# ---------------------------------------------------------------------------

# The report of the runs is named as every log file of SPPAS is.
REPORT_PATTERN = "plugins"
REPORT_EXTENSION = ".json"
REPORT_PREFIX = "{:s}_{:s}_".format(sg.__name__, REPORT_PATTERN)

# ---------------------------------------------------------------------------


class swappFileResult:
    """What happened to one file of a run: whether it was done, what was said, what appeared.

    """

    def __init__(self, filename: str, done: bool, said: str, produced: list | None = None):
        """Create the result of one file.

        :param filename: (str) Name of the file, with its path
        :param done: (bool) The plugin was started on it, and returned no error
        :param said: (str) What the plugin said about it, as it said it
        :param produced: (list of str) Names of the files which appeared for it, with their path

        """
        if produced is None:
            produced = list()

        self.__file = filename
        self.__done = done is True
        self.__said = said
        self.__produced = list(produced)

    # -----------------------------------------------------------------------

    def get_file(self) -> str:
        """Return the name of the file, with its path (str)."""
        return self.__file

    # -----------------------------------------------------------------------

    def is_done(self) -> bool:
        """Return True if the plugin was started on the file and returned no error (bool)."""
        return self.__done

    # -----------------------------------------------------------------------

    def get_said(self) -> str:
        """Return what the plugin said about the file, as it said it (str)."""
        return self.__said

    # -----------------------------------------------------------------------

    def get_produced(self) -> list:
        """Return the names of the files which appeared for it, with their path (list)."""
        return list(self.__produced)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    file = property(get_file, None)
    done = property(is_done, None)
    said = property(get_said, None)
    produced = property(get_produced, None)

# ---------------------------------------------------------------------------


class swappPluginRun:
    """One plugin started on files at one moment, with the values its options held.

    It holds one result per file which is done, in the order they were
    added.

    """

    def __init__(self, plugin: str, moment: str, values: dict, files: list):
        """Create a run, with no result yet.

        :param plugin: (str) Identifier of the plugin
        :param moment: (str) When the run started
        :param values: (dict) key=identifier of an option, value=the value it held, as a string
        :param files: (list of str) Names of the files the run is given, with their path

        """
        self.__plugin = plugin
        self.__moment = moment
        self.__values = dict(values)
        self.__files = list(files)
        self.__results = list()

    # -----------------------------------------------------------------------

    def add(self, result: swappFileResult) -> None:
        """Add the result of one file of the run.

        :param result: (swappFileResult) What happened to that file

        """
        self.__results.append(result)

    # -----------------------------------------------------------------------

    def remaining(self) -> int:
        """Return how many files the run was given and have no result yet (int)."""
        return len(self.__files) - len(self.__results)

    # -----------------------------------------------------------------------

    def is_over(self) -> bool:
        """Return True if the run holds one result per file it was given (bool)."""
        return self.remaining() == 0

    # -----------------------------------------------------------------------

    def serialize(self) -> dict:
        """Return everything a page needs to show the run, and nothing of the machine.

        :return: (dict)

        """
        _results = list()
        for _result in self.__results:
            _results.append({"file": _result.file, "done": _result.done,
                             "said": _result.said, "produced": _result.produced})

        return {"plugin": self.__plugin, "moment": self.__moment, "values": self.__values,
                "files": self.__files, "results": _results}

    # -----------------------------------------------------------------------

    @staticmethod
    def parse(data: dict) -> swappPluginRun:
        """Return the run a serialization holds.

        :param data: (dict) What serialize() gave
        :return: (swappPluginRun)

        """
        _run = swappPluginRun(data["plugin"], data["moment"], data["values"], data["files"])
        for _result in data["results"]:
            _run.add(swappFileResult(_result["file"], _result["done"], _result["said"], _result["produced"]))

        return _run

    # -----------------------------------------------------------------------

    def get_plugin(self) -> str:
        """Return the identifier of the plugin of the run (str)."""
        return self.__plugin

    # -----------------------------------------------------------------------

    def get_moment(self) -> str:
        """Return when the run started (str)."""
        return self.__moment

    # -----------------------------------------------------------------------

    def get_values(self) -> dict:
        """Return the values the options held when the run started, by option (dict)."""
        return dict(self.__values)

    # -----------------------------------------------------------------------

    def get_files(self) -> list:
        """Return the names of the files the run is given, with their path (list)."""
        return list(self.__files)

    # -----------------------------------------------------------------------

    def get_results(self) -> list:
        """Return the results of the files which are done, in the order they were added (list)."""
        return list(self.__results)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    plugin = property(get_plugin, None)
    moment = property(get_moment, None)
    values = property(get_values, None)
    files = property(get_files, None)
    results = property(get_results, None)

# ---------------------------------------------------------------------------


class swappPluginsReport:
    """The report of the runs of the selected plugins, one run per plugin.

    It is a file of the folder of the logs of SPPAS, and it is what any
    process of the server reads to say where the runs stand. It is written
    again, at once, each time a file has its result: a reader never finds it
    half written.

    """

    def __init__(self, name: str):
        """Create the report of the given name.

        :param name: (str) Name of the report, without its path
        :raises: ValueError: The name is not the one of a report of Plugins

        """
        if name != os.path.basename(name) or name.startswith(REPORT_PREFIX) is False \
                or name.endswith(REPORT_EXTENSION) is False:
            raise ValueError("Not the name of a report of the plugins: {}".format(name))
        self.__name = name

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the report, without its path (str)."""
        return self.__name

    # -----------------------------------------------------------------------

    def write(self, runs: list) -> None:
        """Write the report, at once.

        :param runs: (list of swappPluginRun) The runs, in the order of the list of the plugins

        """
        _runs = list()
        for _run in runs:
            _runs.append(_run.serialize())
        _filename = os.path.join(paths.logs, self.__name)
        _written = _filename + ".part"
        with open(_written, "w", encoding="utf-8") as fp:
            json.dump({"runs": _runs}, fp)
        os.replace(_written, _filename)

    # -----------------------------------------------------------------------

    def read(self) -> list:
        """Return the runs the report holds, with the results written so far.

        :return: (list of swappPluginRun) Empty when nothing was written

        """
        _filename = os.path.join(paths.logs, self.__name)
        if os.path.exists(_filename) is False:
            return list()
        with open(_filename, "r", encoding="utf-8") as fp:
            _data = json.load(fp)
        _runs = list()
        for _run in _data["runs"]:
            _runs.append(swappPluginRun.parse(_run))

        return _runs

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    name = property(get_name, None)
