"""
:filename: sppas.ui.swapp.app_plugins.plugins_model.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The model of the Plugins application.

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
import os
from datetime import datetime

from sppas.core.config import paths
from sppas.core.coreutils import sppasLogFile
from sppas.src.plugins import sppasPluginsManager
from sppas.src.structs import sppasOption
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from ..services.files import swappFilesManager
from ..services.files.files_chooser import swappFileChooser
from ..swapp_base.swapp_process import swappProcess

from .plugins_run import swappFileResult
from .plugins_run import swappPluginRun
from .plugins_run import swappPluginsReport
from .plugins_run import REPORT_PATTERN
from .plugins_run import REPORT_EXTENSION

# ---------------------------------------------------------------------------

# The file of the folder of a plugin which says of it what its card does not.
README = "README.txt"

# ---------------------------------------------------------------------------


class swappPluginsModel:
    """The plugins which are installed, as the domain of the plugins holds them.

    It is the only class of this application which speaks to the domain of
    the plugins and to the provision of files: what a plugin declares of
    itself is read there, and nothing is added to it. It starts the runs of
    the selected plugins as one process of swapp, and reads where they stand
    in their report: it holds nothing of a run.

    """

    def __init__(self, files: swappFilesManager):
        """Create the model, and the domain of the plugins it reads.

        :param files: (swappFilesManager) What the response holds of the provision of files
        :raises: Exception: The domain of the plugins cannot be created

        """
        self.__manager = sppasPluginsManager()
        self.__files = files
        # What asks the person for the archive to install, and says why none
        # came back.
        self.__chooser = swappFileChooser()

    # -----------------------------------------------------------------------

    def plugins(self) -> list:
        """Return the plugins which are installed, in the order the domain of the plugins gives them.

        :return: (list of sppasPluginParam) Empty when none is installed

        """
        _plugins = list()
        for _id in self.__manager.get_plugin_ids():
            _plugins.append(self.__manager.get_plugin(_id))

        return _plugins

    # -----------------------------------------------------------------------

    def one(self, plugin_id: str):
        """Return one plugin, by its identifier.

        :param plugin_id: (str) Identifier of a plugin
        :return: (sppasPluginParam|None) None when no plugin bears that identifier

        """
        return self.__manager.get_plugin(plugin_id)

    # -----------------------------------------------------------------------

    def options_of(self, plugin_id: str) -> list:
        """Return the options a plugin declares, to be set, each one with its value by default.

        They are copies: what is set on them is set for one request, and
        nothing of the plugin which is installed changes. The options which
        name the input file of the plugin are not among them: the files of a
        run give it.

        :param plugin_id: (str) Identifier of a plugin which is installed
        :return: (list of sppasOption)

        """
        _options = list()
        for _declared in self.__manager.get_plugin(plugin_id).get_options():
            if _declared.get_key() == "input" or _declared.get_untypedvalue() == "input":
                continue
            _option = sppasOption(_declared.get_key())
            _option.set_type(_declared.get_type())
            _option.set_value(_declared.get_untypedvalue())
            _option.set_text(_declared.get_text())
            _options.append(_option)

        return _options

    # -----------------------------------------------------------------------

    def readme(self, plugin_id: str) -> str:
        """Return the README which comes with a plugin, as it is written.

        :param plugin_id: (str) Identifier of a plugin which is installed
        :return: (str) Empty when its folder holds none

        """
        _readme = os.path.join(self.__manager.get_plugin(plugin_id).get_directory(), README)
        if os.path.exists(_readme) is False:
            return ""
        with open(_readme, "r") as fp:
            return fp.read()

    # -----------------------------------------------------------------------

    def choose_archive(self) -> str:
        """Return the archive the person designates with the file chooser of the machine.

        :return: (str) Name of the archive, with its path; empty when none was chosen

        """
        _files = self.__chooser.ask_for_files()
        if len(_files) == 0:
            return ""
        return _files[0]

    # -----------------------------------------------------------------------

    def why_no_archive(self) -> str:
        """Return why no archive was obtained, when there is something to say.

        :return: (str) Empty when the person simply chose none

        """
        return self.__chooser.why_nothing()

    # -----------------------------------------------------------------------

    def install(self, archive: str) -> str:
        """Install the plugin an archive holds, in a folder named after the archive.

        The spaces of the name of the archive are replaced by underscores.

        :param archive: (str) Name of the archive, with its path
        :raises: Exception: What the domain of the plugins refused
        :return: (str) The folder the plugin was installed in

        """
        _folder = os.path.splitext(os.path.basename(archive))[0]
        _folder = _folder.replace(" ", "_")
        self.__manager.install(archive, _folder)

        return _folder

    # -----------------------------------------------------------------------

    def remove(self, plugin_id: str) -> None:
        """Remove a plugin. What it produced is not removed.

        :param plugin_id: (str) Identifier of the plugin
        :raises: Exception: What the domain of the plugins refused

        """
        self.__manager.delete(plugin_id)

    # -----------------------------------------------------------------------

    def files_for(self) -> list:
        """Return the files the person chose, as the provision of files exposes them.

        :return: (list of str) Names of the files, with their path; empty when she chose none

        """
        _filenames = list()
        for _file in self.__files.files_for_app().get_filename_from_state(States().CHECKED):
            _filenames.append(_file.get_id())

        return _filenames

    # -----------------------------------------------------------------------

    def start(self, keys: list, options: dict) -> tuple:
        """Start the runs of the given plugins on the files the person chose, as one process.

        One run per plugin is written in the report before the process
        starts, in the given order, with its moment and the values its
        options hold, and with no result yet. The files are locked by the
        request which starts them.

        :param keys: (list of str) Identifiers of the plugins, in the order of the list
        :param options: (dict) key=identifier of a plugin, value=its options (list of sppasOption)
        :return: (tuple) The name of the report, and the name of the process, without their path

        """
        _filenames = self.files_for()
        _moment = datetime.now().isoformat(timespec="seconds")
        _runs = list()
        for _key in keys:
            _values = dict()
            for _option in options[_key]:
                _values[_option.get_key()] = _option.get_untypedvalue()
            _runs.append(swappPluginRun(_key, _moment, _values, _filenames))

        _name = sppasLogFile(pattern=REPORT_PATTERN, extension=REPORT_EXTENSION).get_filename()
        _report = swappPluginsReport(os.path.basename(_name))
        _report.write(_runs)
        self.__files.lock(_filenames)
        _process = swappProcess.start(self.run, (_runs, _report))

        return _report.name, _process.name

    # -----------------------------------------------------------------------

    def run(self, runs: list, report: swappPluginsReport, progress=None) -> None:
        """Perform the runs, one after the other, one file at a time.

        The runs are given a domain of the plugins made for them: the values
        of each run are set on the options of its plugin there, before its
        first file, and no other run reads them. The results are written in
        the report: the request which asks for them gives the files back.

        :param runs: (list of swappPluginRun) The runs, with no result yet
        :param report: (swappPluginsReport) The report the results are written in
        :param progress: (sppasBaseProgress|None) The progress of the process of the runs

        """
        _domain = sppasPluginsManager()
        for _run in runs:
            _plugin = _domain.get_plugin(_run.plugin)
            _values = _run.values
            for _key in _values:
                _plugin.get_option_from_key(_key).set_value(_values[_key])
            self.__perform(_domain, _run, runs, report, progress)

    # -----------------------------------------------------------------------

    def give_back(self, report: str) -> None:
        """Give the files of the runs back to the provision of files, as their report says it.

        The files are released, what appeared is given back, once, and that
        the runs have finished is said. It is done by the request which asks
        for the results: the copy of the files it works on is the one that
        request carries.

        :param report: (str) Name of the report, without its path
        :raises: ValueError: The name is not the one of a report of Plugins

        """
        _runs = swappPluginsReport(report).read()
        _filenames = list()
        if len(_runs) > 0:
            _filenames = _runs[0].files
        self.__files.release(_filenames)

        _produced = sppasWorkspace()
        for _run in _runs:
            for _result in _run.results:
                for _filename in _result.produced:
                    if os.path.isfile(_filename) is True:
                        _produced.add_file(_filename)
        self.__files.produced(_produced)
        self.__files.consumes({"task": "finished"})

    # -----------------------------------------------------------------------

    @staticmethod
    def is_running(process: str) -> bool:
        """Return True while the process of the given name has not ended.

        :param process: (str) Name of the process, without its path
        :return: (bool) False for a name no process bears

        """
        try:
            _process = swappProcess(process)
        except ValueError:
            return False
        if os.path.exists(os.path.join(paths.logs, process)) is False:
            return False
        _percent, _header, _text, _finished = _process.read()

        return _finished is False

    # -----------------------------------------------------------------------

    @staticmethod
    def the_run(report: str) -> list:
        """Return the runs as their report holds them, with the results written so far.

        :param report: (str) Name of the report, without its path
        :raises: ValueError: The name is not the one of a report of Plugins
        :return: (list of swappPluginRun)

        """
        return swappPluginsReport(report).read()

    # -----------------------------------------------------------------------

    def address_of(self, filename: str) -> str:
        """Return the address a produced file is reached at.

        :param filename: (str) Name of the produced file, with its path
        :return: (str) Empty when the file is reached at no address

        """
        return self.__files.address_of(filename)

    # -----------------------------------------------------------------------

    def address_of_all(self, filenames: list) -> str:
        """Return the address of one archive holding the produced files.

        :param filenames: (list of str) Names of the files, with their path
        :return: (str) Empty when no archive is to be made

        """
        return self.__files.address_of_all(filenames)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __perform(domain: sppasPluginsManager, run: swappPluginRun, runs: list, report: swappPluginsReport,
                  progress=None) -> None:
        """Start the plugin of a run on each of its files, and write each result in the report.

        Where the run stands is said before each file: the plugin, then the
        file and how many there are, and the files which are done, out of a
        hundred. What appeared for a file is what the folder of that file
        gained, or had written again, while the plugin was started on it.

        :param domain: (sppasPluginsManager) The domain of the plugins made for the runs
        :param run: (swappPluginRun) The run
        :param runs: (list of swappPluginRun) Every run, written together in the report
        :param report: (swappPluginsReport) The report
        :param progress: (sppasBaseProgress|None) The progress of the process

        """
        _total = len(run.files)
        for i, _filename in enumerate(run.files):
            if progress is not None:
                progress.set_header(run.plugin)
                progress.update((100 * i) // _total,
                                "{:s} ({:d}/{:d})".format(os.path.basename(_filename), i + 1, _total))
            _before = swappPluginsModel.__beside(_filename)
            _said, _status = domain.run_plugin_on_file(run.plugin, _filename)
            _produced = list()
            _after = swappPluginsModel.__beside(_filename)
            for _name in sorted(_after):
                if _name != _filename and (_name not in _before or _after[_name] > _before[_name]):
                    _produced.append(_name)
            run.add(swappFileResult(_filename, _status == 0, _said, _produced))
            report.write(runs)

    # -----------------------------------------------------------------------

    @staticmethod
    def __beside(filename: str) -> dict:
        """Return the files of the folder of a file, with the moment each one was written.

        :param filename: (str) Name of a file, with its path
        :return: (dict) key=name of a file, with its path, value=its modification time

        """
        _folder = os.path.dirname(filename)
        _files = dict()
        for _entry in os.listdir(_folder):
            _name = os.path.join(_folder, _entry)
            if os.path.isfile(_name) is True:
                _files[_name] = os.path.getmtime(_name)

        return _files
