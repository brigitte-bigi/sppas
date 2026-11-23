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
from threading import Lock

from sppas.core.coreutils import sppasLogFile
from sppas.src.annotations import sppasAnnotationsManager
from sppas.src.annotations import sppasParam
from sppas.src.wkps import States

from ..nodes import swappProgressBar

from .annotate_provision import swappModelProvision

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


class swappModelRun:
    """Have the API execute the selected annotations.

    It names the report, makes the progress the API says where it stands on,
    locks the batch, and creates a sppasAnnotationsManager, which executes
    the annotations in its own thread, the merge option being given to it.
    It holds that manager and the progress: it says whether the annotations
    are being executed, and where they stand. Once they have been, it
    releases the batch, gives back what was produced, keeps what came of
    every root of the batch, and says it has finished, once. It is the only
    class of this application which has the API execute annotations.

    """

    def __init__(self, provision: swappModelProvision):
        """Create the run, with none going.

        :param provision: (swappModelProvision) The access to the provision of files

        """
        self.__provision = provision
        # It names the report of each run under a name no report
        # bore before.
        self.__log_report = sppasLogFile(pattern="report")
        self.__manager = None
        self.__progress = None
        # The batch which is locked, and its files: given back once.
        self.__batch = None
        self.__filenames = list()
        self.__lock = Lock()
        # The roots of the batch, in its order, and what came of each of
        # them once the run has ended.
        self.__roots = list()
        self.__results = list()

    # -----------------------------------------------------------------------

    def start(self, batch, parameters: sppasParam, merge: bool) -> str:
        """Start a run, and return the name of its report.

        The report is named first, and the name of the next one is prepared
        at once. What was decided is handed to the API as it stands, with the
        workspace and the name of the report.

        :param batch: (sppasWorkspace) The workspace the provision of files handed
        :param parameters: (sppasParam) What was decided
        :param merge: (bool) One file gathering everything is to be created
        :raises: RuntimeError: A run is going
        :return: (str) Name of the report, without its path

        """
        if self.is_running() is True:
            raise RuntimeError("A run is going.")

        _report = self.__log_report.get_filename()
        self.__log_report.increment()
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

        self.__progress = swappProgressBar("annotate_log_panel")
        self.__provision.lock(_filenames)
        self.__batch = batch
        self.__filenames = _filenames
        self.__roots = _roots
        self.__results = list()
        self.__manager = sppasAnnotationsManager(parameters, self.__progress, merge)

        return os.path.basename(_report)

    # -----------------------------------------------------------------------

    def is_running(self) -> bool:
        """Return True while the thread of the manager executes the annotations (bool).

        The first time it is found ended, the batch is given back.

        """
        if self.__manager is None:
            return False
        if self.__manager.is_alive() is True:
            return True

        self.__give_back()
        return False

    # -----------------------------------------------------------------------

    def progress(self) -> tuple:
        """Return where the run stands, as the API set it on the progress.

        Nothing is counted here.

        :return: (tuple) The percent, the header and the text; the hundred when no run is going

        """
        _progress = self.__progress
        if self.is_running() is False or _progress is None:
            return 100, "", ""

        return _progress.get_percent(), _progress.get_header(), _progress.get_text()

    # -----------------------------------------------------------------------

    def results(self) -> list:
        """Return what came of every root of the batch of the last run which ended.

        :return: (list of swappRootResult) In the order of the batch; empty while a run goes, and before the first one has ended

        """
        if self.is_running() is True:
            return list()

        return list(self.__results)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __give_back(self) -> None:
        """Release the batch, give back what was produced, keep the results, and say it has finished.

        Whatever each annotation did, it is done once, the first time the
        annotations are found executed: two requests which find it at the
        same time do not do it twice. Each root of the batch is given the
        files the API wrote under it, a file which stood already and was
        written again included.

        """
        with self.__lock:
            if self.__batch is None:
                return
            self.__provision.release(self.__filenames)
            self.__provision.produced(self.__batch)

            # The API added what it wrote to the batch: each written file is
            # found there under its root.
            _written = self.__manager.get_out_files()
            _under = dict()
            for _path in self.__batch.get_paths():
                for _root in _path:
                    for _file in _root:
                        if _file.get_id() in _written:
                            _of_root = _under.get(_root.get_id(), list())
                            _of_root.append(_file.get_id())
                            _under[_root.get_id()] = _of_root
            _results = list()
            for _root in self.__roots:
                _results.append(swappRootResult(_root, _under.get(_root, list())))
            self.__results = _results
            self.__provision.finished()
            self.__batch = None
            self.__filenames = list()
            self.__roots = list()
            self.__progress = None
