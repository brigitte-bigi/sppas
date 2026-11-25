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
from ..services.options import swappOptionsManager

from .annotate_record import swappAnnotateRecord
from .annotate_view import swappAnnotateView

# ---------------------------------------------------------------------------

MSG_REPORT_UNAVAILABLE = _("The report is not available...\nError is: {:s}")

# ---------------------------------------------------------------------------

# The types of the annotations which cannot be performed online.
NOT_ONLINE_TYPES = ("SPEAKER", "INTERACTION")

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
        self.__options = None
        self.__starts_over = False

    # -----------------------------------------------------------------------

    def handle(self, events: dict) -> None:
        """Do the task the events of a request ask for.

        :param events: (dict) What a page sent

        """
        self.__record = swappAnnotateRecord()
        self.__record.parse(events)

        # An annotation which can't be performed on that machine is never
        # selected.
        for _key in self.__record.selected:
            if self.__model.is_installed(_key) is False:
                self.__record.unselect(_key)

        # The page of the six steps sends the language of the page: a
        # gesture, which the model gives to the annotations.
        if isinstance(events.get("annotate_lang"), str) is True:
            self.__model.fix_language(self.__record.parameters, events["annotate_lang"])

        # The options of one annotation are handed to the service of the
        # options, which shows and checks them. Their values are taken back
        # when she applies them, and stay what they were when she gives up.
        if self.__record.task.startswith("annotate_options_") is True:
            _key = self.__record.task[len("annotate_options_"):]
            self.__options = swappOptionsManager("annotate_options_" + _key, self.__record.get_options(_key))
            self.__options.consumes(events)
            if "options_validate" in events:
                self.__record.set_options(_key, self.__options.options_for_app())

        # One run at a time: while one goes, nothing starts another,
        # resets the page or asks for another batch, and it is said.
        self.__starts_over = False
        if self.__model.is_running() is True and \
                self.__record.task in ("annotate_perform", "annotate_reset", "annotate_steps"):
            self.__record.show("going", True)

        # A reset takes the page back to what it was on arrival: nothing of
        # what was transmitted is kept, and the provision of files starts over.
        elif self.__record.task == "annotate_reset":
            self.__record = swappAnnotateRecord()
            self.__starts_over = True

        # Coming back to the six steps once a run has ended is asking
        # for another batch: the decisions are kept, and the provision of
        # files starts over.
        elif self.__record.task == "annotate_steps" and len(self.__record.followed) > 0:
            self.__record.followed = ""
            self.__starts_over = True

        # The annotations are performed with at least one selected and a
        # batch which is not empty; what is missing is said otherwise.
        elif self.__record.task == "annotate_perform":
            _batch = self.__model.batch()
            _missing = self.__record.what_is_missing(_batch)
            if len(_missing) > 0:
                self.__record.show("missing", _missing)
            else:
                self.__record.followed = self.__model.start(_batch, self.__record.parameters, self.__record.merge)

        # Once the annotations have been performed, the report of that
        # run is the one which is checked, and what came of every root of
        # the batch is shown.
        elif self.__record.task == "annotate_complete":
            self.__record.report = self.__record.followed
            self.__show_results()

        # Locally, the checked report is deleted, or every report which is
        # not checked. Those which could not be deleted are said.
        if swapp_serverstate.local is True:
            _names = list()
            if self.__record.task == "annotate_delete_checked" and len(self.__record.report) > 0:
                _names.append(self.__record.report)
            elif self.__record.task == "annotate_delete_unchecked":
                for _name in self.__model.reports():
                    if _name != self.__record.report:
                        _names.append(_name)
            if len(_names) > 0:
                _left = self.__model.delete_reports(_names)
                if len(_left) > 0:
                    self.__record.show("undeleted", _left)

            # The checked report is one which is kept: a report which is no
            # longer there is no longer checked. Online, no report is kept:
            # the report is the one of the run which has ended.
            if (self.__record.report in self.__model.reports()) is False:
                self.__record.report = ""

    # -----------------------------------------------------------------------

    def followed_report(self) -> list:
        """Return the lines of the report of the run the page follows, as they are written.

        What is not written yet is not there to be read.

        :return: (list of swappReportLine) Empty when nothing is written yet

        """
        try:
            return self.__model.read_report(self.__record.followed)
        except (ValueError, IOError):
            return list()

    # -----------------------------------------------------------------------

    def say_not_performed(self) -> None:
        """Have it said that the annotations could not be performed: what was asked raised."""
        self.__record.show("not_performed", True)

    # -----------------------------------------------------------------------

    def starts_over(self) -> bool:
        """Return True if the provision of files is to start over: a reset, or another batch (bool)."""
        return self.__starts_over

    # -----------------------------------------------------------------------

    def populate_view(self) -> None:
        """Have the view build its tree from the record.

        What the page shows is asked to the model at every request: the
        progress while a run goes; the annotations of one type when
        the task asks for them, with the options of one of them when it is
        configured; the report once the annotations have been performed, or
        when it is asked for; the six steps otherwise, and the reports beside.
        Online, the view is given no report.

        """
        _type = ""
        if self.__record.task.startswith("annotate_annotations_") is True:
            _type = self.__record.task[len("annotate_annotations_"):]
        elif self.__record.task.startswith("annotate_options_") is True:
            # The options of an annotation are shown in its dialog, on the
            # page of the annotations of its first type.
            _key = self.__record.task[len("annotate_options_"):]
            for _annotation in self.__model.annotations():
                if _annotation.get_key() == _key:
                    _type = _annotation.get_types()[0]
            self.__record.show("configured", _key)
            self.__record.show("options", self.__options.container())

        # The run which is going is the one the page follows, whatever the
        # page transmitted: the server holds it.
        if self.__model.is_running() is True:
            self.__record.followed = self.__model.report_name()

        # While the annotations are performed, the page shows the progress,
        # and the report under it as it fills: what is not written yet is
        # not there to be read.
        if self.__model.is_running() is True or \
                (self.__record.task == "annotate_perform" and len(self.__record.followed) > 0):
            self.__record.show("running", True)
            self.__record.show("process", self.__model.process_name())
            self.__record.show("report", self.followed_report())
        elif len(_type) > 0:
            _annotations = list()
            _disabled = list()
            _reasons = dict()
            _required = dict()
            _filetypes = dict()
            for _annotation in self.__model.annotations():
                if _type in _annotation.get_types():
                    _key = _annotation.get_key()
                    _annotations.append(_annotation)
                    # An annotation which can't be performed on that machine
                    # says why, and nothing of what it requires.
                    _why = self.__model.why_not_installed(_key)
                    if len(_why) > 0:
                        _disabled.append(_key)
                        _reasons[_key] = _why
                    else:
                        _required[_key] = self.__model.required_names(_key)
                        _filetypes[_key] = self.__model.required_filetypes(_key)
            self.__record.show("type", _type)
            self.__record.show("annotations", _annotations)
            self.__record.show("disabled", _disabled)
            self.__record.show("reasons", _reasons)
            self.__record.show("required", _required)
            self.__record.show("filetypes", _filetypes)
        elif self.__record.task in ("annotate_show", "annotate_complete"):
            try:
                self.__record.show("report", self.__model.read_report(self.__record.report))
            except Exception as e:
                self.__record.show("report", list())
                self.__record.show("unavailable", MSG_REPORT_UNAVAILABLE.format(str(e)))
        else:
            self.__record.show("kinds", self.__model.kinds())
            self.__record.show("languages", self.__model.languages())
            self.__record.show("lang", self.__model.language_of_selected(self.__record.parameters))
            self.__record.show("types", annots.types)
            # Online, the annotations of some types cannot be performed: these
            # types are disabled.
            _disabled_types = list()
            if swapp_serverstate.local is False:
                _disabled_types = list(NOT_ONLINE_TYPES)
            self.__record.show("disabled_types", _disabled_types)
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

    def __show_results(self) -> None:
        """Show what came of every root of the batch, and where each produced file is reached."""
        _results = self.__model.results()
        self.__record.show("results", _results)

        # Where the person is not on the machine which wrote them, each
        # produced file is reached at an address: the page leads to it.
        _addresses = dict()
        _all = list()
        for _result in _results:
            for _produced in _result.produced:
                _address = self.__model.address_of(_produced)
                if len(_address) > 0:
                    _addresses[_produced] = _address
                _all.append(_produced)
        self.__record.show("addresses", _addresses)

        # Online, the report stands with the produced files: it is reached at
        # an address of its own, and the archive holds it with them.
        _report = self.__model.report_path(self.__record.report)
        _report_address = self.__model.address_of(_report)
        if len(_report_address) > 0:
            self.__record.show("report_address", _report_address)
            _all.append(_report)

        # Ten files are got back in one gesture and not in ten: they are
        # gathered in one archive, which is reached like any of them.
        if len(_addresses) > 0:
            self.__record.show("archive", self.__model.address_of_all(_all))
