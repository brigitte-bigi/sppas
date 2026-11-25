"""
:filename: sppas.ui.swapp.app_setup.setup_model.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Setup Model of the MVC paradigm: manage the installer.

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
import sys
import traceback
import logging

from sppas.core import cfg
from sppas.core.preinstall import sppasInstallerDeps

from ..swapp_base.swapp_process import swappProcess

# ---------------------------------------------------------------------------

# What a person accepts before anything is installed.
ACCEPTANCES = ("check_ref", "check_prod", "check_license")

# They are accepted beforehand at the log level of the author only -- 1,
# below any standard level and out of reach of the Configuration page: an
# engagement is taken by the user, never by the software, and this is what
# makes the tests bearable for the one who writes them.
AUTHOR_LOG_LEVEL = 1

# ---------------------------------------------------------------------------


class swappSetupModel:

    def __init__(self):
        """Initialize the swappSetupModel.

        The installer is None until reset() is invoked.

        """
        # The process the installation is performed in: none before the first one.
        self.__process = None

        # Declare members
        self.__installer = None
        self.__errors = ""
        self.__accepted = dict()
        self.reset()

    # -----------------------------------------------------------------------

    def get_installer(self):
        return self.__installer

    installer = property(get_installer, None, None, "installer")

    def get_errors(self):
        return self.__errors

    errors = property(get_errors, None, None, "errors")

    # -----------------------------------------------------------------------

    def reset(self):
        """Reset all. """
        if self.is_installation_running() is True:
            return

        self.__installer = None
        self.__errors = ""
        self.__accepted = dict()
        for _name in ACCEPTANCES:
            self.__accepted[_name] = cfg.log_level <= AUTHOR_LOG_LEVEL

        # Create the SPPAS installer system for dependencies
        try:
            self.__installer = sppasInstallerDeps()
        except Exception as e:
            logging.error("No installation will be performed. The installer "
                          "wasn't created due to the following error: {}"
                          "".format(str(e)))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            self.__installer = None
        else:
            # The 'sppas' feature updates the installed 'sppas' package: it is
            # enabled only if a newer version is available on the pypi repository.
            self.__installer.enable("sppas", cfg.update_info.get('update'))

    # -----------------------------------------------------------------------

    def enable_feature(self, feature_name: str) -> None:
        """Enable or disable a feature the installer can manage.

        :param feature_name: (str) Name of the feature

        """
        do_enable = not self.__installer.enable(feature_name)
        self.__installer.enable(feature_name, do_enable)
        logging.debug(" - feature {} enable is: {}".format(feature_name, do_enable))

    # -----------------------------------------------------------------------

    def is_available(self, feature_name: str) -> bool:
        """Return True if the feature can be installed on this machine.

        :param feature_name: (str) Name of the feature
        :return: (bool)

        """
        if feature_name == "sppas" and cfg.update_info.get('update') is False:
            return False
        if feature_name == "mactools" and sys.platform != "darwin":
            return False
        if feature_name == "wintools" and sys.platform.startswith("win") is False:
            return False
        return True

    # -----------------------------------------------------------------------

    def is_accepted(self, name: str) -> bool:
        """Return True if the person accepted what the given name stands for.

        :param name: (str) One of the acceptances
        :return: (bool) False for a name which is not an acceptance

        """
        return self.__accepted.get(name, False)

    # -----------------------------------------------------------------------

    def accept(self, name: str) -> bool:
        """Accept what the given name stands for, or take the acceptance back.

        :param name: (str) One of the acceptances
        :raises: KeyError: The given name is not an acceptance
        :return: (bool) Whether it is accepted now

        """
        if name not in self.__accepted:
            raise KeyError("Unknown acceptance: {:s}".format(name))
        self.__accepted[name] = self.__accepted[name] is False
        return self.__accepted[name]

    # -----------------------------------------------------------------------
    # Installation processing
    # -----------------------------------------------------------------------

    def is_installation_running(self):
        """Return true if the installation is currently running.

        It is read in the file of the process, which says it has ended once
        the installer has returned.

        """
        if self.__process is None:
            return False
        _percent, _header, _text, _finished = self.__process.read()

        return _finished is False

    # -----------------------------------------------------------------------

    def installation_start(self) -> str:
        """Start the installation as a process of swapp.

        :raises: RuntimeError: The installation was already running.
        :return: (str) The name of the process, which the page follows

        """
        # Already installing
        if self.is_installation_running() is True:
            raise RuntimeError("The installation is already running.")

        # Log
        logging.info("--- Selected features for installation ---")
        for ftype in ("deps", "lang", "annot", "spin"):
            ids = self.__installer.features_ids(ftype)
            enabled = [fid for fid in ids if self.__installer.enable(fid)]
            logging.info(f"{ftype}: {len(enabled)} is {enabled}")

        # Start the installation process
        # It is not allowed to be stopped, only killed with the app
        self.__errors = ""
        self.__process = swappProcess.start(self.__install_features, ())

        return self.__process.name

    # -----------------------------------------------------------------------
    # The method for the process -- private
    # -----------------------------------------------------------------------

    def __install_features(self, progress=None):
        """Install all the enabled features, of any type.

        It is what the process performs, in its thread.

        :param progress: (swappProcessProgress) The progress of the process

        """
        self.__installer.set_progress(progress)
        self.__errors = self.__installer.install()
