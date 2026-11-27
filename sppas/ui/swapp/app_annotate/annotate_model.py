"""
:filename: sppas.ui.swapp.app_annotate.annotate_model.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Model for the Annotate application.

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

from sppas.core.config import paths

from ..swapp_core.swappsg import swapp_settings
from ..services.files import swappFilesManager

from .annotate_annotations import swappModelAnnotations
from .annotate_reports import swappModelReports
from .annotate_provision import swappModelProvision
from .annotate_run import swappModelRun

# ---------------------------------------------------------------------------


class swappAnnotateModel:
    """Model for the Annotate application.

    The single interface the controller reaches: it makes the models of the
    annotations, of the run, of the reports and of the access to the
    provision of files, and nothing else reaches them.

    """

    def __init__(self, manager: swappFilesManager):
        """Create the model of the Annotate application.

        :param manager: (swappFilesManager) What the response holds of the provision of files
        :raises: sppasTypeError: The given manager is not a swappFilesManager

        """
        self.__annotations = swappModelAnnotations()
        self.__reports = swappModelReports()
        self.__provision = swappModelProvision(manager)
        self.__run = swappModelRun(self.__provision)

    # -----------------------------------------------------------------------

    def start(self, batch, parameters, merge: bool) -> str:
        """Start a run, and return the name of its report.

        It is answered without waiting for the run to end.

        :param batch: (sppasWorkspace) The workspace the provision of files handed
        :param parameters: (sppasParam) What was decided
        :param merge: (bool) One file gathering everything is to be created
        :raises: RuntimeError: A run is going
        :return: (str) Name of the report, without its path

        """
        return self.__run.start(batch, parameters, merge)

    # -----------------------------------------------------------------------

    def is_running(self) -> bool:
        """Return True while a run is going (bool)."""
        return self.__run.is_running()

    # -----------------------------------------------------------------------

    def report_name(self) -> str:
        """Return the name of the report of the run going, empty if none (str)."""
        return self.__run.report_name()

    # -----------------------------------------------------------------------

    def process_name(self) -> str:
        """Return the name of the process of the last run, empty before the first one (str)."""
        return self.__run.process_name()

    # -----------------------------------------------------------------------

    def results(self) -> list:
        """Return what came of every root of the batch of the last run which ended.

        :return: (list of swappRootResult) Empty while a run goes, and before the first one has ended

        """
        return self.__run.results()

    # -----------------------------------------------------------------------

    def address_of(self, filename: str) -> str:
        """Return the address a produced file is reached at.

        :param filename: (str) Name of the produced file, with its path
        :return: (str) Empty when the file is reached at no address

        """
        return self.__provision.address_of(filename)

    # -----------------------------------------------------------------------

    def address_of_all(self, filenames: list) -> str:
        """Return the address of one archive holding the produced files.

        :param filenames: (list of str) Names of the files, with their path
        :return: (str) Empty when no archive is to be made

        """
        return self.__provision.address_of_all(filenames)

    # -----------------------------------------------------------------------

    def batch(self):
        """Return the batch: the workspace the provision of files hands.

        :return: (sppasWorkspace) Can hold no file at all

        """
        return self.__provision.batch()

    # -----------------------------------------------------------------------

    def annotations(self) -> list:
        """Return every annotation the API declares, in the order of the API.

        :return: (list) What each step of the API answers

        """
        return self.__annotations.annotations()

    # -----------------------------------------------------------------------

    def is_installed(self, key: str) -> bool:
        """Return True if the annotation of that key is installed on that machine.

        :param key: (str) Key of an annotation
        :return: (bool)

        """
        return self.__annotations.is_installed(key)

    # -----------------------------------------------------------------------

    def why_not_installed(self, key: str) -> str:
        """Return why the annotation of that key is not installed on that machine.

        :param key: (str) Key of an annotation
        :raises: KeyError: No annotation has that key
        :return: (str) Empty when it is installed

        """
        return self.__annotations.why_not_installed(key)

    # -----------------------------------------------------------------------

    def required_names(self, key: str) -> list:
        """Return the names of the annotations the annotation of that key requires.

        :param key: (str) Key of an annotation
        :raises: KeyError: No annotation has that key
        :return: (list of str) Empty when it requires none

        """
        return self.__annotations.required_names(key)

    # -----------------------------------------------------------------------

    def required_filetypes(self, key: str) -> list:
        """Return the types of file the annotation of that key reads, each once.

        :param key: (str) Key of an annotation
        :raises: KeyError: No annotation has that key
        :return: (list of str)

        """
        return self.__annotations.required_filetypes(key)

    # -----------------------------------------------------------------------

    def kinds(self) -> dict:
        """Return every kind of output file which has at least one extension.

        :return: (dict) key=kind, value=(list of extensions, default extension)

        """
        return self.__annotations.kinds()

    # -----------------------------------------------------------------------

    def language_of_selected(self, parameters) -> str:
        """Return the language the selected annotations hold.

        :param parameters: (sppasParam) What was decided
        :return: (str) LANG_NONE when none has a language, LANG_MIX when they have several

        """
        return self.__annotations.language_of_selected(parameters)

    # -----------------------------------------------------------------------

    def fix_language(self, parameters, lang: str) -> None:
        """Give the language of the page to every annotation which has resources for it.

        :param parameters: (sppasParam) What was decided
        :param lang: (str) The language of the page, LANG_NONE or LANG_MIX

        """
        self.__annotations.fix_language(parameters, lang)

    # -----------------------------------------------------------------------

    def languages(self) -> list:
        """Return every language at least one annotation has resources for, each of them once.

        :return: (list of str)

        """
        return self.__annotations.languages()

    # -----------------------------------------------------------------------

    def reports(self) -> list:
        """Return the names of the reports which are kept, the last one written first.

        :return: (list of str) Empty when there are none, and empty online

        """
        if swapp_settings.served_locally is False:
            return list()

        return self.__reports.reports()

    # -----------------------------------------------------------------------

    def read_report(self, name: str) -> list:
        """Return the lines of a report as they were written, each with the state it bears.

        :param name: (str) Name of the report
        :raises: ValueError: The name is not the one of a report of its folder
        :raises: IOError: The report can't be read
        :return: (list of swappReportLine)

        """
        return self.__reports.read(name, self.__folder_of_reports())

    # -----------------------------------------------------------------------

    def report_path(self, name: str) -> str:
        """Return the name of a report with its path.

        :param name: (str) Name of the report, without its path
        :return: (str) In the folder of the logs locally, beside the files of the batch online

        """
        return os.path.join(self.__folder_of_reports(), name)

    # -----------------------------------------------------------------------

    def delete_reports(self, names: list) -> list:
        """Delete the reports which are named, and nothing else.

        :param names: (list of str) Names of reports
        :return: (dict) key=name of a report which could not be deleted, value=the reason

        """
        return self.__reports.delete(names)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __folder_of_reports(self) -> str:
        """Return the folder the reports stand in.

        :return: (str) The folder of the logs locally, the one of the files of the batch online

        """
        if swapp_settings.served_locally is True:
            return paths.logs

        return self.__provision.folder()
