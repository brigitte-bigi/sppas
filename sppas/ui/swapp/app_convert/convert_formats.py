"""
:filename: sppas.ui.swapp.app_convert.convert_formats.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The formats which can be written, and what each of them holds.

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

from sppas.core.coreutils import sppasTypeError
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import FileFormatProperty
from sppas.ui import _

# ---------------------------------------------------------------------------

# The properties of a format: its identifier, the method of the API which
# says whether a format holds it, and what is shown of it.
PROPERTIES = (
    ("metadata", "metadata_support", _("Metadata")),
    ("multi_tiers", "multi_tiers_support", _("Multi tiers")),
    ("no_tiers", "no_tiers_support", _("No tier")),
    ("point", "point_support", _("Point")),
    ("interval", "interval_support", _("Interval")),
    ("gaps", "gaps_support", _("Gaps")),
    ("overlaps", "overlaps_support", _("Overlaps")),
    ("hierarchy", "hierarchy_support", _("Hierarchy")),
    ("ctrl_vocab", "ctrl_vocab_support", _("Ctrl vocab")),
    ("media", "media_support", _("Media")),
    ("radius", "radius_support", _("Vagueness")),
    ("alt_localization", "alternative_localization_support", _("Alt. loc")),
    ("alt_tag", "alternative_tag_support", _("Alt. tag")),
    ("tag_types", "tag_types_support", _("Typed tags")),
    ("tag_geometry", "tag_geometry_support", _("Geom. tags"))
)

# ---------------------------------------------------------------------------


class swappFormat:
    """A format of the API, and what it holds.

    What a format holds is read from the API when the format is created, and
    it belongs to the format and never to a file.

    """

    def __init__(self, extension: str):
        """Create the format of the given extension.

        :param extension: (str) Extension of the format, with or without its dot
        :raises: sppasTypeError: The given extension is not a string

        """
        if isinstance(extension, str) is False:
            raise sppasTypeError(extension, "str")

        _format_property = FileFormatProperty(extension)
        self.__extension = _format_property.get_extension()
        self.__software = _format_property.get_software()
        self.__writer = _format_property.get_writer()
        self.__properties = swappFormat.__read_properties(self.__extension)

    # -----------------------------------------------------------------------

    def get_extension(self) -> str:
        """Return the extension of the format, its dot included (str)."""
        return self.__extension

    # -----------------------------------------------------------------------

    def get_software(self) -> str:
        """Return the name of the software the format belongs to (str)."""
        return self.__software

    # -----------------------------------------------------------------------

    def get_properties(self) -> dict:
        """Return what the format holds, by property.

        :return: (dict) True or False for every property

        """
        return dict(self.__properties)

    # -----------------------------------------------------------------------

    def holds(self, identifier: str) -> bool:
        """Return True if the format holds the given property.

        :param identifier: (str) Identifier of a property
        :return: (bool) False for a property which is not known

        """
        return self.__properties.get(identifier, False)

    # -----------------------------------------------------------------------

    def can_be_written(self) -> bool:
        """Return True if the API can write this format (bool)."""
        return self.__writer

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __read_properties(extension: str) -> dict:
        """Return what the format of the given extension holds.

        :param extension: (str) Extension of the format, its dot included
        :return: (dict) True or False for every property, False when the format is not known

        """
        _instance = None
        for _key in sppasTrsRW.TRANSCRIPTION_TYPES:
            if "." + _key.lower() == extension.lower():
                _instance = sppasTrsRW.TRANSCRIPTION_TYPES[_key]()

        _properties = dict()
        for _identifier, _method, _text in PROPERTIES:
            if _instance is None:
                _properties[_identifier] = False
            else:
                _properties[_identifier] = getattr(_instance, _method)()

        return _properties

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    extension = property(get_extension, None)
    software = property(get_software, None)
    properties = property(get_properties, None)

# ---------------------------------------------------------------------------


class swappModelFormats:
    """Know which formats can be written, and what each of them holds.

    It reads no file of the user: what it says depends on the API alone.

    """

    def __init__(self):
        """Create the knowledge of the formats which can be written."""
        self.__formats = list()
        for _key in sppasTrsRW.extensions_out():
            self.__formats.append(swappFormat(_key))

    # -----------------------------------------------------------------------

    def writable_formats(self) -> list:
        """Return the formats which can be written.

        :return: (list of swappFormat)

        """
        return list(self.__formats)

    # -----------------------------------------------------------------------

    @staticmethod
    def properties() -> list:
        """Return the properties of a format, in the order they are shown.

        :return: (list of tuple) The identifier and the text of every property

        """
        _properties = list()
        for _identifier, _method, _text in PROPERTIES:
            _properties.append((_identifier, _text))

        return _properties

    # -----------------------------------------------------------------------

    def can_be_written(self, extension: str) -> bool:
        """Return True if the given extension is one of a writable format.

        :param extension: (str) Extension of a format, its dot included
        :return: (bool)

        """
        if self.__format_of(extension) is None:
            return False

        return True

    # -----------------------------------------------------------------------

    def properties_of(self, extension: str) -> dict:
        """Return what the format of the given extension holds.

        :param extension: (str) Extension of a writable format, its dot included
        :return: (dict) True or False for every property, empty when the format cannot be written

        """
        _format = self.__format_of(extension)
        if _format is None:
            return dict()

        return _format.properties

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __format_of(self, extension: str):
        """Return the writable format of the given extension.

        :param extension: (str) Extension of a format, its dot included
        :return: (swappFormat) None when no writable format has this extension

        """
        if isinstance(extension, str) is False:
            return None

        for _format in self.__formats:
            if _format.extension.lower() == extension.lower():
                return _format

        return None
