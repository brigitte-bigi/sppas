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
from threading import Thread

from sppas.core import cfg
from sppas.core.preinstall import sppasInstallerDeps

# ---------------------------------------------------------------------------


class swappSetupModel:

    def __init__(self):
        """Initialize the swappSetupModel.

        The installer is None until reset() is invoked.

        """
        # Create the thread for the installation process
        self.__th = Thread(target=self.__install_features)

        # Declare members
        self.__installer = None
        self.__errors = ""
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
        if self.__th.is_alive():
            return

        self.__installer = None
        self.__errors = ""

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
    # Installation processing
    # -----------------------------------------------------------------------

    def is_installation_running(self):
        """Return true if the installation is currently running."""
        return self.__th.is_alive()

    # -----------------------------------------------------------------------

    def installation_start(self, progress):
        """Start the installation in a thread.

        :param progress: (sppasBaseProgress|None) Progress object or None
        :raises: RuntimeError: The installation was already running.

        """
        # Already installing
        if self.__th.is_alive() is True:
            raise RuntimeError("The installation is already running.")

        self.__installer.set_progress(progress)

        # Log
        logging.info("--- Selected features for installation ---")
        for ftype in ("deps", "lang", "annot", "spin"):
            ids = self.__installer.features_ids(ftype)
            enabled = [fid for fid in ids if self.__installer.enable(fid)]
            logging.info(f"{ftype}: {len(enabled)} is {enabled}")

        # Start the installation process
        # It is not allowed to be stopped, only killed with the app
        self.__errors = ""
        self.__th = Thread(target=self.__install_features)
        self.__th.daemon = True  # If the main thread is killed, this thread will be killed as well.
        self.__th.start()

    # -----------------------------------------------------------------------
    # The method for the thread -- private
    # -----------------------------------------------------------------------

    def __install_features(self):
        """Install all the enabled features, of any type."""
        self.__errors = self.__installer.install()
