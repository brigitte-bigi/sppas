"""
:filename: sppas.ui.swapp.app_setup.fieldsets.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Create and manage the fieldset' nodes of the setup app.

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

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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
from whakerpy.htmlmaker import HTMLNode

from .base_fieldset import swappSetupBaseFieldset
from .fieldset_welcome import swappSetupHomeFieldset
from .fieldset_license import swappSetupLicenseFieldset
from .fieldset_feature import swappSetupDepsFieldset
from .fieldset_feature import swappSetupLangFieldset
from .fieldset_feature import swappSetupAnnotFieldset
from .fieldset_feature import swappSetupSpinOffFieldset
from .fieldset_install import swappSetupInstallFieldset

# ---------------------------------------------------------------------------


class swappSetupFieldsets:
    """Create all fieldset node instances for the Setup HTML tree.

    """

    def __init__(self, installer, uri: str = ""):
        """Create a SetupFieldsMaker instance.

        """
        self._installer = installer

        self.__fields = list()
        self.__fields.append(swappSetupHomeFieldset(None, uri))
        self.__fields.append(swappSetupLicenseFieldset(None, uri))
        self.__fields.append(swappSetupDepsFieldset(None, self._installer, "deps"))
        self.__fields.append(swappSetupLangFieldset(None, self._installer, "lang"))
        self.__fields.append(swappSetupAnnotFieldset(None, self._installer, "annot"))
        self.__fields.append(swappSetupSpinOffFieldset(None, self._installer, "spin"))
        self.__fields.append(swappSetupInstallFieldset(None))

        self.__keys = tuple([f.identifier for f in self.__fields])
        self.__current = 0

    # -----------------------------------------------------------------------

    def get_current(self) -> int:
        """Return the index of the current fieldset."""
        return self.__current

    # -----------------------------------------------------------------------

    def get_current_identifier(self) -> str:
        """Return the identifier of the current fieldset."""
        return self.__keys[self.__current]

    # -----------------------------------------------------------------------

    def get_index(self, field: swappSetupBaseFieldset) -> int:
        """Return the index of the given field.

        :param field: (HTMLNode)
        :raises: ValueError: if field is unknown

        """
        return self.__fields.index(field)

    # -----------------------------------------------------------------------

    def get_index_from_name(self, field_name: str) -> int:
        """Return the index of the given field from its identifier.

        :param field_name: (str) Name of the field to get index
        :raises: ValueError: if field_name is unknown

        """
        return self.__keys.index(field_name)

    # -----------------------------------------------------------------------

    def get_identifier(self, idx) -> str:
        return self.__keys[idx]

    # -----------------------------------------------------------------------

    def browse_next(self) -> int:
        """Get the index of the current field and offset it by +1."""
        self.__current = min(self.__current + 1, len(self.__fields)-1)
        return self.__current

    # -----------------------------------------------------------------------

    def browse_previous(self) -> int:
        """Get the index of the current field and offset it by -1."""
        self.__current = max(0, self.__current - 1)
        return self.__current

    # -----------------------------------------------------------------------

    def next_field(self, current):
        """Return the next field.

        :return: (HTMLNode) a fieldset

        """
        if isinstance(current, HTMLNode) is False:
            raise TypeError
        if current.identifier not in self.__keys:
            raise KeyError

        # Get the index of the given field and offset it by +1
        next_index = min(self.__keys.index(current.identifier) + 1, len(self.__keys)-1)

        # Return the previous key's value, or the current if no prev
        return self.__fields[next_index]

    # -----------------------------------------------------------------------

    def prev_field(self, current):
        """Return the previous field.

        :return: (HTMLNode) a fieldset

        """
        if isinstance(current, HTMLNode) is False:
            raise TypeError
        if current.identifier not in self.__keys:
            raise KeyError

        # Get the index of the given field and offset it by -1
        prev_index = max(0, self.__keys.index(current.identifier) - 1)

        # return the next key's value, or the current if no next
        return self.__fields[prev_index]

    # -----------------------------------------------------------------------

    def get_progress(self) -> object:
        """Return the progress of the current fieldset or None."""
        field = self.__fields[self.__current]
        if hasattr(field, "get_progress"):
            return field.get_progress()
        return None

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __contains__(self, field):
        return field in self.__fields

    def __iter__(self):
        for f in self.__fields:
            yield f

    def __getitem__(self, i):
        return self.__fields[i]

    def __len__(self):
        return len(self.__keys)

    def __index__(self, field):
        return self.__fields.index(field)
