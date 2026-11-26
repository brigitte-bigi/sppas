"""
:filename: sppas.src.plugins.manager.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The plugins manager: manage the list of plugins.

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
import os
import shutil
import traceback
import logging
import zipfile
import sys
from threading import Thread

from sppas.core.config import paths
from sppas.core.coreutils import info
from sppas.core.coreutils import u
from sppas.core.config import sppasExecProcess
from sppas.src.utils import sppasDirUtils

from .pluginsexc import PluginArchiveFileError
from .pluginsexc import PluginArchiveIOError
from .pluginsexc import PluginDuplicateError
from .pluginsexc import PluginConfigFileError
from .pluginsexc import PluginIdError
from .pluginsexc import PluginFolderError
from .pluginsexc import PluginKeyError
from .plugin import sppasPluginParam

# ----------------------------------------------------------------------------


class sppasPluginsManager(Thread):
    """Class to manage the list of plugins into SPPAS.

    """

    def __init__(self):
        """Instantiate the sppasPluginsManager and load the current plugins."""
        Thread.__init__(self)

        # Set the plugin path in which plugins can be found
        self.__plugin_path = paths.plugins

        # Load the installed plugins
        self._plugins = {}
        if self.__init_plugin_dir() is True:
            self.load()

        # To get progress information while executing a plugin
        self._progress = None

        # Start threading
        self.start()

    # ------------------------------------------------------------------------

    def get_plugins_path(self) -> str:
        """Return the path of installed plugins"""
        return self.__plugin_path

    # ------------------------------------------------------------------------

    def get_plugin_ids(self):
        """Get the list of plugin identifiers.

        :return: List of plugin identifiers.

        """
        return self._plugins.keys()

    # ------------------------------------------------------------------------

    def get_plugin(self, plugin_id):
        """Get the sppasPluginParam from a plugin identifier.

        :return: sppasPluginParam matching the plugin_id or None

        """
        return self._plugins.get(plugin_id, None)

    # ------------------------------------------------------------------------

    def set_progress(self, progress):
        """Fix the progress system to be used while executing a plugin.

        :param progress: (TextProgress or ProcessProgressDialog)

        """
        self._progress = progress

    # ------------------------------------------------------------------------

    def load(self):
        """Load all installed plugins in the SPPAS directory.

        A plugin is not loaded if:

            - a configuration file is not defined or corrupted,
            - the platform system of the command does not match.

        """
        folders = self.__get_plugins()
        for plugin_folder in folders:
            try:
                self.append(plugin_folder)
            except Exception as e:
                logging.error("Plugin {:s} loading error: {:s}"
                              "".format(plugin_folder, str(e)))
                logging.debug(traceback.format_exc())

    # ------------------------------------------------------------------------

    def install(self, plugin_archive, plugin_folder):
        """Install a plugin into the plugin directory.

        :param plugin_archive: (str) File name of the plugin to be installed (ZIP).
        :param plugin_folder: (str) Destination folder name of the plugin to be installed.

        """
        if zipfile.is_zipfile(plugin_archive) is False:
            raise PluginArchiveFileError

        plugin_dir = os.path.join(self.__plugin_path, plugin_folder)
        if os.path.exists(plugin_dir):
            raise PluginDuplicateError

        # Create the plugin folder and make it a python package
        os.mkdir(plugin_dir)
        with open(os.path.join(plugin_dir, "__init__.py"), "w") as fd:
            fd.write("# File automatically created by SPPAS.")
            fd.close()

        # Unzip the plugin into the directory
        with zipfile.ZipFile(plugin_archive, 'r') as z:
            restest = z.testzip()
            if restest is not None:
                raise PluginArchiveIOError
            z.extractall(plugin_dir)

        try:
            plugin_id = self.append(plugin_folder)
        except Exception:
            shutil.rmtree(plugin_dir)
            raise

        return plugin_id

    # ------------------------------------------------------------------------

    def delete(self, plugin_id):
        """Delete a plugin of the plugin's directory.

        :param plugin_id: (str) Identifier of the plugin to delete.

        """
        p = self._plugins.get(plugin_id, None)
        if p is not None:
            shutil.rmtree(p.get_directory())
            del self._plugins[plugin_id]
        else:
            raise PluginIdError(plugin_id)

    # ------------------------------------------------------------------------

    def append(self, plugin_folder):
        """Append a plugin in the list of plugins.

        It is supposed that the given plugin folder name is a folder of the
        plugin directory.

        :param plugin_folder: (str) The folder name of the plugin.

        """
        # Fix the full path of the plugin
        if "win32" in sys.platform:
            plug_path = self.__plugin_path.replace(os.sep, os.sep+os.sep)
            plugin_folder = plugin_folder.replace(os.sep, os.sep+os.sep)
            plugin_path = plug_path + os.sep + os.sep + plugin_folder
        else:
            plugin_path = os.path.join(self.__plugin_path, plugin_folder)
        logging.info("Folder of the plugin: {:s}".format(plugin_path))
        if os.path.exists(plugin_path) is False:
            raise PluginFolderError(plugin_path)

        # Find a file with the extension .json
        f = self.__get_config_file(plugin_path)
        if f is None:
            logging.error("No json file was found in the plugin folder.")
            raise PluginConfigFileError

        # Create the plugin instance
        p = sppasPluginParam(plugin_path, f)
        plugin_id = p.get_key()

        # Append in our list
        if plugin_id in self._plugins.keys():
            raise PluginKeyError
        logging.info('Plugin {:s} successfully installed.'.format(f))

        self._plugins[plugin_id] = p
        return plugin_id

    # ------------------------------------------------------------------------

    def run_plugin(self, plugin_id, file_names):
        """Apply a given plugin on a list of files.

        :param plugin_id: (str) Identifier of the plugin to apply.
        :param file_names: (list) List of files on which the plugin has to be applied.

        """
        if self._progress is not None:
            self._progress.set_header(plugin_id)
            self._progress.update(0, "")

        if plugin_id not in self._plugins.keys():
            raise PluginIdError(plugin_id)

        output_lines = ""
        total = len(file_names)
        for i, pfile in enumerate(file_names):

            # Indicate the file to be processed
            if self._progress is not None:
                self._progress.set_text(
                    os.path.basename(pfile) +
                    " ("+str(i+1) + "/" +
                    str(total)+")")
            output_lines += (info(4010, "plugins")).format(filename=pfile)
            output_lines += "\n"

            # Apply the plugin
            said, status = self.run_plugin_on_file(plugin_id, pfile)
            output_lines += said

            # Indicate progress
            if self._progress is not None:
                self._progress.set_fraction(float((i+1))/float(total))
            output_lines += "\n"

        # Indicate completed!
        if self._progress is not None:
            self._progress.update(1, info(4020, "plugins") + "\n")

        return output_lines

    # ------------------------------------------------------------------------

    def run_plugin_on_file(self, plugin_id, filename):
        """Apply a given plugin on a file.

        The plugin is applied with the values its options hold.

        :param plugin_id: (str) Identifier of the plugin to apply.
        :param filename: (str) Name of the file on which the plugin has to be applied.
        :raises: PluginIdError: No plugin has that identifier
        :return: (tuple) What the plugin said, and the code it returned -- None if it could not be executed

        """
        if plugin_id not in self._plugins.keys():
            raise PluginIdError(plugin_id)

        # Apply the plugin
        status = None
        command = self._plugin_command(self._plugins[plugin_id], filename)
        try:
            p = sppasExecProcess()
            p.run(command)
            stdout = p.out()
            result = u(p.error().strip())
            status = p.status()
            logging.info("Command return code is {}".format(status))
            if len(stdout) > 3:
                logging.info(stdout)
        except Exception as e:
            result = str(e)

        # Interpret the output result
        if len(result) == 0:
            said = info(4015, "plugins")
        else:
            try:
                said = u(result)
            except Exception as e:
                said = info(4100, "plugins")
                logging.info(str(e))
                logging.info(result)

        return said, status

    # ------------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------------

    def _plugin_command(self, plugin_param, filename):
        """Return the command to run when plugin is applied on given filename.

        :param filename: (str) Name of the input file
        :return: (str)

        """
        # the command
        command = plugin_param.get_command()

        # append the options (sorted like in the configuration file)
        for opt in plugin_param.get_options():
            opt_id = opt.get_key()

            if opt_id == "input":
                command += " \'" + filename + "\' "

            elif opt_id == "options":
                value = opt.get_untypedvalue()
                if len(value) > 0:
                    command += " " + value

            elif opt_id == "output":
                value = opt.get_untypedvalue()
                if len(value) > 0:
                    fname = os.path.splitext(filename)[0]
                    command += " \'" + fname + value + "\' "

            elif opt.get_type() == "bool":
                value = opt.get_value()
                if value is True:
                    command += " " + opt.get_key()

            else:
                value = opt.get_untypedvalue()
                if len(value) > 0:
                    command += " " + opt.get_key()
                    if value == "input":
                        command += " \'" + filename + "\' "
                    elif "file" in opt.get_type():
                        command += " \'" + value + "\' "
                    else:
                        command += " " + value

        logging.debug("Execute the command: {:s}".format(command))
        return command

    # -----------------------------------------------------------------------

    def __init_plugin_dir(self):
        """Create the plugin directory if any."""
        if os.path.exists(self.__plugin_path):
            return True
        try:
            os.makedirs(self.__plugin_path)
        except OSError as e:
            logging.error(f"Failed to create plugin directory {self.__plugin_path}: {str(e)}")
            return False
        else:
            return True

    # ------------------------------------------------------------------------

    def __get_plugins(self):
        """Return a list of plugin folders."""
        folders = list()
        for entry in os.listdir(self.__plugin_path):
            entry_path = os.path.join(self.__plugin_path, entry)
            if os.path.isdir(entry_path):
                folders.append(entry)

        return folders

    # ------------------------------------------------------------------------

    @staticmethod
    def __get_config_file(plugin_dir):
        """Return the config file of a given plugin."""
        sd = sppasDirUtils(plugin_dir)

        # Find a file with the extension .json, and only one
        jsonfiles = sd.get_files(extension=".json", recurs=False)
        if len(jsonfiles) > 0:
            logging.info("Configuration file: {:s}".format(jsonfiles[0]))
            return jsonfiles[0]

        return None
