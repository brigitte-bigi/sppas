#!/usr/bin/env python
# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.config.appcfg.py
:author: Brigitte Bigi
:contributor: Florian Hocquet
:contact: contact@sppas.org
:summary: The application configuration.

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
import sys
import json
import hashlib

from .settings import paths

# ---------------------------------------------------------------------------


class sppasAppConfig(object):
    """Configuration for SPPAS application.

    An instance of this class has to be created for any application using
    the SPPAS API.

    Members are:

        - log_level
        - interoperability
        - features dictionary

    """

    APP_CONFIG_FILENAME = ".app~"
    DEFAULT_LOG_LEVEL = 15
    DEFAULT_INTEROPERABILITY = True

    # -----------------------------------------------------------------------

    def __init__(self):
        """Create a new sppasAppConfig instance.

        The configuration is set to its default values and updated
        with the content of a configuration file (if existing).

        The configuration is saved the 1st time this class is instantiated
        and when this class is deleted.

        """
        super(sppasAppConfig, self).__init__()

        # Create a default configuration
        self.__update_info = None
        self.__log_level = sppasAppConfig.DEFAULT_LOG_LEVEL
        self.__interoperability = sppasAppConfig.DEFAULT_INTEROPERABILITY
        self.__feat_ids = dict()

        # Load the existing configuration file (if any)
        self.load()

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        # self.save()
        pass

    # -----------------------------------------------------------------------

    def get_log_level(self):
        """Return the level for logging messages, ranging 0-50."""
        return self.__log_level

    def set_log_level(self, value):
        """Set the log level for the application.

        :param value: (int) Logging ranges from 0 (any) to 50 (critical only).

        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 50:
            value = 50
        self.__log_level = value

    log_level = property(get_log_level, set_log_level)

    # -----------------------------------------------------------------------

    def get_interoperability(self):
        """Return True if a file is written without loss of information."""
        return self.__interoperability

    def set_interoperability(self, value):
        """Set whether a file is written without loss of information.

        When it is False, what a format can't hold is lost: it's the choice
        of the user, the default is to preserve it.

        :param value: (bool) Preserve what the destination format can't hold.

        """
        self.__interoperability = bool(value)

    interoperability = property(get_interoperability, set_interoperability)

    # -----------------------------------------------------------------------

    def set_update_info(self, info):
        """Store update check result."""
        self.__update_info = info

    def get_update_info(self):
        """Return update check result."""
        return self.__update_info

    update_info = property(get_update_info, set_update_info)

    # -----------------------------------------------------------------------

    @staticmethod
    def cfg_filename():
        """Return the name of the config file.

        The file says which features are installed, and they are installed
        in the environment SPPAS is running in: two installed versions have
        their own, and neither writes into the other. It is stored with the
        other files of the user, and not in the environment: an environment
        created by somebody to install SPPAS with pip is theirs, and SPPAS
        leaves no file of its own in it.

        The name carries the environment: the name of its directory, and a
        short digest of its full path -- two environments named alike are
        still told apart. It begins with a dot, like every other file SPPAS
        leaves among the files of the user: they are its own, not theirs.

        """
        prefix = os.path.abspath(sys.prefix)
        digest = hashlib.sha1(prefix.encode("utf-8")).hexdigest()[:8]
        name = ".{:s}-{:s}{:s}".format(os.path.basename(prefix), digest,
                                       sppasAppConfig.APP_CONFIG_FILENAME)

        return os.path.join(paths.ext_dir, name)

    # ------------------------------------------------------------------------

    def load(self):
        """Load the configuration from a file."""
        cfg = self.cfg_filename()

        if os.path.exists(cfg) is False:
            # The file isn't existing. It's the first launch. Save it
            # with the default values.
            self.save()

        else:
            with open(self.cfg_filename()) as cfg:
                try:
                    d = json.load(cfg)
                except json.decoder.JSONDecodeError:
                    # Override
                    self.save()
                else:
                    self.__log_level = d.get("log_level", sppasAppConfig.DEFAULT_LOG_LEVEL)
                    self.__interoperability = d.get(
                        "interoperability",
                        sppasAppConfig.DEFAULT_INTEROPERABILITY)

                    # Load the deps of the file without deleting the ones already in
                    # the dict: add or override the deps of the file to our dict.
                    deps = d.get("features", dict())
                    for key in deps:
                        self.__feat_ids[key] = deps[key]

    # ------------------------------------------------------------------------

    def save(self):
        """Save into a JSON file."""
        # Admin rights are needed to write in an hidden file. So it's needed
        # to switch the file in a normal mode in order to modify it and then
        # to hide back the file.
        self.__hide(False)
        with open(self.cfg_filename(), "w") as f:
            d = dict()
            d["log_level"] = self.__log_level
            d["interoperability"] = self.__interoperability
            d["features"] = self.__feat_ids
            f.write(json.dumps(d, indent=2))

        self.__hide(True)

    # ------------------------------------------------------------------------

    def __hide(self, value):
        """Hide or un-hide a file.

        :param value: (bool) Hide the config filename

        """
        filename = self.cfg_filename()
        system = sys.platform
        if system == "win32":
            oper = "+"
            if value is False:
                oper = "-"
            p = os.popen('attrib ' + oper + 'h ' + filename)
            p.close()

    # ------------------------------------------------------------------------
    # Methods related to the list of available features.
    # ------------------------------------------------------------------------

    def get_feature_ids(self):
        """Return the list of feature identifiers currently known."""
        return list(self.__feat_ids.keys())

    # ------------------------------------------------------------------------

    def feature_installed(self, key):
        """Return True if a feature was successfully installed by SPPAS.

        :param key: (str) Identifier of a feature.

        """
        if key not in self.__feat_ids:
            return False
        return self.__feat_ids[key]

    # ------------------------------------------------------------------------

    def set_feature(self, key, value):
        """Add or update a feature.

        This change is set to the current dict but is not saved in the
        configuration file.

        :param key: (str) Identifier of a feature
        :param value: (bool) Installed or disabled

        """
        self.__feat_ids[key] = bool(value)
