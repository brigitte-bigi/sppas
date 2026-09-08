# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.main_settings.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The main settings of the SPPAS Web-based Applications.

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
import json
import logging

from sppas.core.config import paths

# ---------------------------------------------------------------------------


class sppasWebAppSettings:
    """Manage the web-based application global settings.

    """

    def __init__(self):
        """Create or load the dictionary of settings for the application.

        It fixes the relative path to its default value: "sppas/ui/swapp/".

        """
        # Ensure all private members will be set
        self.reset()
        # Load the existing stored ones.
        self.load()

        # Fix relative path from the web server launcher path, to the 'statics' folder.

        # Get the current working directory (where the script is launched from)
        cwd = os.getcwd()

        # Define the absolute path to the 'statics' folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sppas_root = os.path.abspath(os.path.join(script_dir, "../../../"))
        static_path = os.path.join(sppas_root, "sppas/ui/swapp/")

        # Compute the relative path
        relative_static_path = os.path.relpath(static_path, cwd)

        # Set the dynamically determined relative path
        self.set_relative_path(relative_static_path)

    # -----------------------------------------------------------------------

    def get_relative_path(self) -> str:
        """Return the relative path from the server launcher path.

        Relative path from the web server launcher path, to the 'statics' folder
        where CSS, JS, fonts, etc. are located.

        """
        return self.__relative_path


    def set_relative_path(self, path: str):
        """Set the relative path from the server launcher path, to the 'statics' folder.

        Fixing this path ensures "whakerexa" and "statics" can be used by any server.

        :param path: (str) The relative path

        """
        # Normalize the provided path with UNIX-style separators
        self.__relative_path  = os.path.normpath(path).replace(os.sep, "/").rstrip("/")

        if self.__relative_path[-1] != "/":
            self.__relative_path += "/"

        # In case the server was launched from a sub-folder, i.e. a folder inside 'swapp'
        launch_dir_list = os.getcwd().split(os.sep)
        launch_dir = "/".join(launch_dir_list)
        if launch_dir.endswith("sppas/ui/swapp") is True:
            # Launching the UI from here.
            self.__relative_path = ""
        elif launch_dir.endswith("sppas/ui") is True:
            # Launching the UI from parent.
            self.__relative_path = "swapp/"
        elif launch_dir.endswith("sppas") is True:
            self.__relative_path = "ui/swapp/"

        logging.info("Launching directory: {:s}".format(launch_dir))
        logging.info(f"Relative path to statics: {self.__relative_path}")

        # Fix folders inside this relative path
        self.__reset_to_relative_path()

    relative_path = property(get_relative_path, set_relative_path, None)

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        self.save()

    # -----------------------------------------------------------------------
    # Setters
    # -----------------------------------------------------------------------

    def set(self, key, value):
        """Set a new value to a key.

        :param key: (str) A key of this class dictionary
        :param value: (any)

        """
        setattr(self, key, value)

    # -----------------------------------------------------------------------

    def reset(self):
        """Fill in the dictionary with the default values.

        Set all members but relative path.

        """
        # The 'dict' of the class contains the user preferences.
        self.__dict__ = dict(
            # What the reader chose to be shown with, written with the words
            # the client announces them with and carried in the address of the
            # pages. An empty value is the way SPPAS is shown by default. An
            # application bringing its own theme does not change any of them.
            accessibility_theme="",
            accessibility_color="",
            accessibility_contrast="",

            # The lastly used httpd port
            hport=80,

            # License agreement
            license_agreement=False,

            # Host and Port to communicate with the wxapp
            shost="127.0.0.1",
            sport=9669
        )

        # Not modifiable members -- not loaded/saved.
        # Fix the name of the file with the stored settings
        wapp_dir = os.path.dirname(os.path.abspath(__file__))
        self.__filename = os.path.join(paths.ext_dir, ".webapp~")
        self.__base_dir = os.path.dirname(os.path.abspath(__file__))

    # -----------------------------------------------------------------------

    def __reset_to_relative_path(self):
        """Fix folders inside the relative path."""
        self.__wexa = self.__relative_path + "whakerexa/wexa_statics/"
        self.__statics = self.__relative_path + "statics/"
        self.__css = self.__statics + "css/"
        self.__fonts = self.__statics + "fonts/"
        self.__js = self.__statics + "js/"
        self.__icons = self.__statics + "icons/"
        self.__images = self.__statics + "images/"
        self.__logos = self.__statics + "logos/"

    # -----------------------------------------------------------------------
    # Getters
    # -----------------------------------------------------------------------

    @staticmethod
    def default_colors_scheme():
        """The color scheme a page is shown with when none was chosen."""
        return "light"

    # -----------------------------------------------------------------------

    @staticmethod
    def default_page():
        """The page the server answers with when the address names none."""
        return "dashboard.html"

    # -----------------------------------------------------------------------
    # Get access directly to the defined relative paths.

    @property
    def base_dir(self):
        return self.__base_dir

    @property
    def wexa_statics(self):
        return self.__wexa

    @property
    def statics(self):
        return self.__statics

    @property
    def css(self):
        return self.__css

    @property
    def fonts(self):
        return self.__fonts

    @property
    def icons(self):
        return self.__icons

    @property
    def images(self):
        return self.__images

    @property
    def logos(self):
        return self.__logos

    @property
    def js(self):
        return self.__js

    # -----------------------------------------------------------------------
    # Manage the file with settings: load from, save to.
    # -----------------------------------------------------------------------

    def load(self):
        """Load the dictionary of settings from a dump file.

        """
        if os.path.exists(self.__filename):
            try:
                with open(self.__filename, "r") as fd:
                    d = json.load(fd)
                    self.__parse(d)
                    logging.info("Web-based application settings loaded from {:s}"
                                 "".format(self.__filename))
            except Exception as e:
                logging.error("Web-based application settings not loaded: {:s}. "
                              "Reset to default.".format(str(e)))
                self.reset()

        else:
            logging.info("No web-based application settings file defined. "
                         "Set settings to default.")
            self.reset()

    # -----------------------------------------------------------------------

    def save(self):
        """Save the dictionary of settings in a file.

        """
        try:
            with open(self.__filename, 'w') as fd:
                json.dump(self.serialize(), fd, indent=4, separators=(',', ': '))
            logging.info("Settings saved successfully in file {:s}".format(self.__filename))
        except Exception as e:
            logging.error("The settings were not saved due to the following"
                          "error: {:s}.".format(str(e)))

    # -----------------------------------------------------------------------

    def serialize(self):
        """Convert this setting dictionary into a serializable data structure.

        :returns: (dict) a dictionary that can be serialized (without classes).

        """
        d = dict()
        for k in self.__dict__:
            # save only members of the dict in reset,
            # but do not save added members.
            if k.startswith("_" + self.__class__.__name__) is False:
                v = self.__dict__[k]
                d[k] = v

        return d

    # -----------------------------------------------------------------------

    def __parse(self, d):
        """Fill in the internal dictionary with data in the given dict.

        :param d: (dict) a dictionary that can be serialized (without classes).

        """
        self.reset()
        for k in d:
            if k not in self.__dict__:
                # A preference SPPAS does not have any more.
                continue
            v = d[k]
            if isinstance(v, type(self.__dict__[k])) is False:
                # A preference that changed of nature since it was saved:
                # what the file says is dropped and the default is kept.
                continue
            setattr(self, k, v)
