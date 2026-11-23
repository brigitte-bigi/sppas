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

from ..swapp_core.swappsg import swapp_serverstate
from ..services.files import swappFilesManager

from .annotate_annotations import swappModelAnnotations
from .annotate_reports import swappModelReports
from .annotate_provision import swappModelProvision

# ---------------------------------------------------------------------------


class swappAnnotateModel:
    """Model for the Annotate application.

    The single interface the controller reaches: it makes the models of the
    annotations, of the reports and of the access to the provision of files,
    and nothing else reaches them.

    """

    def __init__(self, manager: swappFilesManager):
        """Create the model of the Annotate application.

        :param manager: (swappFilesManager) What the response holds of the provision of files
        :raises: sppasTypeError: The given manager is not a swappFilesManager

        """
        self.__annotations = swappModelAnnotations()
        self.__reports = swappModelReports()
        self.__provision = swappModelProvision(manager)

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

    def can_be_performed(self, key: str) -> bool:
        """Return True if the annotation of that key can be performed on that machine.

        :param key: (str) Key of an annotation
        :return: (bool)

        """
        return self.__annotations.can_be_performed(key)

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
        if swapp_serverstate.local is False:
            return list()

        return self.__reports.reports()

    # -----------------------------------------------------------------------

    def read_report(self, name: str) -> list:
        """Return the lines of a report as they were written, each with the state it bears.

        :param name: (str) Name of the report
        :raises: ValueError: The name is not the one of a report which is kept
        :raises: IOError: The report can't be read
        :return: (list of swappReportLine)

        """
        return self.__reports.read(name)

    # -----------------------------------------------------------------------

    def delete_reports(self, names: list) -> list:
        """Delete the reports which are named, and nothing else.

        :param names: (list of str) Names of reports
        :return: (dict) key=name of a report which could not be deleted, value=the reason

        """
        return self.__reports.delete(names)
