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

    def can_be_performed(self, key: str) -> bool:
        """Return True if the annotation of that key can be performed on that machine.

        :param key: (str) Key of an annotation
        :return: (bool)

        """
        return True

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
