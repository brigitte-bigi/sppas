"""
:filename: sppas.ui.swapp.app_annotate.annotate_controller.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What reads the task of a request and answers it.

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

from sppas.core.config import annots
from sppas.ui import _
from sppas.core.coreutils import sppasTypeError
from sppas.src.wkps import States

from ..swapp_core.swappsg import swapp_serverstate

from .annotate_record import swappAnnotateRecord
from .annotate_record import LANG_NONE
from .annotate_record import LANG_MIX
from .annotate_view import swappAnnotateView

# ---------------------------------------------------------------------------

MSG_REPORT_UNAVAILABLE = _("The report is not available...\nError is: {:s}")

# ---------------------------------------------------------------------------


class swappAnnotateController:
    """Read the task a request carries, and answer it.

    It is called once per request, and holds nothing afterward.

    """

    def __init__(self, model, view: swappAnnotateView):
        """Create the controller with what it is given.

        :param model: (swappAnnotateModel) The model of Annotate
        :param view: (swappAnnotateView) The view of Annotate
        :raises: sppasTypeError: The given view is not a swappAnnotateView

        """
        if isinstance(view, swappAnnotateView) is False:
            raise sppasTypeError(view, "swappAnnotateView")
        self.__model = model
        self.__view = view
        self.__record = swappAnnotateRecord()

    # -----------------------------------------------------------------------

    def handle(self, events: dict) -> None:
        """Do the task the events of a request ask for.

        :param events: (dict) What a page sent

        """
        self.__record = swappAnnotateRecord()
        self.__record.parse(events)

        # A reset takes the page back to what it was on arrival: nothing of
        # what was transmitted is kept.
        if self.__record.task == "reset":
            self.__record = swappAnnotateRecord()

        # An annotation which can't be performed on that machine is never
        # selected.
        for _key in self.__record.selected:
            if self.__model.can_be_performed(_key) is False:
                self.__record.unselect(_key)

        # The page of the six steps sent the language of the page. When it is
        # not the one of the selected annotations, the person chose it: it is
        # given to every annotation which has resources for it.
        if len(self.__record.lang) > 0 and self.__record.lang != self.__lang_of_selected():
            for _annotation in self.__model.annotations():
                _languages = _annotation.get_langlist()
                if len(_languages) > 0:
                    if self.__record.lang in _languages:
                        self.__record.set_annotation_lang(_annotation.get_key(), self.__record.lang)
                    else:
                        self.__record.set_annotation_lang(_annotation.get_key(), "")

        # The language of the page is the one of the selected annotations.
        self.__record.lang = self.__lang_of_selected()

        # Locally, the checked report is deleted, or every report which is
        # not checked. Those which could not be deleted are said.
        if swapp_serverstate.local is True:
            _names = list()
            if self.__record.task == "delete_checked" and len(self.__record.report) > 0:
                _names.append(self.__record.report)
            elif self.__record.task == "delete_unchecked":
                for _name in self.__model.reports():
                    if _name != self.__record.report:
                        _names.append(_name)
            if len(_names) > 0:
                _left = self.__model.delete_reports(_names)
                if len(_left) > 0:
                    self.__record.show("undeleted", _left)

        # The checked report is one which is kept: a report which is no longer
        # there is no longer checked.
        if (self.__record.report in self.__model.reports()) is False:
            self.__record.report = ""

    # -----------------------------------------------------------------------

    def get_progress_values(self) -> tuple:
        """Get the current progress values.

        :return: (tuple) Percent, Header, Text

        """
        return 100, "", ""

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build its tree from the record.

        What the page shows is asked to the model at every request: the
        annotations of one type when the task asks for them, the six steps
        otherwise, and the reports beside. Online, the view is given no report.

        """
        if self.__record.task.startswith("annotations_") is True:
            _type = self.__record.task[len("annotations_"):]
            _annotations = list()
            _disabled = list()
            for _annotation in self.__model.annotations():
                if _type in _annotation.get_types():
                    _annotations.append(_annotation)
                    if self.__model.can_be_performed(_annotation.get_key()) is False:
                        _disabled.append(_annotation.get_key())
            self.__record.show("type", _type)
            self.__record.show("annotations", _annotations)
            self.__record.show("disabled", _disabled)
        elif self.__record.task == "show":
            try:
                self.__record.show("report", self.__model.read_report(self.__record.report))
            except Exception as e:
                self.__record.show("report", MSG_REPORT_UNAVAILABLE.format(str(e)))
        else:
            self.__record.show("kinds", self.__model.kinds())
            self.__record.show("languages", self.__model.languages())
            self.__record.show("types", annots.types)
            # The types which hold a selected annotation.
            _holding = list()
            for _annotation in self.__model.annotations():
                if _annotation.get_key() in self.__record.selected:
                    for _type in _annotation.get_types():
                        if (_type in _holding) is False:
                            _holding.append(_type)
            self.__record.show("holding", _holding)
            self.__record.show("files", len(self.__model.batch().get_filename_from_state(States().CHECKED)))
        if swapp_serverstate.local is True:
            self.__record.show("reports", self.__model.reports())

        self.__view.populate_tree_content(self.__record)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __lang_of_selected(self) -> str:
        """Return the language of the selected annotations.

        :return: (str) LANG_NONE when none has a language, LANG_MIX when they have several

        """
        _langs = list()
        _annotation_langs = self.__record.annotation_langs
        for _key in self.__record.selected:
            _lang = _annotation_langs.get(_key, "")
            if len(_lang) > 0 and _lang != LANG_NONE and (_lang in _langs) is False:
                _langs.append(_lang)

        if len(_langs) == 0:
            return LANG_NONE
        if len(_langs) == 1:
            return _langs[0]
        return LANG_MIX
