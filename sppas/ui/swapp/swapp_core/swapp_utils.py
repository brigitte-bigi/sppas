"""
:filename: sppas.ui.swapp.swapp_core.swapp_utils.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Utilities for SPPAS Web-based applications.

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

    Copyright (C) 2011-2026 Brigitte Bigi
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
import logging

from .swappsg import swapp_settings

# ---------------------------------------------------------------------------


class swappImagesAccess:
    """Provide some access to image and icons of SPPAS web-based apps.

    Notice that os.path.join() is not used; "/" is used instead, because it
    is relevant in this situation (HTTPD protocol).

    """

    @staticmethod
    def get_image_filename(name, default="default"):
        """Return the filename matching the given name or the default.

        The pictures of the web-based apps stand in "statics/images" and
        the drawings SPPAS brings in "statics/icons". A logo is asked for
        with get_logo_filename().

        :param name: (str) Name of an image or an icon.
        :param default: (str) Default icon if name is missing.
        :return: (str|None) The filename or None.

        """
        # Given "name" is already a filename
        if os.path.exists(name):
            return name

        for asked in (name, default):
            for folder in (swapp_settings.images, swapp_settings.icons):
                for ext in (".png", ".svg"):
                    filename = folder + asked + ext
                    if os.path.exists(filename):
                        return filename

        logging.warning("Missing image {:s} in the SPPAS Package.".format(name))
        return None

    # ------------------------------------------------------------------------

    @staticmethod
    def get_logo_filename(name):
        """Return the filename of the logo matching the given name.

        The logos -- of SPPAS and of the institutions and the services it
        stands with -- are gathered in "statics/logos".

        :param name: (str) Name of a logo.
        :return: (str|None) The filename or None.

        """
        for ext in (".png", ".svg"):
            filename = swapp_settings.logos + name + ext
            if os.path.exists(filename):
                return filename

        logging.warning("Missing logo {:s} in the SPPAS Package.".format(name))
        return None
