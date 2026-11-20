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

# ---------------------------------------------------------------------------

# The choice of no language, and the one of several languages.
LANG_NONE = "---"
LANG_MIX = "MIX"

# ---------------------------------------------------------------------------


class swappAnnotateRecord:
    """What one request holds: its task, what was decided, and what is shown.

    The view serializes what was decided into the form of the page, and the
    controller parses it back at the next request: nobody holds it between
    two requests. The language of the page is not serialized: it is the one
    of the selected annotations, and it is transmitted only by the page of
    the six steps, where it is a field. What is to be shown is not serialized: it is decided by
    the request which shows it.

    """

    def __init__(self):
        """Create a record with nothing in it."""
        self.__task = ""
        self.__report = ""
        self.__extensions = dict()
        self.__lang = ""
        self.__selected = list()
        self.__annotation_langs = dict()
        self.__merge = False
        self.__to_be_shown = dict()

    # -----------------------------------------------------------------------

    def serialize(self) -> dict:
        """Return what was decided, as strings a page carries.

        :return: (dict) One entry per name, each of them a string

        """
        _data = dict()
        for _kind in self.__extensions:
            _data["annotate_ext_" + _kind] = self.__extensions[_kind]
        for _key in self.__selected:
            _data["annotate_ann_" + _key] = "True"
        for _key in self.__annotation_langs:
            _data["annotate_lang_" + _key] = self.__annotation_langs[_key]
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
        self.__extensions = dict()
        self.__lang = ""
        self.__selected = list()
        self.__annotation_langs = dict()
        self.__merge = False
        self.__to_be_shown = dict()

        if isinstance(data.get("annotate_task"), str) is True:
            self.__task = data["annotate_task"]
        if isinstance(data.get("annotate_report"), str) is True:
            self.__report = data["annotate_report"]
        if isinstance(data.get("annotate_lang"), str) is True:
            self.__lang = data["annotate_lang"]
        self.__merge = str(data.get("annotate_merge", False)) == "True"

        for _name in data:
            if isinstance(data[_name], str) is False:
                continue
            if _name.startswith("annotate_ext_") is True:
                self.__extensions[_name[len("annotate_ext_"):]] = data[_name]
            elif _name.startswith("annotate_ann_") is True:
                if data[_name] == "True":
                    self.__selected.append(_name[len("annotate_ann_"):])
            elif _name.startswith("annotate_lang_") is True:
                self.__annotation_langs[_name[len("annotate_lang_"):]] = data[_name]

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
        """Return the extension chosen for each kind of output file (dict)."""
        return dict(self.__extensions)

    # -----------------------------------------------------------------------

    def set_extension(self, kind: str, extension: str) -> None:
        """Set the extension chosen for a kind of output file.

        :param kind: (str) The kind of output file
        :param extension: (str) The extension, its dot included

        """
        self.__extensions[str(kind)] = str(extension)

    # -----------------------------------------------------------------------

    def get_lang(self) -> str:
        """Return the language of the page, empty if none (str)."""
        return self.__lang

    # -----------------------------------------------------------------------

    def get_selected(self) -> list:
        """Return the keys of the selected annotations (list of str)."""
        return list(self.__selected)

    # -----------------------------------------------------------------------

    def unselect(self, key: str) -> None:
        """Take the selection of an annotation back.

        :param key: (str) The key of the annotation

        """
        if (key in self.__selected) is True:
            self.__selected.remove(key)

    # -----------------------------------------------------------------------

    def set_lang(self, lang: str) -> None:
        """Set the language of the page.

        :param lang: (str) The language, LANG_NONE or LANG_MIX

        """
        self.__lang = str(lang)

    # -----------------------------------------------------------------------

    def get_annotation_langs(self) -> dict:
        """Return the language of each annotation, by its key (dict)."""
        return dict(self.__annotation_langs)

    # -----------------------------------------------------------------------

    def set_annotation_lang(self, key: str, lang: str) -> None:
        """Set the language of one annotation.

        :param key: (str) The key of the annotation
        :param lang: (str) Its language

        """
        self.__annotation_langs[str(key)] = str(lang)

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
    lang = property(get_lang, set_lang)
    selected = property(get_selected, None)
    annotation_langs = property(get_annotation_langs, None)
    merge = property(get_merge, None)
    to_be_shown = property(get_to_be_shown, None)
