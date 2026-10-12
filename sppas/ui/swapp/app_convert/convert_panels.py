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
MSG_UNSUPPORTED = _("Not supported by this format: {}.")
MSG_SUPPORTED = _("supported")
MSG_NOT_SUPPORTED = _("not supported")
MSG_COMPARE = _("Compare the formats")
MSG_COMPARE_CAPTION = _("Formats and the properties each supports")
MSG_COLUMNS = _("Columns visibility:")
MSG_TOGGLE_COLUMNS = _("Toggle columns visibility")
MSG_SHOW_HIDE = _("Show/Hide {}")
MSG_APPLY = _("Apply")
MSG_FORMAT = _("Format")
MSG_SOFTWARE = _("Software")
MSG_OVERRIDE = _("Replace an output file that already exists")
MSG_HEURISTIC = _("Guess the format of a file whose extension is unknown")
MSG_CONVERT = _("Convert")
MSG_RESET = _("Reset")
MSG_RESULTS = _("Results")
MSG_RESULTS_CAPTION = _("One line per file of the batch")
MSG_FILE = _("File")
MSG_STATUS = _("Status")
MSG_RESULT = _("Result")
MSG_RESTART = _("Start over")
MSG_STATUSES = {"written": _("written"), "skipped": _("skipped"), "refused": _("refused")}

# The icon which says the status of a file: its shape says it, its text alternative is the word.
STATUS_ICONS = {"written": "yes", "skipped": "warning", "refused": "no"}

# What is shown of each property a format may hold, by its identifier.
MSG_PROPERTIES = {
    "metadata": _("Metadata"),
    "multi_tiers": _("Multi tiers"),
    "no_tiers": _("No tier"),
    "point": _("Point"),
    "interval": _("Interval"),
    "gaps": _("Gaps"),
    "overlaps": _("Overlaps"),
    "hierarchy": _("Hierarchy"),
    "ctrl_vocab": _("Ctrl vocab"),
    "media": _("Media"),
    "radius": _("Vagueness"),
    "alt_localization": _("Alt. loc"),
    "alt_tag": _("Alt. tag"),
    "tag_types": _("Typed tags"),
    "tag_geometry": _("Geom. tags")
}

# The name the page sends the destination under.
FIELD_DESTINATION = "destination"

# The two general options, by the name the page sends them under.
GENERAL_OPTIONS = (("override", MSG_OVERRIDE), ("heuristic", MSG_HEURISTIC))

ID_FORMATS = "convert_formats_h"
ID_DESTINATION = "convert_destination"
ID_RESULTS = "convert_results_h"
ID_COMPARE_OPEN = "convert_compare_open"
ID_COMPARE_DIALOG = "convert_compare_dialog"
ID_COMPARE_COLUMNS = "convert_compare_columns"
ID_COMPARE_APPLY = "convert_compare_apply"
ID_COMPARE_TABLE = "convert_compare_table"

# The form of the conversion: every field of a decision belongs to it.
ID_FORM = "convert_form"

# ---------------------------------------------------------------------------


def property_name(identifier: str) -> str:
    """Return what is shown of a property: its text, or its identifier if it has none.

    :param identifier: (str) Identifier of a property
    :return: (str)

    """
    return MSG_PROPERTIES.get(identifier, identifier)

# ---------------------------------------------------------------------------


def support_icon(parent: str, supported: bool) -> HTMLNode:
    """Return the icon saying whether a property is supported, with its text.

    :param parent: (str) Identifier of the node the icon is appended to
    :param supported: (bool) The property is supported
    :return: (HTMLNode)

    """
    _icon = "no"
    _text = MSG_NOT_SUPPORTED
    if supported is True:
        _icon = "yes"
        _text = MSG_SUPPORTED
    return HTMLNode(parent, None, "span", value="",
                    attributes={"data-icon": _icon, "role": "img", "aria-label": _text})

# ---------------------------------------------------------------------------


def holds_id(extension: str) -> str:
    """Return the identifier of the block which says what reaching a format costs.

    :param extension: (str) Extension of the format, its dot included
    :return: (str)

    """
    return "convert_holds_" + format_name(extension)

# ---------------------------------------------------------------------------


def unsupported_properties(destination) -> list:
    """Return the properties a format does not support, in their order.

    :param destination: (swappFormat) The format
    :return: (list of str) Identifiers of the properties

    """
    _unsupported = list()
    for _identifier in destination.properties:
        if destination.holds(_identifier) is False:
            _unsupported.append(_identifier)
    return _unsupported

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

    A table: the software, then one radio button per format of that
    software. The chosen format is checked. A radio button belongs to the
    form of the conversion, and controls the block of its format when it
    loses something. It carries no property.

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
        _table = TagNode(self.identifier, None, "table", attributes={"aria-labelledby": ID_FORMATS})
        self.append_child(_table)
        _head = TagNode(_table.identifier, None, "thead")
        _table.append_child(_head)
        _tr = TagNode(_head.identifier, None, "tr")
        _head.append_child(_tr)
        _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=MSG_SOFTWARE, attributes={"scope": "col"}))
        _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=MSG_FORMAT, attributes={"scope": "col"}))

        # The formats of one software together, in the order the first of them comes.
        _groups = dict()
        _order = list()
        for _format in formats:
            if (_format.software in _groups) is False:
                _groups[_format.software] = list()
                _order.append(_format.software)
            _groups[_format.software].append(_format)

        for _software in _order:
            _body = TagNode(_table.identifier, None, "tbody")
            _table.append_child(_body)
            _first = True
            for _format in _groups[_software]:
                _tr = TagNode(_body.identifier, None, "tr")
                _body.append_child(_tr)
                if _first is True:
                    _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=_software,
                                              attributes={"scope": "rowgroup",
                                                          "rowspan": str(len(_groups[_software]))}))
                    _first = False
                _td = TagNode(_tr.identifier, None, "td")
                _tr.append_child(_td)
                _id = "convert_dest_" + format_name(_format.extension)
                _attributes = {"type": "radio", "form": ID_FORM, "name": FIELD_DESTINATION, "id": _id,
                               "value": _format.extension}
                if len(unsupported_properties(_format)) > 0:
                    _attributes["aria-controls"] = holds_id(_format.extension)
                if _format.extension.lower() == destination.lower():
                    _attributes["checked"] = None
                _td.append_child(EmptyNode(_td.identifier, None, "input", attributes=_attributes))
                _td.append_child(HTMLNode(_td.identifier, None, "label", value=format_name(_format.extension),
                                          attributes={"for": _id}))

# ---------------------------------------------------------------------------


class swappDestinationPanel(TagNode):
    """What reaching the chosen format costs, beside the table of the formats.

    The column is kept when nothing is shown in it. It holds one block per
    format which loses something: the one of the destination is shown, the
    others are in the page and hidden. What appears in it is announced to a
    screen reader, politely.

    """

    def __init__(self, parent: str, formats: list, destination: str):
        """Create the column, and the block of every format which loses something.

        :param parent: (str) Identifier of the node the panel is appended to
        :param formats: (list of swappFormat) The formats which can be written
        :param destination: (str) Extension of the format chosen

        """
        super(swappDestinationPanel, self).__init__(parent, ID_DESTINATION, "section",
                                                    attributes={"id": ID_DESTINATION,
                                                                "class": "flex-item width_50",
                                                                "aria-live": "polite"})
        for _format in formats:
            _unsupported = unsupported_properties(_format)
            if len(_unsupported) == 0:
                continue
            _attributes = {"id": holds_id(_format.extension)}
            if _format.extension.lower() != destination.lower():
                _attributes["class"] = "hidden"
            _block = TagNode(self.identifier, None, "div", attributes=_attributes)
            self.append_child(_block)
            _names = list()
            for _identifier in _unsupported:
                _names.append(property_name(_identifier))
            _block.append_child(HTMLNode(_block.identifier, None, "p",
                                         value=MSG_UNSUPPORTED.format(", ".join(_names))))

# ---------------------------------------------------------------------------


class swappComparePanel(TagNode):
    """The formats by properties, one against another, in a modal dialog.

    A button opens the dialog. The table sorts on any of its columns, and
    the columns of the properties which are shown are chosen in a list.

    """

    def __init__(self, parent: str, formats: list):
        """Create the panel which compares the formats.

        :param parent: (str) Identifier of the node the panel is appended to
        :param formats: (list of swappFormat) The formats which can be written

        """
        super(swappComparePanel, self).__init__(parent, None, "div")

        self.append_child(HTMLNode(self.identifier, None, "button", value=MSG_COMPARE,
                                   attributes={"type": "button", "id": ID_COMPARE_OPEN,
                                               "aria-haspopup": "dialog", "aria-controls": ID_COMPARE_DIALOG}))

        _dialog = TagNode(self.identifier, ID_COMPARE_DIALOG, "dialog",
                          attributes={"id": ID_COMPARE_DIALOG, "class": "hidden-alert",
                                      "aria-labelledby": ID_COMPARE_DIALOG + "_h"})
        self.append_child(_dialog)
        _dialog.append_child(HTMLNode(_dialog.identifier, None, "h2", value=MSG_COMPARE,
                                      attributes={"id": ID_COMPARE_DIALOG + "_h"}))

        _properties = list()
        if len(formats) > 0:
            _properties = list(formats[0].properties.keys())

        swappComparePanel.__append_columns(_dialog, _properties)
        swappComparePanel.__append_table(_dialog, formats, _properties)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __append_columns(dialog: TagNode, properties: list) -> None:
        """Append the list which chooses the columns shown, and its button.

        :param dialog: (TagNode) The dialog
        :param properties: (list of str) Identifiers of the properties

        """
        _panel = TagNode(dialog.identifier, None, "div", attributes={"class": "flex-panel"})
        dialog.append_child(_panel)

        _details = TagNode(_panel.identifier, ID_COMPARE_COLUMNS, "details",
                           attributes={"id": ID_COMPARE_COLUMNS, "class": "flex-item width_30"})
        _panel.append_child(_details)
        _summary = TagNode(_details.identifier, None, "summary", attributes={"class": "summary-choice"})
        _details.append_child(_summary)
        _summary.append_child(HTMLNode(_summary.identifier, None, "span", value=MSG_COLUMNS))
        _toggle = TagNode(_summary.identifier, None, "button",
                          attributes={"type": "button", "class": "accordion-action", "data-toggle": None,
                                      "aria-label": MSG_TOGGLE_COLUMNS})
        _summary.append_child(_toggle)
        _toggle.append_child(EmptyNode(_toggle.identifier, None, "img", attributes={"src": "", "alt": ""}))

        _div = TagNode(_details.identifier, None, "div")
        _details.append_child(_div)
        _ul = TagNode(_div.identifier, None, "ul")
        _div.append_child(_ul)
        for _identifier in properties:
            _id = "convert_column_" + _identifier
            _li = TagNode(_ul.identifier, None, "li", attributes={"class": "check-item"})
            _ul.append_child(_li)
            _li.append_child(EmptyNode(_li.identifier, None, "input",
                                       attributes={"id": _id, "type": "checkbox", "aria-labelledby": _id + "_l",
                                                   "checked": None, "data-toggle": _identifier}))
            _text = MSG_SHOW_HIDE.format(property_name(_identifier))
            _li.append_child(HTMLNode(_li.identifier, None, "label", value=_text,
                                      attributes={"for": _id, "id": _id + "_l"}))

        _panel.append_child(HTMLNode(_panel.identifier, None, "button", value=MSG_APPLY,
                                     attributes={"type": "button", "class": "flex-item", "id": ID_COMPARE_APPLY}))

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_table(dialog: TagNode, formats: list, properties: list) -> None:
        """Append the table of formats by properties, sortable on each column.

        :param dialog: (TagNode) The dialog
        :param formats: (list of swappFormat) The formats which can be written
        :param properties: (list of str) Identifiers of the properties

        """
        _div = TagNode(dialog.identifier, None, "div", attributes={"class": "scrolled-panel"})
        dialog.append_child(_div)
        _table = TagNode(_div.identifier, ID_COMPARE_TABLE, "table", attributes={"id": ID_COMPARE_TABLE})
        _div.append_child(_table)
        _table.append_child(HTMLNode(_table.identifier, None, "caption", value=MSG_COMPARE_CAPTION))

        _head = TagNode(_table.identifier, None, "thead")
        _table.append_child(_head)
        _tr = TagNode(_head.identifier, None, "tr")
        _head.append_child(_tr)
        _th = TagNode(_tr.identifier, None, "th", attributes={"scope": "col"})
        _tr.append_child(_th)
        _th.append_child(HTMLNode(_th.identifier, None, "button", value=MSG_FORMAT,
                                  attributes={"type": "button", "class": "sortatable", "data-sort": "format"}))
        for _identifier in properties:
            _th = TagNode(_tr.identifier, None, "th", attributes={"scope": "col"})
            _tr.append_child(_th)
            _th.append_child(HTMLNode(_th.identifier, None, "button", value=property_name(_identifier),
                                      attributes={"type": "button", "class": "sortatable",
                                                  "data-sort": _identifier}))

        _body = TagNode(_table.identifier, None, "tbody")
        _table.append_child(_body)
        for _format in formats:
            _tr = TagNode(_body.identifier, None, "tr")
            _body.append_child(_tr)
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=format_name(_format.extension),
                                      attributes={"scope": "row"}))
            for _identifier in properties:
                _supported = _format.holds(_identifier)
                _value = "0"
                if _supported is True:
                    _value = "1"
                _td = TagNode(_tr.identifier, None, "td", attributes={"data-sort-value": _value})
                _tr.append_child(_td)
                _td.append_child(support_icon(_td.identifier, _supported))

# ---------------------------------------------------------------------------


class swappGeneralPanel(TagNode):
    """The general options, and the form of the conversion.

    Every field of a decision belongs to that form, wherever it stands in the
    page: Convert sends them all, and Reset puts them all back.

    """

    def __init__(self, parent: str, override: bool, heuristic: bool):
        """Create the panel of the general options.

        :param parent: (str) Identifier of the node the panel is appended to
        :param override: (bool) An existing output file may be replaced
        :param heuristic: (bool) The format of an unknown extension may be detected

        """
        super(swappGeneralPanel, self).__init__(parent, None, "section")

        _form = TagNode(self.identifier, ID_FORM, "form", attributes={"id": ID_FORM, "method": "post"})
        self.append_child(_form)

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

        _form.append_child(HTMLNode(_form.identifier, None, "button", value=MSG_CONVERT,
                                    attributes={"type": "submit", "class": "cta-button",
                                                "name": EVENT_TASK, "value": TASK_CONVERT}))
        _form.append_child(HTMLNode(_form.identifier, None, "button", value=MSG_RESET,
                                    attributes={"type": "reset"}))

# ---------------------------------------------------------------------------


class swappResultsPanel(TagNode):
    """What came of every file: its status, then what it produced or why not.

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
        for _text in (MSG_FILE, MSG_STATUS, MSG_RESULT):
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=_text, attributes={"scope": "col"}))

        _body = TagNode(_table.identifier, None, "tbody")
        _table.append_child(_body)
        for _result in results:
            _tr = TagNode(_body.identifier, None, "tr")
            _body.append_child(_tr)
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=os.path.basename(_result.file),
                                      attributes={"scope": "row"}))
            _status = TagNode(_tr.identifier, None, "td")
            _tr.append_child(_status)
            _status.append_child(HTMLNode(_status.identifier, None, "span", value="",
                                          attributes={"data-icon": STATUS_ICONS.get(_result.status, "warning"),
                                                      "role": "img",
                                                      "aria-label": MSG_STATUSES.get(_result.status,
                                                                                     _result.status)}))
            if len(_result.produced) > 0:
                _td = TagNode(_tr.identifier, None, "td")
                _tr.append_child(_td)
                _ul = TagNode(_td.identifier, None, "ul")
                _td.append_child(_ul)
                for _produced in _result.produced:
                    _ul.append_child(HTMLNode(_ul.identifier, None, "li", value=os.path.basename(_produced)))
            else:
                _tr.append_child(HTMLNode(_tr.identifier, None, "td", value=_result.cause))

        _form = TagNode(self.identifier, None, "form", attributes={"method": "post"})
        self.append_child(_form)
        _form.append_child(HTMLNode(_form.identifier, None, "button", value=MSG_RESTART,
                                    attributes={"type": "submit", "name": EVENT_TASK, "value": TASK_RESET}))
