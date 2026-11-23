"""
:filename: sppas.ui.swapp.app_annotate.annotate_reports.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The reports of the annotations which are kept.

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
import codecs

from sppas.core.config import sg
from sppas.core.config import paths
from sppas.ui import _

# ---------------------------------------------------------------------------

# The states a line of a result bears, and the word the API writes for each
# of them at the beginning of that line, in the language of the interface.
REPORT_STATES = (("OK", _("OK")),
                 ("ERROR", _("ERROR")),
                 ("WARNING", _("WARNING")),
                 ("INFO", _("INFO")),
                 ("IGNORED", _("IGNORED")))

# ---------------------------------------------------------------------------


class swappReportLine:
    """One line of a report, as it was written, and the state it bears.

    """

    def __init__(self, text: str, state: str):
        """Create a line of a report.

        :param text: (str) The line, as it was written
        :param state: (str) One of the states of REPORT_STATES, empty if the line states no result

        """
        self.__text = str(text)
        self.__state = str(state)

    # -----------------------------------------------------------------------

    def get_text(self) -> str:
        """Return the line, as it was written (str)."""
        return self.__text

    # -----------------------------------------------------------------------

    def get_state(self) -> str:
        """Return the state the line bears, empty if none (str)."""
        return self.__state

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    text = property(get_text, None)
    state = property(get_state, None)

# ---------------------------------------------------------------------------


class swappModelReports:
    """The reports of the annotations which are kept in the folder of the logs.

    """

    def reports(self) -> list:
        """Return the names of the reports which are kept, the last one written first.

        :return: (list of str) Empty when there are none

        """
        _dated = list()
        for _name in os.listdir(paths.logs):
            _path = os.path.join(paths.logs, _name)
            if os.path.isfile(_path) is True and _name.endswith(".txt") is True and "report" in _name:
                _dated.append((os.path.getmtime(_path), _name))
        _dated.sort(reverse=True)

        _reports = list()
        for _date, _name in _dated:
            _reports.append(_name)

        return _reports

    # -----------------------------------------------------------------------

    def read(self, name: str) -> list:
        """Return the lines of a report as they were written, each with the state it bears.

        Nothing is counted, and nothing is decided from it.

        :param name: (str) Name of the report, one of those which are kept
        :raises: ValueError: The name is not the one of a report which is kept
        :raises: IOError: The report can't be read
        :return: (list of swappReportLine) One per line, in the order of the file

        """
        if (name in self.reports()) is False:
            raise ValueError("{:s} is not a report which is kept.".format(name))

        with codecs.open(os.path.join(paths.logs, name), "r", sg.__encoding__) as fp:
            _content = fp.read()

        _lines = list()
        for _text in _content.splitlines():
            _lines.append(swappReportLine(_text, swappModelReports.__state_of(_text)))

        return _lines

    # -----------------------------------------------------------------------

    def delete(self, names: list) -> list:
        """Delete the reports which are named, each of them on its own.

        A report which can't be deleted does not keep the others from being.
        A name which is not the one of a report which is kept deletes no file.

        :param names: (list of str) Names of reports, without their path
        :return: (dict) key=name of a report which is left, value=the reason

        """
        _reports = self.reports()
        _left = dict()
        for _name in names:
            if (_name in _reports) is True:
                try:
                    os.remove(os.path.join(paths.logs, _name))
                except OSError as e:
                    _left[_name] = str(e)
            else:
                _left[_name] = "It is not a report which is kept."

        return _left

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __state_of(text: str) -> str:
        """Return the state a line of a result bears, empty if the line states no result.

        The word of a state is searched after the first "[ " of the line,
        within 14 characters.

        :param text: (str) One line of a report
        :return: (str)

        """
        _start = text.find("[ ")
        if _start > -1:
            for _state, _word in REPORT_STATES:
                if text.find(_word, _start, _start + 14) > -1:
                    return _state

        return ""
