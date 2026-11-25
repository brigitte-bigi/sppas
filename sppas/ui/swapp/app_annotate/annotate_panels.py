"""
:filename: sppas.ui.swapp.app_annotate.annotate_panels.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The panels of the page of Annotate.

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
import html
import os

from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.ui import _

from ..nodes import swappProgressBar

from .annotate_annotations import LANG_NONE
from .annotate_annotations import LANG_MIX

# ---------------------------------------------------------------------------

MSG_STEP_FORMAT = _("Choose the output file format(s)")
MSG_STEP_LANG = _("Fix the language(s)")
MSG_STEP_ANNCHOICE = _("Select and configure annotations")
MSG_STEP_FILES = _("Add files")
MSG_STEP_RUN = _("Perform the annotations")
MSG_STEP_REPORT = _("Read the procedure outcome report")
MSG_TYPE = _("{:s} annotations")
MSG_TYPE_NONE = _("no annotation selected")
MSG_FILES_STATE = _("{:d} files selected")
MSG_FILES_CHOOSE = _("Choose the files")
MSG_MERGE = _("Create -merge files")
MSG_BTN_RUN = _("Let's go!")
MSG_RUN_MISSING = _("No annotation is selected.")
MSG_BTN_REPORT = _("Show report")
MSG_REPORT_MISSING = _("No report is checked.")
MSG_RESET = _("Reset")
MSG_REPORTS = _("Reports:")
MSG_DEL_CHECKED = _("Del checked")
MSG_DEL_ALL = _("Del all")
MSG_BACK = _("Back")
MSG_SELECT_TYPE = _("Select annotations of type {:s}")
MSG_CONFIGURE = _("Configure...")
MSG_DEVEL = _("Development")
MSG_DISABLED = _("Not installed on this machine.")
MSG_REQUIRED_FILES = _("Required files")
MSG_REQUIRED_ANNOTATION = _("Required annotation")
MSG_REQUIRED_ANNOTATIONS = _("Required annotations")

# What a person reads of each type of file an annotation reads.
MSG_FILETYPES = {"AUDIO": _("audio"),
                 "VIDEO": _("video"),
                 "IMAGE": _("image"),
                 "ANNOT": _("annotated file"),
                 "ANNOT_ANNOT": _("annotated file"),
                 "ANNOT_MEASURE": _("measure file")}
MSG_LANG_OF = _("Language of {:s}")
MSG_OPTIONS_OF = _("Options of {:s}")
MSG_OPTIONS = _("Options")
MSG_FILES_TITLE = _("Add files")
MSG_LOG_TITLE = _("Procedure outcome report")
MSG_PROGRESS = _("Progress:")
MSG_REPORT_FILE = _("Report file:")
MSG_RESULTS = _("Results")
MSG_RESULTS_CAPTION = _("One line per root of the batch")
MSG_ROOT = _("Root")
MSG_STATUS = _("Status")
MSG_RESULT = _("Result")
MSG_DOWNLOAD_ALL = _("Download all the files")
MSG_STATUSES = {"written": _("written"), "refused": _("refused")}

# The icon which says the status of a root: its shape says it, its text alternative is the word.
STATUS_ICONS = {"written": "yes", "refused": "no"}

# The class of the line of each state a line of a report bears.
STATE_CLASSES = {"OK": "ok",
                 "ERROR": "error",
                 "WARNING": "warning",
                 "INFO": "info",
                 "IGNORED": "ignore"}

# ---------------------------------------------------------------------------


def append_head(panel: TagNode, title_id: str, title: str, available: bool = True) -> None:
    """Append the button which comes back to the six steps, and the title of a panel.

    :param panel: (TagNode) The panel
    :param title_id: (str) Identifier of the title
    :param title: (str) The title
    :param available: (bool) The way back is available; it is offered and not available otherwise

    """
    _head = TagNode(panel.identifier, None, "div", attributes={"class": "annotate-head"})
    panel.append_child(_head)
    _attributes = {"type": "submit", "form": "annotate_form", "name": "event_bake",
                   "value": "annotate_steps", "data-icon": "arrow-up"}
    if available is False:
        _attributes["disabled"] = None
    _back = TagNode(_head.identifier, None, "button", attributes=_attributes)
    _head.append_child(_back)
    _back.append_child(HTMLNode(_back.identifier, None, "span", value=MSG_BACK))
    _head.append_child(HTMLNode(_head.identifier, None, "h3", value=title, attributes={"id": title_id}))

# ---------------------------------------------------------------------------


class swappActionAnnotatePanel(TagNode):
    """The six steps, in their order and with their titles, and the Reset button.

    Every field belongs to the form of the run, which the view
    writes first: a field is tied to it by its attribute "form".

    """

    def __init__(self, parent: str, kinds: dict, extensions: dict, languages: list, lang: str,
                 types: list, holding: list, disabled_types: list, files: int, merge: bool, selected: list,
                 report: str, beside: bool):
        """Create the panel of the steps.

        :param parent: (str) Identifier of the node the panel is appended to
        :param kinds: (dict) key=kind, value=(list of extensions, default extension)
        :param extensions: (dict) The extension chosen for each kind
        :param languages: (list of str) The languages the annotations have resources for
        :param lang: (str) The language chosen for the page, empty if none
        :param types: (list of str) The types of the annotations
        :param holding: (list of str) The types which hold a selected annotation
        :param disabled_types: (list of str) The types whose annotations cannot be performed
        :param files: (int) Number of files selected
        :param merge: (bool) The merge option is checked
        :param selected: (list of str) The keys of the selected annotations
        :param report: (str) The name of the checked report, empty if none
        :param beside: (bool) The panel of the reports is shown beside this one

        """
        _class = "width_70 annotate-steps"
        if beside is False:
            _class = "width_full annotate-steps"
        super(swappActionAnnotatePanel, self).__init__(parent, None, "section",
                                                       attributes={"id": "annotate_actions_panel",
                                                                   "class": _class})

        _steps = TagNode(self.identifier, None, "ol", attributes={"class": "enumerate-cards"})
        self.append_child(_steps)
        swappActionAnnotatePanel.__append_formats(_steps, kinds, extensions)
        swappActionAnnotatePanel.__append_languages(_steps, languages, lang)
        swappActionAnnotatePanel.__append_types(_steps, types, holding, disabled_types)
        swappActionAnnotatePanel.__append_files(_steps, files)
        swappActionAnnotatePanel.__append_run(_steps, merge, len(selected) > 0)
        swappActionAnnotatePanel.__append_report(_steps, len(report) > 0)

        _p = TagNode(self.identifier, None, "p")
        self.append_child(_p)
        _p.append_child(HTMLNode(_p.identifier, None, "button", value=MSG_RESET,
                                 attributes={"type": "submit", "form": "annotate_form",
                                             "name": "event_bake", "value": "annotate_reset"}))

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __append_step(steps: TagNode, number: int, title: str) -> TagNode:
        """Append one step with its title, and return it.

        :param steps: (TagNode) The list of the steps
        :param number: (int) Number of the step, from 1
        :param title: (str) Title of the step
        :return: (TagNode) The item of the step

        """
        _item = TagNode(steps.identifier, None, "li", attributes={"class": "enumerate-cards-item"})
        steps.append_child(_item)
        _item.append_child(HTMLNode(_item.identifier, None, "p", value=title,
                                    attributes={"id": "annotate_step{:d}_h".format(number)}))
        return _item

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_button(parent: TagNode, value: str, text: str, attributes: dict) -> TagNode:
        """Append a button of the form, its text in a span, and return it.

        :param parent: (TagNode) The node the button is appended to
        :param value: (str) The task the button sends
        :param text: (str) The text of the button
        :param attributes: (dict) The other attributes of the button
        :return: (TagNode) The button

        """
        _attributes = {"type": "submit", "form": "annotate_form", "name": "event_bake", "value": value}
        for _key in attributes:
            _attributes[_key] = attributes[_key]
        _button = TagNode(parent.identifier, None, "button", attributes=_attributes)
        parent.append_child(_button)
        _button.append_child(HTMLNode(_button.identifier, None, "span", value=text))
        return _button

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_formats(steps: TagNode, kinds: dict, extensions: dict) -> None:
        """Step 1: one choice per kind of output file, the chosen extension selected."""
        _item = swappActionAnnotatePanel.__append_step(steps, 1, MSG_STEP_FORMAT)
        _group = TagNode(_item.identifier, None, "div",
                         attributes={"role": "group", "aria-labelledby": "annotate_step1_h"})
        _item.append_child(_group)
        _wrap = TagNode(_group.identifier, None, "div", attributes={"class": "wrap-panel width_full"})
        _group.append_child(_wrap)

        for _kind in kinds:
            _extensions, _default = kinds[_kind]
            _chosen = extensions.get(_kind, _default)
            _span = TagNode(_wrap.identifier, None, "span", attributes={"class": "wrap-item width_50"})
            _wrap.append_child(_span)
            _select = TagNode(_span.identifier, None, "select",
                              attributes={"id": "annotate_ext_" + _kind, "name": "annotate_ext_" + _kind,
                                          "form": "annotate_form", "aria-label": _kind})
            _span.append_child(_select)
            for _extension in _extensions:
                _attributes = {"value": _extension}
                if _extension == _chosen:
                    _attributes["selected"] = None
                _select.append_child(HTMLNode(_select.identifier, None, "option", value=_extension,
                                              attributes=_attributes))

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_languages(steps: TagNode, languages: list, lang: str) -> None:
        """Step 2: the choice of the language of the page, the chosen one selected."""
        _item = swappActionAnnotatePanel.__append_step(steps, 2, MSG_STEP_LANG)
        _div = TagNode(_item.identifier, None, "div")
        _item.append_child(_div)
        _span = TagNode(_div.identifier, None, "span", attributes={"class": "wrap-item"})
        _div.append_child(_span)
        _select = TagNode(_span.identifier, None, "select",
                          attributes={"id": "annotate_lang", "name": "annotate_lang",
                                      "form": "annotate_form", "aria-labelledby": "annotate_step2_h"})
        _span.append_child(_select)

        _choices = list(languages)
        _choices.append(LANG_NONE)
        if lang == LANG_MIX:
            _choices.append(LANG_MIX)
        _selected = lang
        if len(_selected) == 0:
            _selected = LANG_NONE
        for _lang in sorted(_choices):
            _attributes = {"value": _lang}
            if _lang == _selected:
                _attributes["selected"] = None
            _select.append_child(HTMLNode(_select.identifier, None, "option", value=_lang,
                                          attributes=_attributes))

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_types(steps: TagNode, types: list, holding: list, disabled_types: list) -> None:
        """Step 3: one button per type, saying when it holds no selected annotation, and disabled when its annotations cannot be performed."""
        _item = swappActionAnnotatePanel.__append_step(steps, 3, MSG_STEP_ANNCHOICE)
        _group = TagNode(_item.identifier, None, "div",
                         attributes={"role": "group", "aria-labelledby": "annotate_step3_h"})
        _item.append_child(_group)

        for _type in types:
            _attributes = {"type": "submit", "form": "annotate_form", "name": "event_bake",
                           "value": "annotate_annotations_" + _type, "class": "width_full",
                           "id": "annotate_type_" + _type}
            if _type in disabled_types:
                _attributes["disabled"] = None
            _button = TagNode(_group.identifier, None, "button", attributes=_attributes)
            _group.append_child(_button)
            if (_type in holding) is False:
                _button.append_child(HTMLNode(_button.identifier, None, "span",
                                              attributes={"data-icon": "no", "role": "img",
                                                          "aria-label": MSG_TYPE_NONE}))
            _button.append_child(HTMLNode(_button.identifier, None, "span", value=MSG_TYPE.format(_type)))

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_files(steps: TagNode, files: int) -> None:
        """Step 4: how many files are selected, and the way to choose them."""
        _item = swappActionAnnotatePanel.__append_step(steps, 4, MSG_STEP_FILES)
        _group = TagNode(_item.identifier, None, "div",
                         attributes={"role": "group", "aria-labelledby": "annotate_step4_h"})
        _item.append_child(_group)
        _group.append_child(HTMLNode(_group.identifier, None, "p", value=MSG_FILES_STATE.format(files),
                                     attributes={"id": "annotate_files_state"}))
        swappActionAnnotatePanel.__append_button(_group, "annotate_files", MSG_FILES_CHOOSE, {"class": "width_full"})

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_run(steps: TagNode, merge: bool, selected: bool) -> None:
        """Step 5: the merge option, and the button which performs, disabled when no annotation is selected."""
        _item = swappActionAnnotatePanel.__append_step(steps, 5, MSG_STEP_RUN)
        _group = TagNode(_item.identifier, None, "div",
                         attributes={"role": "group", "aria-labelledby": "annotate_step5_h"})
        _item.append_child(_group)

        _p = TagNode(_group.identifier, None, "p")
        _group.append_child(_p)
        _attributes = {"type": "checkbox", "id": "annotate_merge", "name": "annotate_merge",
                       "value": "True", "form": "annotate_form"}
        if merge is True:
            _attributes["checked"] = None
        _p.append_child(EmptyNode(_p.identifier, None, "input", attributes=_attributes))
        _p.append_child(HTMLNode(_p.identifier, None, "label", value=MSG_MERGE,
                                 attributes={"for": "annotate_merge"}))

        if selected is True:
            swappActionAnnotatePanel.__append_button(_group, "annotate_perform", MSG_BTN_RUN,
                                                     {"class": "action-button width_full", "data-icon": "play"})
        else:
            swappActionAnnotatePanel.__append_button(_group, "annotate_perform", MSG_BTN_RUN,
                                                     {"class": "action-button width_full", "disabled": None,
                                                      "aria-describedby": "annotate_perform_state",
                                                      "data-icon": "play"})
            _group.append_child(HTMLNode(_group.identifier, None, "p", value=MSG_RUN_MISSING,
                                         attributes={"id": "annotate_perform_state", "class": "annotate-missing"}))

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_report(steps: TagNode, checked: bool) -> None:
        """Step 6: the button which shows the checked report, disabled when no report is checked."""
        _item = swappActionAnnotatePanel.__append_step(steps, 6, MSG_STEP_REPORT)
        _group = TagNode(_item.identifier, None, "div",
                         attributes={"role": "group", "aria-labelledby": "annotate_step6_h"})
        _item.append_child(_group)

        if checked is True:
            swappActionAnnotatePanel.__append_button(_group, "annotate_show", MSG_BTN_REPORT,
                                                     {"class": "action-button width_full", "data-icon": "file"})
        else:
            swappActionAnnotatePanel.__append_button(_group, "annotate_show", MSG_BTN_REPORT,
                                                     {"class": "action-button width_full", "disabled": None,
                                                      "aria-describedby": "annotate_show_state",
                                                      "data-icon": "file"})

        # What says no report is checked is always written, and hidden when
        # one is: checking a report in the page makes no request.
        _class = "annotate-missing"
        if checked is True:
            _class = "annotate-missing hidden"
        _group.append_child(HTMLNode(_group.identifier, None, "p", value=MSG_REPORT_MISSING,
                                     attributes={"id": "annotate_show_state", "class": _class}))

# ---------------------------------------------------------------------------


class swappReportsPanel(TagNode):
    """The reports which are kept, one of them checked at most, and the two buttons which delete.

    Online, there is no list of reports: the panel is collapsed, and holds
    its title only.

    """

    def __init__(self, parent: str, reports: list, checked: str, local: bool):
        """Create the panel of the reports.

        :param parent: (str) Identifier of the node the panel is appended to
        :param reports: (list of str) The names of the reports, the last one written first
        :param checked: (str) The name of the checked report, empty if none
        :param local: (bool) The server is the local one

        """
        _class = "width_30"
        if local is False:
            _class = "width_30 hidden"
        super(swappReportsPanel, self).__init__(parent, None, "section",
                                                attributes={"id": "annotate_reports_panel", "class": _class})
        self.append_child(HTMLNode(self.identifier, None, "h3", value=MSG_REPORTS,
                                   attributes={"id": "annotate_reports_h"}))
        if local is False:
            return

        _p = TagNode(self.identifier, None, "p")
        self.append_child(_p)
        for _value, _icon, _text in (("annotate_delete_checked", "delete-checked", MSG_DEL_CHECKED),
                                     ("annotate_delete_unchecked", "delete-unchecked", MSG_DEL_ALL)):
            _button = TagNode(_p.identifier, None, "button",
                              attributes={"type": "submit", "form": "annotate_form", "name": "event_bake",
                                          "value": _value, "data-icon": _icon})
            _p.append_child(_button)
            _button.append_child(HTMLNode(_button.identifier, None, "span", value=_text))

        _list = TagNode(self.identifier, None, "ul",
                        attributes={"class": "annotate-reports", "role": "radiogroup",
                                    "aria-labelledby": "annotate_reports_h"})
        self.append_child(_list)
        _number = 0
        for _name in reports:
            _number = _number + 1
            _id = "annotate_report_{:d}".format(_number)
            _li = TagNode(_list.identifier, None, "li")
            _list.append_child(_li)
            _attributes = {"type": "radio", "id": _id, "name": "annotate_report",
                           "value": _name, "form": "annotate_form"}
            if _name == checked:
                _attributes["checked"] = None
            _li.append_child(EmptyNode(_li.identifier, None, "input", attributes=_attributes))
            _li.append_child(HTMLNode(_li.identifier, None, "label", value=_name, attributes={"for": _id}))

# ---------------------------------------------------------------------------


class swappAnnotationsPanel(TagNode):
    """The annotations of one type, and the button which comes back to the six steps.

    One item per annotation: what selects it, with its name, and what
    configures it; its references, or the gauge of its development when it
    has none; the choice of its language, when it has language resources;
    its description, then the files and the annotations it requires, or why
    it is not installed. The
    options of an annotation are in a dialog of their
    own: they need the width of the page, which a column of the list cannot
    give them. An annotation which can't be performed on that machine is
    shown, disabled: nothing of it can be set.

    """

    def __init__(self, parent: str, ann_type: str, annotations: list, selected: list, langs: dict,
                 disabled: list, reasons: dict, required: dict, filetypes: dict, configured: str,
                 options: TagNode | None):
        """Create the panel of the annotations of one type.

        :param parent: (str) Identifier of the node the panel is appended to
        :param ann_type: (str) The type of the annotations
        :param annotations: (list) What each step of the API answers, for the annotations of that type
        :param selected: (list of str) The keys of the selected annotations
        :param langs: (dict) The language chosen for each annotation, by its key
        :param disabled: (list of str) The keys of the annotations which can't be performed on that machine
        :param reasons: (dict) Why each one which can't be performed is not installed, by its key
        :param required: (dict) The names of the annotations each one requires, by its key
        :param filetypes: (dict) The types of file each one reads, by its key
        :param configured: (str) The key of the annotation which is configured, empty if none
        :param options: (TagNode) The container of the service of the options for that annotation, None if none

        """
        _title_id = "annotate_{:s}_h".format(ann_type.lower())
        super(swappAnnotationsPanel, self).__init__(parent, None, "section",
                                                    attributes={"id": "annotate_annotations_panel",
                                                                "class": "annotate-annotations",
                                                                "aria-labelledby": _title_id})
        append_head(self, _title_id, MSG_SELECT_TYPE.format(ann_type))

        _list = TagNode(self.identifier, None, "ul")
        self.append_child(_list)
        for _annotation in annotations:
            _key = _annotation.get_key()
            swappAnnotationsPanel.__append_annotation(_list, _annotation, _key in selected, langs.get(_key, ""),
                                                      _key in disabled, reasons.get(_key, ""),
                                                      required.get(_key, list()), filetypes.get(_key, list()))

        for _annotation in annotations:
            if _annotation.get_key() == configured:
                swappAnnotationsPanel.__append_options(self, _annotation, options)
            else:
                swappAnnotationsPanel.__append_options(self, _annotation, None)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __append_annotation(parent: TagNode, annotation, selected: bool, lang: str, disabled: bool,
                            reason: str, required: list, filetypes: list) -> None:
        """Append the item of one annotation.

        :param parent: (TagNode) The list of the annotations
        :param annotation: What the step of the API answers
        :param selected: (bool) The annotation is selected
        :param lang: (str) The language chosen for it, empty if none
        :param disabled: (bool) The annotation can't be performed on that machine
        :param reason: (str) Why it is not installed, empty if it is
        :param required: (list of str) The names of the annotations it requires
        :param filetypes: (list of str) The types of file it reads

        """
        _key = annotation.get_key()
        _name = annotation.get_name()
        _item = TagNode(parent.identifier, None, "li")
        parent.append_child(_item)
        _flex = TagNode(_item.identifier, None, "div", attributes={"class": "flex-panel"})
        _item.append_child(_flex)

        # What selects it, with its name, and what configures it.
        _column = TagNode(_flex.identifier, None, "div", attributes={"class": "flex-item width_25"})
        _flex.append_child(_column)
        _p = TagNode(_column.identifier, None, "p", attributes={"class": "annotate-ann-name"})
        _column.append_child(_p)
        _switch = TagNode(_p.identifier, None, "label", attributes={"class": "switch", "for": "annotate_ann_" + _key})
        _p.append_child(_switch)
        _attributes = {"type": "checkbox", "role": "switch", "id": "annotate_ann_" + _key,
                       "name": "annotate_ann_" + _key, "value": "True", "form": "annotate_form"}
        if selected is True:
            _attributes["checked"] = None
        if disabled is True:
            _attributes["disabled"] = None
        _switch.append_child(EmptyNode(_switch.identifier, None, "input", attributes=_attributes))
        _switch.append_child(HTMLNode(_switch.identifier, None, "span",
                                      attributes={"class": "switch-slider switch-no-text round"}))
        _p.append_child(HTMLNode(_p.identifier, None, "label", value=_name,
                                 attributes={"for": "annotate_ann_" + _key, "id": "annotate_name_" + _key}))
        _p = TagNode(_column.identifier, None, "p")
        _column.append_child(_p)
        _attributes = {"type": "submit", "form": "annotate_form", "name": "event_bake",
                       "value": "annotate_options_" + _key,
                       "class": "text-reveal-button", "data-icon": "parameters"}
        if disabled is True:
            _attributes["disabled"] = None
        _button = TagNode(_p.identifier, None, "button", attributes=_attributes)
        _p.append_child(_button)
        _button.append_child(HTMLNode(_button.identifier, None, "span", value=MSG_CONFIGURE))

        # Its references, or the gauge of its development when it has none.
        _column = TagNode(_flex.identifier, None, "div", attributes={"class": "flex-item width_10"})
        _flex.append_child(_column)
        _references = annotation.get_reference_identifiers()
        if len(_references) > 0:
            for _reference in _references:
                _url = annotation.get_reference_url(_reference)
                # A document is told from a web page.
                _icon = "external-link"
                if _url.endswith("pdf") is True:
                    _icon = "file"
                # A published work is opened in a tab of its own: this page
                # stays where it is, and one comes back to it by closing that tab.
                _column.append_child(HTMLNode(_column.identifier, None, "a",
                                              attributes={"href": _url, "class": "icon-button",
                                                          "data-icon": _icon,
                                                          "aria-label": _url, "title": _url,
                                                          "target": "_blank", "rel": "noopener"}))
        else:
            _devel = min(100, max(0, annotation.get_devel()))
            _p = TagNode(_column.identifier, None, "p", attributes={"class": "annotate-ann-devel"})
            _column.append_child(_p)
            _p.append_child(HTMLNode(_p.identifier, None, "progress",
                                     attributes={"id": "annotate_devel_" + _key, "value": str(_devel),
                                                 "max": "100", "aria-label": MSG_DEVEL}))
            _p.append_child(HTMLNode(_p.identifier, None, "span", value="{:d}%".format(_devel)))

        # The choice of its language, when it has language resources.
        _column = TagNode(_flex.identifier, None, "div", attributes={"class": "flex-item width_10"})
        _flex.append_child(_column)
        _languages = annotation.get_langlist()
        if len(_languages) > 0:
            _attributes = {"id": "annotate_lang_" + _key, "name": "annotate_lang_" + _key,
                           "form": "annotate_form", "aria-label": MSG_LANG_OF.format(_name)}
            if disabled is True:
                _attributes["disabled"] = None
            _select = TagNode(_column.identifier, None, "select", attributes=_attributes)
            _column.append_child(_select)
            _choices = list(_languages)
            _choices.append(LANG_NONE)
            _selected = lang
            if len(_selected) == 0:
                _selected = LANG_NONE
            for _lang in sorted(_choices):
                _attributes = {"value": _lang}
                if _lang == _selected:
                    _attributes["selected"] = None
                _select.append_child(HTMLNode(_select.identifier, None, "option", value=_lang,
                                              attributes=_attributes))

        # Its description, after the reason why it is disabled.
        _column = TagNode(_flex.identifier, None, "div", attributes={"class": "flex-item width_45"})
        _flex.append_child(_column)
        _descr = html.escape(annotation.get_descr().strip())
        if disabled is True:
            _descr = MSG_DISABLED + " " + _descr
        _column.append_child(HTMLNode(_column.identifier, None, "p", value=_descr))

        # Why it is not installed is said where what it requires would be,
        # in the color of what is missing.
        if len(reason) > 0:
            _column.append_child(HTMLNode(_column.identifier, None, "p", value=html.escape(reason),
                                          attributes={"class": "annotate-missing"}))

        # What it requires is a precision given after its description: a
        # description list, one term and its description for the files it
        # reads, by the names a person reads of their types, each name once
        # since two types may be read under the same name; one for the
        # annotations it requires, by their names.
        _names = list()
        for _type in filetypes:
            _name = MSG_FILETYPES.get(_type, _type)
            if (_name in _names) is False:
                _names.append(_name)
        if len(_names) > 0 or len(required) > 0:
            _dl = TagNode(_column.identifier, None, "dl", attributes={"class": "annotate-ann-precision"})
            _column.append_child(_dl)
            if len(_names) > 0:
                _dl.append_child(HTMLNode(_dl.identifier, None, "dt", value=MSG_REQUIRED_FILES))
                _dl.append_child(HTMLNode(_dl.identifier, None, "dd", value=html.escape(", ".join(_names))))
            if len(required) > 0:
                _term = MSG_REQUIRED_ANNOTATION
                if len(required) > 1:
                    _term = MSG_REQUIRED_ANNOTATIONS
                _dl.append_child(HTMLNode(_dl.identifier, None, "dt", value=_term))
                _dl.append_child(HTMLNode(_dl.identifier, None, "dd", value=html.escape(", ".join(required))))

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_options(parent: TagNode, annotation, options: TagNode | None) -> None:
        """Append the dialog of the options of one annotation.

        The container of the service of the options stands in it when that
        annotation is configured; an empty section takes its place otherwise.

        :param parent: (TagNode) The panel
        :param annotation: What the step of the API answers
        :param options: (TagNode) The container of the service of the options, None if not configured

        """
        _key = annotation.get_key()
        _id = "annotate_options_" + _key
        _dialog = TagNode(parent.identifier, _id, "dialog", attributes={"id": _id, "aria-labelledby": _id + "_h"})
        parent.append_child(_dialog)
        _dialog.append_child(HTMLNode(_dialog.identifier, None, "h4",
                                      value=MSG_OPTIONS_OF.format(annotation.get_name()),
                                      attributes={"id": _id + "_h"}))
        if options is None:
            _dialog.append_child(TagNode(_dialog.identifier, None, "section", attributes={"aria-label": MSG_OPTIONS}))
        else:
            _dialog.append_child(options)

# ---------------------------------------------------------------------------


class swappFilesAnnotatePanel(TagNode):
    """The button which comes back to the six steps, and the title of the files.

    The container of the provision of files is appended to it by the
    response, as that service writes it, and altered in nothing.

    """

    def __init__(self, parent: str):
        """Create the panel of the files.

        :param parent: (str) Identifier of the node the panel is appended to

        """
        super(swappFilesAnnotatePanel, self).__init__(parent, "annotate_files_panel", "section",
                                                      attributes={"id": "annotate_files_panel",
                                                                  "aria-labelledby": "annotate_files_h"})
        append_head(self, "annotate_files_h", MSG_FILES_TITLE)

# ---------------------------------------------------------------------------


class swappLogAnnotatePanel(TagNode):
    """The button which comes back to the six steps, the title, and the procedure outcome report.

    The report is written line for line as the API wrote it, in a font of one
    width, the mark of the state a line bears in the class of that state.

    One panel, and two moments. While a run goes, the way back is
    offered and not available; under the title stand the nodes of the
    progress, which the page fills with what the API sets, and the report
    under them, folded. Once it has ended, the report is what the panel shows.

    """

    def __init__(self, parent: str, name: str, report: list, unavailable: str, running: bool, address: str):
        """Create the panel of the procedure outcome report.

        :param parent: (str) Identifier of the node the panel is appended to
        :param name: (str) Name of the report
        :param report: (list of swappReportLine) The lines of the report
        :param unavailable: (str) Why the report is not available, empty if it is
        :param running: (bool) A run is going
        :param address: (str) The address the report is reached at online, empty locally

        """
        super(swappLogAnnotatePanel, self).__init__(parent, "annotate_log_panel", "section",
                                                    attributes={"id": "annotate_log_panel",
                                                                "aria-labelledby": "annotate_log_h"})
        append_head(self, "annotate_log_h", MSG_LOG_TITLE, running is False)

        _holder = self
        if running is True:
            # The text of the progress is given its node, and the bar is named
            # by a label. The header is given its node as well: it holds the
            # annotation which is running, and nothing before the first one.
            _progress = swappProgressBar(self.identifier)
            _progress.update(message="")
            _bar = _progress.get_node()
            _bar.insert_child(0, HTMLNode(_bar.identifier, None, "label", value=MSG_PROGRESS,
                                          attributes={"for": "percent_progress"}))
            _bar.insert_child(0, HTMLNode(_bar.identifier, "progress_header", "h3",
                                          attributes={"id": "progress_header"}))
            self.append_child(_bar)
            _holder = TagNode(self.identifier, None, "details")
            self.append_child(_holder)
            _holder.append_child(HTMLNode(_holder.identifier, None, "summary",
                                          value=MSG_REPORT_FILE + " " + html.escape(name),
                                          attributes={"id": "annotate_report_file"}))
        elif len(address) > 0:
            # Online, the name of the report leads to it, and the browser is
            # told to keep it under that name instead of showing it.
            _p = TagNode(self.identifier, None, "p", attributes={"id": "annotate_report_file"})
            self.append_child(_p)
            _p.append_child(HTMLNode(_p.identifier, None, "span", value=MSG_REPORT_FILE))
            _p.append_child(HTMLNode(_p.identifier, None, "a", value=html.escape(name),
                                     attributes={"href": address, "download": name}))
        else:
            self.append_child(HTMLNode(self.identifier, None, "p", value=MSG_REPORT_FILE + " " + html.escape(name),
                                       attributes={"id": "annotate_report_file"}))

        _holder.append_child(report_node(_holder.identifier, report, unavailable))

# ---------------------------------------------------------------------------


class swappResultsPanel(TagNode):
    """What came of every root of the batch: its status, then the files produced under it.

    """

    def __init__(self, parent: str, results: list, addresses: dict, archive: str):
        """Create the panel of the results.

        :param parent: (str) Identifier of the node the panel is appended to
        :param results: (list of swappRootResult) One result per root of the batch
        :param addresses: (dict) The address of a produced file, by name, when
        the person is not on the machine which wrote it
        :param archive: (str) The address of the archive holding them all, empty if none

        """
        super(swappResultsPanel, self).__init__(parent, None, "section",
                                                attributes={"aria-labelledby": "annotate_results_h"})

        self.append_child(HTMLNode(self.identifier, None, "h4", value=MSG_RESULTS,
                                   attributes={"id": "annotate_results_h"}))
        _table = TagNode(self.identifier, None, "table")
        self.append_child(_table)
        _table.append_child(HTMLNode(_table.identifier, None, "caption", value=MSG_RESULTS_CAPTION))

        _head = TagNode(_table.identifier, None, "thead")
        _table.append_child(_head)
        _tr = TagNode(_head.identifier, None, "tr")
        _head.append_child(_tr)
        for _text in (MSG_ROOT, MSG_STATUS, MSG_RESULT):
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=_text, attributes={"scope": "col"}))

        _body = TagNode(_table.identifier, None, "tbody")
        _table.append_child(_body)
        for _result in results:
            _tr = TagNode(_body.identifier, None, "tr")
            _body.append_child(_tr)
            _tr.append_child(HTMLNode(_tr.identifier, None, "th", value=os.path.basename(_result.root),
                                      attributes={"scope": "row"}))
            _status = TagNode(_tr.identifier, None, "td")
            _tr.append_child(_status)
            _status.append_child(HTMLNode(_status.identifier, None, "span", value="",
                                          attributes={"data-icon": STATUS_ICONS[_result.status],
                                                      "role": "img",
                                                      "aria-label": MSG_STATUSES[_result.status]}))
            _td = TagNode(_tr.identifier, None, "td")
            _tr.append_child(_td)
            if len(_result.produced) > 0:
                _ul = TagNode(_td.identifier, None, "ul")
                _td.append_child(_ul)
                for _produced in _result.produced:
                    _li = TagNode(_ul.identifier, None, "li")
                    _ul.append_child(_li)
                    _name = os.path.basename(_produced)
                    if _produced in addresses:
                        # The file was written where the person is not: the
                        # name leads to it, and the browser is told to keep
                        # it under that name instead of showing it.
                        _li.append_child(HTMLNode(_li.identifier, None, "a", value=_name,
                                                  attributes={"href": addresses[_produced],
                                                              "download": _name}))
                    else:
                        _li.set_value(_name)

        # Ten files are got back in one gesture and not in ten.
        if len(archive) > 0:
            _p = TagNode(self.identifier, None, "p")
            self.append_child(_p)
            _p.append_child(HTMLNode(_p.identifier, None, "a", value=MSG_DOWNLOAD_ALL,
                                     attributes={"href": archive,
                                                 "download": "",
                                                 "class": "action-button",
                                                 "role": "button"}))

# ---------------------------------------------------------------------------


def report_node(parent: str, report: list, unavailable: str) -> HTMLNode:
    """Return the procedure outcome report, line for line, in a font of one width.

    The mark of the state a line bears is in a span of its class: the mark is
    what stands from "[ " to the next "]", and the color is carried by it
    alone, never by the whole line.

    :param parent: (str) Identifier of the node the report is appended to
    :param report: (list of swappReportLine) The lines of the report
    :param unavailable: (str) Why the report is not available, empty if it is
    :return: (HTMLNode)

    """
    if len(unavailable) > 0:
        _code = html.escape(unavailable)
    else:
        _lines = list()
        for _line in report:
            _text = html.escape(_line.text)
            if len(_line.state) > 0:
                _start = _line.text.find("[ ")
                _end = _line.text.find("]", _start)
                if _end > -1:
                    _text = (html.escape(_line.text[:_start])
                             + '<span class="' + STATE_CLASSES[_line.state] + '">'
                             + html.escape(_line.text[_start:_end + 1]) + "</span>"
                             + html.escape(_line.text[_end + 1:]))
            _lines.append(_text)
        _code = "\n".join(_lines)

    # The spaces of a pre are shown: the code it holds is its value, which is
    # written without indentation, and not a child, which would be.
    return HTMLNode(parent, None, "pre", value="<code>" + _code + "</code>",
                    attributes={"id": "annotate_report", "class": "annotate-report"})
