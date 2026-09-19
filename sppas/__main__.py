#!/usr/bin/env python
"""
:filename: sppas.__main__.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: This is the main SPPAS entry point.

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

In Python, '__main__' is the name of the scope in which top-level code
executes. Within SPPAS, it allows to launch the Graphical User Interface.

To launch the Web-based UI, this main file allows the followings 2 solutions:

>>> python3 sppas

"""

# ---------------------------------------------------------------------------
# SPPASAppLauncher: Entry-point for SPPAS.
# This script initializes, launches and handles errors of the SPPAS Dashboard.
# ---------------------------------------------------------------------------

import os
import sys
import logging
import webbrowser
import time
import traceback
from argparse import ArgumentParser

# Set the parent directory of "sppas"
FILE = os.path.abspath(__file__)
sppas_dir = os.path.dirname(os.path.dirname(FILE))

# Adjust sys.path and __package__ for standalone execution
if '__package__' not in globals() or __package__ is None or len(__package__) == 0:
    sys.path.insert(0, sppas_dir)

    # Gestion de __spec__ pour éviter le warning
    if '__spec__' not in globals() or __spec__ is None:
        __package__ = "sppas"  # Définition manuelle de __package__
    else:
        __package__ = __spec__.parent

# Force language environment variable for localization
if os.environ.get("LC_LANG", None) is not None:
    os.environ['LC_LANG'] = "en_US.UTF-8"

# ---------------------------------------------------------------------------


class SPPASAppLauncher:
    """Main class to initialize, configure, and launch the Dashboard app.

    This class is responsible for:

    - Checking Python version compatibility;
    - Importing required SPPAS modules;
    - Handling runtime errors;
    - Starting the main GUI web-based application;
    - Handle error.

    """

    def __init__(self):
        """Create a SPPASAppLauncher instance.

        """
        # Python requirements
        self.__min_py = (3, 9)
        self.__recommended_py = (3, 10)

        # The application to launch
        self.__app = None
        # The list of possible exceptions raised by the app
        self.__exc = tuple()
        # Exit infos: status code, error message and report filename
        self.__report = None
        self.__status = 1
        self.__error_message = "Unknown error."

    # -----------------------------------------------------------------------

    def get_status(self) -> int:
        """Return the current exit status of the launcher."""
        return self.__status

    status = property(get_status, None, None)

    def get_report_filename(self) -> str:
        """Return the filename of the error report log, if any."""
        if self.__report is None:
            return ""
        return self.__report.get_filename()

    report_filename = property(get_report_filename, None, None)

    def get_error_message(self) -> str:
        """Return the error message describing the cause of failure."""
        return self.__error_message

    error_message = property(get_error_message, None, None)

    # ---------------------------------------------------------------------------

    def check_python_version(self) -> str:
        """Check Python version compatibility and print diagnosis on stdout.

        :return: (str) A message if Python is not the expected one

        """
        if sys.version_info < self.__min_py:
            self.__status = 1
            self.__error_message = \
                "[ CRITICAL ] You have to update Python to launch this"\
                " application. SPPAS requires Python >= {:s}"\
                "".format(".".join([str(i) for i in self.__min_py]))
            return self.__error_message

        self.__status = 0
        if sys.version_info < self.__recommended_py:
            return ("[ INFO ] You should consider updating Python to {:s}+."
                    "".format(".".join([str(i) for i in self.__recommended_py])))

        return ""

    # ---------------------------------------------------------------------------

    def set_sppas_language(self, lang: str):
        """Set the message language used by SPPAS.

        :param lang: (str) Language code (e.g., 'en', 'fr').

        """
        sys.path.insert(0, os.path.join(sppas_dir, "core"))
        try:
            from core.config import set_language
            set_language(lang)
        except Exception as _e:
            # Handle import errors and display a helpful message.
            self.__error_message = traceback.format_exc()
            try:
                self.__status = _e.status
            except AttributeError:
                self.__status = 1

    # ---------------------------------------------------------------------------

    def import_and_init(self, arguments):
        """Try to import all required modules and initialize the app.

        """
        try:
            from sppas.core.coreutils import sppasLogFile
            from sppas.core.coreutils import sppasEnableFeatureError
            from sppas.core.coreutils import sppasPackageFeatureError
            from sppas.core.coreutils import sppasPackageUpdateFeatureError
            from sppas.ui.swapp import sppasWebApp
            from sppas.ui.swapp.swappcore.swappsg import swapp_settings
            # Path to the main JSON configuration for WhakerPy.
            json_filename = os.path.join(swapp_settings.get_relative_path(), "swapp.json")
            if os.path.exists(json_filename) is False:
                raise Exception(f"The expected JSON configuration file {json_filename} wasn't found.")

            self.__status = 0
            self.__error_message = ""
            self.__report = sppasLogFile(pattern="dashboard")
            self.__app = sppasWebApp(arguments)
            self.__exc = (sppasEnableFeatureError, sppasPackageFeatureError, sppasPackageUpdateFeatureError)
        except Exception as _e:
            # Handle import errors and display a helpful message.
            self.__error_message = traceback.format_exc()
            try:
                self.__status = _e.status
            except AttributeError:
                self.__status = 1

    # ---------------------------------------------------------------------------

    def run_application(self):
        """Launch the web-based application and handle runtime errors.

        """
        if self.__status != 0 or self.__app is None:
            raise Exception("The import of SPPAS modules wasn't done or failed")

        try:
            # Create the application and start it once. Can stop it with CTRL+C.
            logging.debug("Starting HTTPD server...")
            logging.debug("The server started successfully.")
            logging.debug("Client url is {:s}".format(self.__app.client_url()))

            # Open the web browser at the default location
            logging.warning("----------------------------------------------------------------------")
            logging.warning("              This application was tested with Firefox.               ")
            logging.warning("   Use of this app with another web browser is without any warranty.  ")
            logging.warning("     You can get it here: https://www.mozilla.org/en-US/firefox/      ")
            logging.warning("----------------------------------------------------------------------")
            webbrowser.open_new_tab(self.__app.client_url())

            # Run the application server in a mainloop
            logging.info("Running application in web browser at {:s}".format(self.__app.client_url()))
            logging.info("----------------------------------------------------------------------")
            # logging.info("Enter CTRL+C to quit the application")
            self.__status = self.__app.run()
            logging.debug("Application ended with status: {:d}".format(self.__status))

        except self.__exc as _e:
            self.__status = _e.status
            self.__error_message = traceback.format_exc()
        except:
            self.__status = 1
            self.__error_message = traceback.format_exc()

    # -----------------------------------------------------------------------

    def write_error_report(self):
        """Generate an error report and open it in the browser.

        """
        with open(self.__report.get_filename(), "w") as f:
            f.write(self.__report.get_header())
            f.write(self.__error_message + "\n")
            f.write(f"\nSPPAS application exited with error status: {self.status}.\n")
        webbrowser.open_new_tab(url=self.__report.get_filename())

    # -----------------------------------------------------------------------

    def handle_error(self, report: bool = False):
        """Handle and report an error, then exit the application.

        - Prints the error message to the console.
        - Opens a web page with error documentation for the user.
        - Waits before exiting the program.

        """
        print(f"* * * * *  SPPAS exited with error number: {self.__status:04d}  * * * * * ")
        print(self.__error_message)

        if report is True:
            print(f"A report was generated. See {self.__report.get_filename()} for details.")
            self.write_error_report()
        else:
            try:
                url = f"https://sppas.org/book_08_annexes.html#error-{self.__status:04d}"
                if not webbrowser.open_new_tab(url=url):
                    print(f"Visit the following URL for error details: {url}")
            except Exception as _e:
                print(f"This error occurred while reporting launch error: {_e}")

        # Delay exit so the user can read the message
        time.sleep(10)
        sys.exit(self.__status)


# ---------------------------------------------------------------------------
# The main function to execute the SPPAS application.
#
# - Checks Python version compatibility.
# - Imports required dependencies.
# - Runs the application and handles any errors encountered.
#
# Exits the program with the appropriate status code.
# ---------------------------------------------------------------------------


def parse_args(args: list) -> dict:
    """Parse a list of command-line arguments into a dictionary.

    This function supports both `--key value` and `--key=value` formats.
    If an argument starts with "--" and is not followed by a value or "=",
    it is interpreted as a boolean flag set to True.

    :param args: (list) List of command-line arguments
    :return: (dict) A dictionary mapping option names to their values.

    :example:
    >>> parse_args(["--test", "--config", "file.ini", "--mode=fast"])
    {'test': True, 'config': 'file.ini', 'mode': 'fast'}

    :note: This function does not support short options (e.g., "-k").

    """
    result = {}
    key = None

    for arg in args:
        if arg.startswith("--"):
            if "=" in arg:
                # Format: --key=value
                k, v = arg.lstrip("-").split("=", 1)
                result[k] = v
                key = None
            else:
                # Start of a key expecting a value
                key = arg.lstrip("-")
                result[key] = True  # Default value in case it's a flag
        elif key:
            # Value assigned to previous key
            result[key] = arg
            key = None

    return result

# ---------------------------------------------------------------------------


if __name__ == '__main__':
    """A unique entry point for all the SPPAS web-based applications.

    """
    # Create the application launcher and check python.
    # ------------------------------------------------
    # It can launch any of the available SPPAS-web-based applications. It is
    # used in this program to launch the SPPAS Dashboard Application.
    launcher = SPPASAppLauncher()

    # Print information if Python version is not like expected
    msg = launcher.check_python_version()
    if launcher.status != 0:
        launcher.handle_error()
    if len(msg):
        print(msg)

    # Create a parser for the command-line arguments
    # ----------------------------------------------
    parser = ArgumentParser(
        usage="{:s} [options]".format(os.path.basename(__file__)),
        description="... SPPAS - the automatic annotation and analysis of speech.")

    # add arguments here
    parser.add_argument("-l", "--lang",
                        required=False,
                        type=str,
                        help='Language to be used by SPPAS for messages.')

    # Parse arguments of the command line.
    args, unknown_args = parser.parse_known_args()
    extra_args = parse_args(unknown_args)

    # Fix SPPAS language messages
    # ---------------------------
    if args.lang:
        logging.debug("Requested language is {lang}")
        launcher.set_sppas_language(args.lang)
    else:
        logging.debug("No language specified, using system default.")

    # Import required SPPAS modules and launch the Dashboard
    # ------------------------------------------------------
    launcher.import_and_init(extra_args)
    if launcher.status != 0:
        launcher.handle_error()
    else:
        # Launch the application
        launcher.run_application()
        if launcher.status != 0:
            launcher.handle_error(report=True)
