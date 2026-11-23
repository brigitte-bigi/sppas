"""
:filename: sppas.ui.swapp.app_annotate.annotate_record.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What one request of Annotate holds.

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

from sppas.core.coreutils import sppasTypeError
from sppas.src.annotations import sppasFiles
from sppas.src.annotations import sppasParam

from .annotate_annotations import LANG_NONE

# ---------------------------------------------------------------------------


class swappAnnotateRecord:
    """What one request holds: its task, what was decided, and what is shown.

    The view serializes what was decided into the form of the page, and the
    controller parses it back at the next request: nobody holds it between
    two requests. The language of the page is not held: it is a gesture of
    the page of the six steps, which writes the language of the annotations.
    What is to be shown is not serialized: it is decided by the request which
    shows it.

    What was decided is held in a sppasParam, which carries every decision
    the API performs with: which annotations are activated, the language of
    each, the values of their options, and the extension of every kind of
    output file. A new one holds the defaults of the API. The merge option
    and the checked report are not of it.

    """

    def __init__(self):
        """Create a record with nothing in it."""
        self.__task = ""
        self.__report = ""
        self.__parameters = sppasParam()
        self.__merge = False
        self.__to_be_shown = dict()

    # -----------------------------------------------------------------------

    def serialize(self) -> dict:
        """Return what was decided, as strings a page carries.

        :return: (dict) One entry per name, each of them a string

        """
        _data = dict()
        _extensions = self.get_extensions()
        for _kind in _extensions:
            _data["annotate_ext_" + _kind] = _extensions[_kind]
        for _key in self.get_selected():
            _data["annotate_ann_" + _key] = "True"
        _langs = self.get_annotation_langs()
        for _key in _langs:
            _data["annotate_lang_" + _key] = _langs[_key]
        for i in range(self.__parameters.get_step_numbers()):
            _data.update(self.serialize_options(self.__parameters.get_step_key(i)))
        _data["annotate_merge"] = str(self.__merge)
        _data["annotate_report"] = self.__report

        return _data

    # -----------------------------------------------------------------------

    def parse(self, data: dict) -> None:
        """Fill in the record with what a page sent.

        An entry which is absent takes its default value.

        :param data: (dict) What a page sent
        :raises: sppasTypeError: The given data is not a dictionary

        """
        if isinstance(data, dict) is False:
            raise sppasTypeError(data, "dict")

        self.__task = ""
        self.__report = ""
        self.__parameters = sppasParam()
        self.__merge = False
        self.__to_be_shown = dict()

        if isinstance(data.get("event_bake"), str) is True:
            self.__task = data["event_bake"]
        if isinstance(data.get("annotate_report"), str) is True:
            self.__report = data["annotate_report"]
        self.__merge = str(data.get("annotate_merge", False)) == "True"

        for _name in data:
            if isinstance(data[_name], str) is False:
                continue
            if _name.startswith("annotate_ext_") is True:
                self.set_extension(_name[len("annotate_ext_"):], data[_name])
            elif _name.startswith("annotate_ann_") is True:
                if data[_name] == "True":
                    _key = _name[len("annotate_ann_"):]
                    self.__parameters.activate_step(self.__parameters.get_step_idx(_key))
            elif _name.startswith("annotate_lang_") is True:
                self.set_annotation_lang(_name[len("annotate_lang_"):], data[_name])

        # The field of an option is named after the key of its annotation and
        # its own: the name is built from both, and never split.
        for i in range(self.__parameters.get_step_numbers()):
            _key = self.__parameters.get_step_key(i)
            for _option in self.__parameters.get_options(i):
                _name = "annotate_opt_" + _key + "_" + _option.get_key()
                if isinstance(data.get(_name), str) is True:
                    self.__parameters.set_option_value(i, _option.get_key(), data[_name])

    # -----------------------------------------------------------------------

    def serialize_options(self, key: str) -> dict:
        """Return the values of the options of one annotation, as strings a page carries.

        :param key: (str) The key of the annotation
        :raises: KeyError: No annotation has that key
        :return: (dict) One entry per option, each of them a string

        """
        _data = dict()
        for _option in self.get_options(key):
            _data["annotate_opt_" + key + "_" + _option.get_key()] = str(_option.get_value())

        return _data

    # -----------------------------------------------------------------------

    def show(self, key: str, value) -> None:
        """Put one thing to be shown in the record.

        :param key: (str) What it is
        :param value: What is to be shown

        """
        self.__to_be_shown[key] = value

    # -----------------------------------------------------------------------

    def get_task(self) -> str:
        """Return the task the request asks for, empty if none (str)."""
        return self.__task

    # -----------------------------------------------------------------------

    def get_report(self) -> str:
        """Return the name of the checked report, empty if none (str)."""
        return self.__report

    # -----------------------------------------------------------------------

    def set_report(self, name: str) -> None:
        """Set the name of the checked report.

        :param name: (str) The name of the report, empty if none is checked

        """
        self.__report = str(name)

    # -----------------------------------------------------------------------

    def get_extensions(self) -> dict:
        """Return the extension chosen for each kind of output file which has extensions.

        A kind which has no extension has none to choose.

        :return: (dict) key=kind, value=extension

        """
        _extensions = dict()
        for _kind in sppasFiles.OUT_FORMATS:
            if len(sppasFiles.get_outformat_extensions(_kind)) > 0:
                _extensions[_kind] = self.__parameters.get_output_extension(_kind)

        return _extensions

    # -----------------------------------------------------------------------

    def set_extension(self, kind: str, extension: str) -> None:
        """Set the extension chosen for a kind of output file.

        :param kind: (str) The kind of output file
        :param extension: (str) The extension, its dot included
        :raises: ValueError: The API can't write that kind with that extension

        """
        self.__parameters.set_output_extension(str(extension), str(kind))

    # -----------------------------------------------------------------------

    def get_parameters(self) -> sppasParam:
        """Return what was decided, as the API performs with it (sppasParam)."""
        return self.__parameters

    # -----------------------------------------------------------------------

    def get_selected(self) -> list:
        """Return the keys of the selected annotations, in the order of the API (list of str)."""
        _selected = list()
        for i in range(self.__parameters.get_step_numbers()):
            if self.__parameters.get_step_status(i) is True:
                _selected.append(self.__parameters.get_step_key(i))

        return _selected

    # -----------------------------------------------------------------------

    def unselect(self, key: str) -> None:
        """Take the selection of an annotation back.

        :param key: (str) The key of the annotation
        :raises: KeyError: No annotation has that key

        """
        self.__parameters.disable_step(self.__parameters.get_step_idx(key))

    # -----------------------------------------------------------------------

    def get_annotation_langs(self) -> dict:
        """Return the language of each annotation which has language resources.

        :return: (dict) key=key of the annotation, value=its language, empty if none

        """
        _langs = dict()
        for i in range(self.__parameters.get_step_numbers()):
            _step = self.__parameters.get_step(i)
            if len(_step.get_langlist()) > 0:
                _lang = _step.get_lang()
                if _lang is None:
                    _lang = ""
                _langs[_step.get_key()] = _lang

        return _langs

    # -----------------------------------------------------------------------

    def set_annotation_lang(self, key: str, lang: str) -> None:
        """Set the language of one annotation.

        No language is given to the API as None.

        :param key: (str) The key of the annotation
        :param lang: (str) Its language, empty or LANG_NONE for none
        :raises: KeyError: No annotation has that key

        """
        _step = self.__parameters.get_step(self.__parameters.get_step_idx(key))
        if len(lang) == 0 or lang == LANG_NONE:
            _step.set_lang(None)
        else:
            _step.set_lang(lang)

    # -----------------------------------------------------------------------

    def get_options(self, key: str) -> list:
        """Return the options of one annotation, every one holding its value.

        :param key: (str) The key of the annotation
        :raises: KeyError: No annotation has that key
        :return: (list of sppasOption)

        """
        return self.__parameters.get_options(self.__parameters.get_step_idx(key))

    # -----------------------------------------------------------------------

    def set_options(self, key: str, options: list) -> None:
        """Give the options of one annotation the values the given ones hold.

        :param key: (str) The key of the annotation
        :param options: (list of sppasOption) Options of that annotation
        :raises: KeyError: No annotation has that key, or an option is not one of it

        """
        _idx = self.__parameters.get_step_idx(key)
        for _option in options:
            self.__parameters.set_option_value(_idx, _option.get_key(), _option.get_value())

    # -----------------------------------------------------------------------

    def get_merge(self) -> bool:
        """Return True if the merge option is checked (bool)."""
        return self.__merge

    # -----------------------------------------------------------------------

    def get_to_be_shown(self) -> dict:
        """Return what is to be shown (dict)."""
        return self.__to_be_shown

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    task = property(get_task, None)
    report = property(get_report, set_report)
    extensions = property(get_extensions, None)
    parameters = property(get_parameters, None)
    selected = property(get_selected, None)
    annotation_langs = property(get_annotation_langs, None)
    merge = property(get_merge, None)
    to_be_shown = property(get_to_be_shown, None)
