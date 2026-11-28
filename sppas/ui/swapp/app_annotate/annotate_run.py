"""
:filename: sppas.ui.swapp.app_annotate.annotate_run.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The run of the selected annotations, in a thread.

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
import json

from sppas.core.config import paths
from sppas.core.config import sg
from sppas.core.coreutils import sppasLogFile
from sppas.core.coreutils import sppasBaseProgress
from sppas.src.annotations import sppasAnnotationsManager
from sppas.src.annotations import sppasParam
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from ..swapp_core.swappsg import swapp_settings
from ..swapp_base.swapp_process import swappProcess

from .annotate_provision import swappModelProvision

# ---------------------------------------------------------------------------

RESULTS_PATTERN = "annotate"
RESULTS_EXTENSION = ".json"
RESULTS_PREFIX = "{:s}_{:s}_".format(sg.__name__, RESULTS_PATTERN)

# ---------------------------------------------------------------------------


class swappRootResult:
    """What came of one root of the batch: its status, then the files produced under it.

    """

    def __init__(self, root: str, produced: list):
        """Create the result of one root.

        :param root: (str) Identifier of the root of the batch
        :param produced: (list of str) Names of the files produced under it, with their path

        """
        self.__root = root
        self.__produced = list(produced)

    # -----------------------------------------------------------------------

    def get_root(self) -> str:
        """Return the identifier of the root of the batch (str)."""
        return self.__root

    # -----------------------------------------------------------------------

    def get_status(self) -> str:
        """Return written when at least one file was produced under the root, refused otherwise (str)."""
        if len(self.__produced) > 0:
            return "written"
        return "refused"

    # -----------------------------------------------------------------------

    def get_produced(self) -> list:
        """Return the names of the files produced under the root, with their path (list)."""
        return list(self.__produced)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    root = property(get_root, None)
    status = property(get_status, None)
    produced = property(get_produced, None)

# ---------------------------------------------------------------------------


class swappAnnotateProgress(sppasBaseProgress):
    """The progress the manager of the annotations is given.

    The API says where it stands as a fraction, from 0 to 1, and the
    progress of the process holds a percent: what the API gives is
    multiplied by 100, then handed to the progress of the process.

    """

    def __init__(self, progress):
        """Create the progress which hands what it is given to the one of the process.

        :param progress: (swappProcessProgress) The progress of the process

        """
        super(swappAnnotateProgress, self).__init__()
        self.__progress = progress

    # -----------------------------------------------------------------------

    def set_header(self, header: str) -> None:
        """Override. Hand the header to the progress of the process.

        :param header: (str) What the API is doing

        """
        self._header = str(header)
        self.__progress.set_header(header)

    # -----------------------------------------------------------------------

    def update(self, percent: float | None = None, message: str | None = None) -> None:
        """Override. Hand the fraction, as a percent, and the text to the progress of the process.

        :param percent: (float) The fraction the API gives, from 0 to 1, None to leave it unchanged
        :param message: (str) The text, None to leave it unchanged

        """
        _percent = None
        if percent is not None:
            self._percent = percent
            _percent = percent * 100
        if message is not None:
            self._text = str(message)
        self.__progress.update(_percent, message)

# ---------------------------------------------------------------------------


class swappRunResults:
    """The results of one run: its batch, its report, and what came of every root of the batch.

    It is a file of the folder of the logs of SPPAS, and it is what any
    process of the server reads to give the results of a run and to give
    its batch back. It is written before the run starts, with no result, and
    again, at once, when the run has ended: a reader never finds it half
    written.

    """

    def __init__(self, name: str):
        """Create the results of the given name.

        :param name: (str) Name of the results, without its path
        :raises: ValueError: The name is not the one of the results of a run of Annotate

        """
        if name != os.path.basename(name) or name.startswith(RESULTS_PREFIX) is False \
                or name.endswith(RESULTS_EXTENSION) is False:
            raise ValueError("Not the name of the results of a run: {}".format(name))
        self.__name = name

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the results, without its path (str)."""
        return self.__name

    # -----------------------------------------------------------------------

    def write(self, files: list, report: str, results: list, finished: bool = False) -> None:
        """Write the results, at once.

        :param files: (list of str) The files of the batch, which are locked while the run goes
        :param report: (str) The report to give back with what was produced, empty locally
        :param results: (list of swappRootResult) What came of every root of the batch
        :param finished: (bool) The run has ended

        """
        _lines = list()
        for _result in results:
            _lines.append({"root": _result.root, "produced": _result.produced})
        _filename = os.path.join(paths.logs, self.__name)
        _written = _filename + ".part"
        with open(_written, "w", encoding="utf-8") as fp:
            json.dump({"files": files, "report": report, "finished": finished, "results": _lines}, fp)
        os.replace(_written, _filename)

    # -----------------------------------------------------------------------

    def read(self) -> tuple:
        """Return the files of the batch, the report, what came of every root, and whether the run has ended.

        :return: (tuple) (list of str, str, list of swappRootResult, bool); ([], "", [], False) when nothing was written

        """
        _filename = os.path.join(paths.logs, self.__name)
        if os.path.exists(_filename) is False:
            return list(), "", list(), False
        with open(_filename, "r", encoding="utf-8") as fp:
            _data = json.load(fp)
        _results = list()
        for _line in _data["results"]:
            _results.append(swappRootResult(_line["root"], _line["produced"]))
        return _data["files"], _data["report"], _results, _data["finished"]

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    name = property(get_name, None)

# ---------------------------------------------------------------------------


class swappModelRun:
    """Have the API execute the selected annotations.

    It names the report and the results, locks the batch, and creates a
    sppasAnnotationsManager, the merge option being given to it. The
    annotations are a process of swapp: the manager executes them in the
    thread of that process, and the progress it is given is the one of the
    process, which says where they stand in the file of the process. Once
    they have been, the process writes what came of every root of the batch
    in the results. The request which asks for the results gives the batch
    back: it releases it, gives back what was produced, and says it has
    finished. Nothing of a run is held between two requests: the page
    transmits the names of its report, of its results and of its process,
    and any process of the server reads them. It is the only class of this
    application which has the API execute annotations.

    """

    def __init__(self, provision: swappModelProvision):
        """Create the run.

        :param provision: (swappModelProvision) The access to the provision of files

        """
        self.__provision = provision

    # -----------------------------------------------------------------------

    def start(self, batch, parameters: sppasParam, merge: bool) -> tuple:
        """Start a run, and return the names of its report, of its results and of its process.

        The report is named first, under a name no report bore before, and
        the results are written with none. What was decided is handed to the
        API as it stands, with the workspace and the name of the report.

        :param batch: (sppasWorkspace) The workspace the provision of files handed
        :param parameters: (sppasParam) What was decided
        :param merge: (bool) One file gathering everything is to be created
        :return: (tuple) The name of the report, of the results and of the process, without their path

        """
        _report = sppasLogFile(pattern="report").get_filename()
        # Online, the report is written beside the files of the batch: it is
        # given back with what was produced.
        _given_back = ""
        if swapp_settings.served_locally is False:
            _report = os.path.join(self.__provision.folder(), os.path.basename(_report))
            _given_back = _report
        parameters.set_report_filename(_report)
        parameters.set_workspace(batch)

        _filenames = list()
        for _file in batch.get_filename_from_state(States().CHECKED):
            _filenames.append(_file.get_id())

        # The roots which hold a file of the batch, in the order of the batch.
        _roots = list()
        for _path in batch.get_paths():
            for _root in _path:
                for _file in _root:
                    if _file.get_id() in _filenames and (_root.get_id() in _roots) is False:
                        _roots.append(_root.get_id())

        _results = swappRunResults(os.path.basename(
            sppasLogFile(pattern=RESULTS_PATTERN, extension=RESULTS_EXTENSION).get_filename()))
        _results.write(_filenames, _given_back, list())

        self.__provision.lock(_filenames)
        # Given no parameters, the manager executes nothing in a thread of its
        # own: it executes the annotations in the thread of the process.
        _manager = sppasAnnotationsManager(do_merge=merge)
        _process = swappProcess.start(self.__perform,
                                      (batch, parameters, _manager, _filenames, _roots, _given_back, _results))

        return os.path.basename(_report), _results.name, _process.name

    # -----------------------------------------------------------------------

    @staticmethod
    def is_running(process: str) -> bool:
        """Return True while the process of the given name has not ended.

        It is read in the file of the process, which says it has ended once
        the batch was given back.

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
    def results(name: str) -> list:
        """Return what came of every root of the batch of a run, as its results say it.

        :param name: (str) Name of the results, without its path
        :raises: ValueError: The name is not the one of the results of a run of Annotate
        :return: (list of swappRootResult) In the order of the batch; empty while the run goes

        """
        _files, _report, _results, _finished = swappRunResults(name).read()

        return _results

    # -----------------------------------------------------------------------

    def give_back(self, name: str) -> None:
        """Give the batch of a run back to the provision of files, as its results say it.

        The batch is released, what was produced is given back, the report
        included online, and that it has finished is said. It is done by the
        request which asks for the results: the copy of the files it works
        on is the one that request carries.

        :param name: (str) Name of the results, without its path
        :raises: ValueError: The name is not the one of the results of a run of Annotate

        """
        _files, _report, _results, _finished = swappRunResults(name).read()
        self.__provision.release(_files)

        _produced = sppasWorkspace()
        for _result in _results:
            for _filename in _result.produced:
                if os.path.isfile(_filename) is True:
                    _produced.add_file(_filename)
        if len(_report) > 0 and os.path.isfile(_report) is True:
            _produced.add_file(_report)
        self.__provision.produced(_produced)
        self.__provision.finished()

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __perform(self, batch, parameters: sppasParam, manager, filenames: list, roots: list,
                  report: str, results: swappRunResults, progress=None) -> None:
        """Have the API execute the annotations, then write the results.

        It is what the process performs, in its thread. The results are
        written whatever the API did: the process ends once they were.

        :param batch: (sppasWorkspace) The workspace the provision of files handed
        :param parameters: (sppasParam) What was decided
        :param manager: (sppasAnnotationsManager) What executes the annotations
        :param filenames: (list of str) The files of the batch, which are locked
        :param roots: (list of str) The roots of the batch, in its order
        :param report: (str) The report to give back with what was produced, empty locally
        :param results: (swappRunResults) Where what came of every root is written
        :param progress: (swappProcessProgress) The progress of the process

        """
        try:
            manager.annotate(parameters, swappAnnotateProgress(progress))
        finally:
            self.__write_results(batch, manager, filenames, roots, report, results)

    # -----------------------------------------------------------------------

    def __write_results(self, batch, manager, filenames: list, roots: list, report: str,
                        results: swappRunResults) -> None:
        """Write what came of every root of the batch, and that the run has ended.

        Each root of the batch is given the files the API wrote under it, a
        file which stood already and was written again included.

        :param batch: (sppasWorkspace) The workspace the provision of files handed
        :param manager: (sppasAnnotationsManager) What executed the annotations
        :param filenames: (list of str) The files of the batch, which are locked
        :param roots: (list of str) The roots of the batch, in its order
        :param report: (str) The report to give back with what was produced, empty locally
        :param results: (swappRunResults) Where what came of every root is written

        """
        # The API added what it wrote to the batch: each written file is
        # found there under its root.
        _written = manager.get_out_files()
        _under = dict()
        for _path in batch.get_paths():
            for _root in _path:
                for _file in _root:
                    if _file.get_id() in _written:
                        _of_root = _under.get(_root.get_id(), list())
                        _of_root.append(_file.get_id())
                        _under[_root.get_id()] = _of_root
        _results = list()
        for _root in roots:
            _results.append(swappRootResult(_root, _under.get(_root, list())))
        results.write(filenames, report, _results, finished=True)
