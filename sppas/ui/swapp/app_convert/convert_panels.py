"""
:filename: sppas.ui.swapp.app_convert.convert_panels.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The panels of the section of the conversion.

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

import os

from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.ui import _

from .convert_record import EVENT_TASK
from .convert_record import TASK_CONVERT
from .convert_record import TASK_RESET

# ---------------------------------------------------------------------------

MSG_WRITE_INTO = _("Write into")
MSG_FORMAT_OF = "{} ({})"
MSG_HOLDS = _("What {} holds")
MSG_HELD = _("held")
MSG_NOT_HELD = _("not held")
MSG_COMPARE = _("Compare the formats")
MSG_COMPARE_CAPTION = _("Formats and the properties each holds")
MSG_FORMAT = _("Format")
MSG_YES = _("yes")
MSG_NO = _("no")
MSG_OVERRIDE = _("Replace an output file that already exists")
MSG_HEURISTIC = _("Guess the format of a file whose extension is unknown")
MSG_CONVERT = _("Convert")
MSG_RESULTS = _("Results")
MSG_RESULTS_CAPTION = _("One line per file written, refused or skipped")
MSG_FILE = _("File")
MSG_STATUS = _("Status")
MSG_REMARKS = _("Remarks")
MSG_NO_REMARK = "—"
MSG_RESTART = _("Start over")
MSG_STATUSES = {"written": _("written"), "skipped": _("skipped"), "refused": _("refused")}

# The name the page sends the destination under.
FIELD_DESTINATION = "destination"

# The two general options, by the name the page sends them under.
GENERAL_OPTIONS = (("override", MSG_OVERRIDE), ("heuristic", MSG_HEURISTIC))

ID_FORMATS = "convert_formats_h"
ID_DESTINATION = "convert_destination_h"
ID_RESULTS = "convert_results_h"

# ---------------------------------------------------------------------------


def format_name(extension: str) -> str:
    """Return the name of a format as the page shows it: its extension, no dot.

    :param extension: (str) Extension of the format, its dot included
    :return: (str)

    """
    return extension.lstrip(".")

# ---------------------------------------------------------------------------


class swappFormatsPanel(TagNode):
    """The formats which can be written, in one list.

    A format is chosen by its radio button, and the chosen one is checked.
    Each line says the format and the software it belongs to. It carries no
    property.

    """

    def __init__(self, parent: str, formats: list, destination: str):
        """Create the panel of the formats.

        :param parent: (str) Identifier of the node the panel is appended to
        :param formats: (list of swappFormat) The formats which can be written
        :param destination: (str) Extension of the chosen format

        """
        super(swappFormatsPanel, self).__init__(parent, None, "section",
                                                attributes={"class": "flex-item width_50",
                                                            "aria-labelledby": ID_FORMATS})

        self.append_child(HTMLNode(self.identifier, None, "h4", value=MSG_WRITE_INTO,
                                   attributes={"id": ID_FORMATS}))
        _form = TagNode(self.identifier, None, "form")
        self.append_child(_form)

        for _format in formats:
            _id = "convert_dest_" + format_name(_format.extension)
            _div = TagNode(_form.identifier, None, "div")
            _form.append_child(_div)
            _attributes = {"type": "radio", "name": FIELD_DESTINATION, "id": _id, "value": _format.extension}
            if _format.extension == destination:
                _attributes["checked"] = None
            _div.append_child(EmptyNode(_div.identifier, None, "input", attributes=_attributes))
            _div.append_child(HTMLNode(_div.identifier, None, "label",
                                       value=MSG_FORMAT_OF.format(format_name(_format.extension), _format.software),
                                       attributes={"for": _id}))

# ---------------------------------------------------------------------------


class swappDestinationPanel(TagNode):
    """What the chosen format holds: every property, always in the same order.

    """

    def __init__(self, parent: str, destination: str, properties: list, held: dict):
        """Create the panel of the destination.

        :param parent: (str) Identifier of the node the panel is appended to
        :param destination: (str) Extension of the chosen format
        :param properties: (list of tuple) The identifier and the text of every property
        :param held: (dict) True or False for every property

        """
        super(swappDestinationPanel, self).__init__(parent, None, "aside",
                                                    attributes={"class": "flex-item width_50",
                                                                "aria-labelledby": ID_DESTINATION})

        self.append_child(HTMLNode(self.identifier, None, "h4",
                                   value=MSG_HOLDS.format(format_name(destination)),
                                   attributes={"id": ID_DESTINATION}))
        _dl = TagNode(self.identifier, None, "dl")
        self.append_child(_dl)
        for _identifier, _text in properties:
            _state = MSG_NOT_HELD
            if held.get(_identifier, False) is True:
                _state = MSG_HELD
            _dl.append_child(HTMLNode(_dl.identifier, None, "dt", value=_text))
            _dl.append_child(HTMLNode(_dl.identifier, None, "dd", value=_state))

# ---------------------------------------------------------------------------


class swappComparePanel(TagNode):
    """The formats by properties, one against another, unfolded in place.

    """

    def __init__(self, parent: str, formats: list, properties: list):
        """Create the panel which compares the formats.

        :param parent: (str) Identifier of the node the panel is appended to
        :param formats: (list of swappFormat) The formats which can be written
        :param properties: (list of tuple) The identifier and the text of every property

        """
        super(swappComparePanel, self).__init__(parent, None, "details")

        self.append_child(HTMLNode(self.identifier, None, "summary", value=MSG_COMPARE))
        _div = TagNode(self.identifier, None, "div", attributes={"class": "scrolled-panel"})
        self.append_child(_div)
        _table = TagNode(_div.identifier, None, "table")
        _div.append_child(_table)
        _table.append_child(HTMLNode(_table.identifier, None, "caption", value=MSG_COMPARE_CAPTION))

        _head = TagNode(_table.identifier, None, "thead")
        _table.append_child(_head)
        _tr = TagNode(_head.identifier, None, "tr")
        _head.append_child(_tr)
        _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=MSG_FORMAT, attributes={"scope": "col"}))
        for _identifier, _text in properties:
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=_text, attributes={"scope": "col"}))

        _body = TagNode(_table.identifier, None, "tbody")
        _table.append_child(_body)
        for _format in formats:
            _tr = TagNode(_body.identifier, None, "tr")
            _body.append_child(_tr)
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=format_name(_format.extension),
                                      attributes={"scope": "row"}))
            for _identifier, _text in properties:
                _state = MSG_NO
                if _format.holds(_identifier) is True:
                    _state = MSG_YES
                _tr.append_child(HTMLNode(_tr.identifier, None, "td", value=_state))

# ---------------------------------------------------------------------------


class swappGeneralPanel(TagNode):
    """The two options which hold for the whole conversion, and what runs it.

    """

    def __init__(self, parent: str, carried: dict, override: bool, heuristic: bool):
        """Create the panel of the general options.

        :param parent: (str) Identifier of the node the panel is appended to
        :param carried: (dict) What was decided, carried by the form as hidden fields
        :param override: (bool) An existing output file may be replaced
        :param heuristic: (bool) The format of an unknown extension may be detected

        """
        super(swappGeneralPanel, self).__init__(parent, None, "section")

        _form = TagNode(self.identifier, None, "form", attributes={"method": "post"})
        self.append_child(_form)
        for _name in carried:
            _form.append_child(EmptyNode(_form.identifier, None, "input",
                                         attributes={"type": "hidden", "name": _name,
                                                     "value": carried[_name]}))

        _values = {"override": override, "heuristic": heuristic}
        for _name, _text in GENERAL_OPTIONS:
            _id = "convert_" + _name
            _p = TagNode(_form.identifier, None, "p")
            _form.append_child(_p)
            _label = TagNode(_p.identifier, None, "label", attributes={"class": "switch", "for": _id})
            _p.append_child(_label)
            _attributes = {"type": "checkbox", "id": _id, "name": _name, "value": "True", "aria-label": _text}
            if _values[_name] is True:
                _attributes["checked"] = None
            _label.append_child(EmptyNode(_label.identifier, None, "input", attributes=_attributes))
            _label.append_child(HTMLNode(_label.identifier, None, "span", value="",
                                         attributes={"class": "switch-slider round switch-no-text"}))
            _p.append_child(HTMLNode(_p.identifier, None, "span", value=_text))

        _p = TagNode(_form.identifier, None, "p")
        _form.append_child(_p)
        _p.append_child(HTMLNode(_p.identifier, None, "button", value=MSG_CONVERT,
                                 attributes={"type": "submit", "class": "cta-button",
                                             "name": EVENT_TASK, "value": TASK_CONVERT}))

# ---------------------------------------------------------------------------


class swappResultsPanel(TagNode):
    """What came of every file of the batch: its status, and its remarks.

    """

    def __init__(self, parent: str, results: list):
        """Create the panel of the results.

        :param parent: (str) Identifier of the node the panel is appended to
        :param results: (list of swappFileResult) One result per file of the batch

        """
        super(swappResultsPanel, self).__init__(parent, None, "section",
                                                attributes={"aria-labelledby": ID_RESULTS})

        self.append_child(HTMLNode(self.identifier, None, "h4", value=MSG_RESULTS,
                                   attributes={"id": ID_RESULTS}))
        _table = TagNode(self.identifier, None, "table")
        self.append_child(_table)
        _table.append_child(HTMLNode(_table.identifier, None, "caption", value=MSG_RESULTS_CAPTION))

        _head = TagNode(_table.identifier, None, "thead")
        _table.append_child(_head)
        _tr = TagNode(_head.identifier, None, "tr")
        _head.append_child(_tr)
        for _text in (MSG_FILE, MSG_STATUS, MSG_REMARKS):
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=_text, attributes={"scope": "col"}))

        _body = TagNode(_table.identifier, None, "tbody")
        _table.append_child(_body)
        for _result in results:
            _tr = TagNode(_body.identifier, None, "tr")
            _body.append_child(_tr)
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=os.path.basename(_result.file),
                                      attributes={"scope": "row"}))
            _tr.append_child(HTMLNode(_tr.identifier, None, "td",
                                      value=MSG_STATUSES.get(_result.status, _result.status)))
            _remarks = _result.cause
            if len(_remarks) == 0:
                _remarks = MSG_NO_REMARK
            _tr.append_child(HTMLNode(_tr.identifier, None, "td", value=_remarks))

        _form = TagNode(self.identifier, None, "form", attributes={"method": "post"})
        self.append_child(_form)
        _p = TagNode(_form.identifier, None, "p")
        _form.append_child(_p)
        _p.append_child(HTMLNode(_p.identifier, None, "button", value=MSG_RESTART,
                                 attributes={"type": "submit", "class": "apply-button",
                                             "name": EVENT_TASK, "value": TASK_RESET}))
