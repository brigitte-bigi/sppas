"""
:filename: sppas.ui.swapp.app_annotate.annotate_annotations.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The annotations, the kinds of output file and the languages, as the API declares them.

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

from sppas.src.annotations import sppasFiles
from sppas.src.annotations import sppasParam

# ---------------------------------------------------------------------------

# The choice of no language, and the one of several languages.
LANG_NONE = "---"
LANG_MIX = "MIX"

# ---------------------------------------------------------------------------


class swappModelAnnotations:
    """The annotations, the kinds of output file and the languages.

    What it gives is what the API declares, relayed: nothing is written here.
    It reads no file of the user.

    """

    def __init__(self):
        """Create the model of the annotations, with every step of the API."""
        self.__parameters = sppasParam()

    # -----------------------------------------------------------------------

    def annotations(self) -> list:
        """Return one parameter per step of the API, in the order of the API.

        :return: (list) What each step of the API answers

        """
        _annotations = list()
        for i in range(self.__parameters.get_step_numbers()):
            _annotations.append(self.__parameters.get_step(i))

        return _annotations

    # -----------------------------------------------------------------------

    def is_installed(self, key: str) -> bool:
        """Return True if the annotation of that key is installed on that machine.

        It can when the API instantiates it without error.

        :param key: (str) Key of an annotation
        :raises: KeyError: No annotation has that key
        :return: (bool)

        """
        return self.__parameters.test_step(self.__parameters.get_step_idx(key))

    # -----------------------------------------------------------------------

    def kinds(self) -> dict:
        """Return the kinds of output file, with their extensions and their default one.

        A kind which has no extension is not given.

        :return: (dict) key=kind, value=(list of extensions, default extension)

        """
        _kinds = dict()
        for _kind in sppasFiles.OUT_FORMATS:
            _extensions = sppasFiles.get_outformat_extensions(_kind)
            if len(_extensions) == 0:
                continue
            _kinds[_kind] = (_extensions, sppasFiles.get_default_extension(_kind))

        return _kinds

    # -----------------------------------------------------------------------

    def language_of_selected(self, parameters: sppasParam) -> str:
        """Return the language the selected annotations hold.

        :param parameters: (sppasParam) What was decided
        :return: (str) LANG_NONE when none has a language, LANG_MIX when they have several

        """
        _langs = list()
        for i in range(parameters.get_step_numbers()):
            _step = parameters.get_step(i)
            if _step.get_activate() is True:
                _lang = _step.get_lang()
                if _lang is not None and len(_lang) > 0 and (_lang in _langs) is False:
                    _langs.append(_lang)

        if len(_langs) == 0:
            return LANG_NONE
        if len(_langs) == 1:
            return _langs[0]
        return LANG_MIX

    # -----------------------------------------------------------------------

    def fix_language(self, parameters: sppasParam, lang: str) -> None:
        """Give the language of the page to every annotation which has resources for it.

        An annotation which has language resources, but none for that
        language, is left without a language; one which has no language
        resources is not concerned. The page of the six steps sends the
        language of the page with every request: when it is the one the
        selected annotations hold, it was not changed, and nothing is done.

        :param parameters: (sppasParam) What was decided
        :param lang: (str) The language of the page, LANG_NONE or LANG_MIX

        """
        if lang == self.language_of_selected(parameters):
            return

        for i in range(parameters.get_step_numbers()):
            _step = parameters.get_step(i)
            _languages = _step.get_langlist()
            if len(_languages) > 0:
                if lang in _languages:
                    _step.set_lang(lang)
                else:
                    _step.set_lang(None)

    # -----------------------------------------------------------------------

    def languages(self) -> list:
        """Return the languages of every annotation put together, each of them once.

        :return: (list of str)

        """
        _languages = list()
        for i in range(self.__parameters.get_step_numbers()):
            _step = self.__parameters.get_step(i)
            for _lang in _step.get_langlist():
                if (_lang in _languages) is False:
                    _languages.append(_lang)

        return _languages
