# -*- coding : UTF-8 -*-
"""
:filename: sppas.preinstall.installer.py
:author: Brigitte Bigi
:contributor: Florian Hocquet
:contact: contact@sppas.org
:summary: Multi-platform installer system of SPPAS dependencies

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

import logging
import shlex
import os
import time
import zipfile
import tarfile
import sys
import traceback
import re
import urllib
import http

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from sppas.core.config import cfg
from sppas.core.coreutils import info
from sppas.core.config import paths
from sppas.core.config import sppasExecProcess
from sppas.core.coreutils.makeunicode import u
from sppas.core.coreutils.exceptions import sppasInstallationError

from .features import Features

# ---------------------------------------------------------------------------


def _info(identifier):
    return info(identifier, "globals")


MESSAGES = {
    "beginning_feature": _info(510),
    "available_false": _info(520),
    "enable_false": _info(530),
    "install_success": _info(540),
    "install_failed": _info(550),
    "install_finished": _info(560),
    "does_not_exist": _info(570),
}

# -----------------------------------------------------------------------


def quote(s):
    """Return a shell-escaped version of the string *s*."""
    try:
        return shlex.quote(s)
    except AttributeError:  # python < 3.3
        _find_unsafe = re.compile(r'[^\w@%+=:,./-]', re.UNICODE).search

        if not s:
            return "''"
        if _find_unsafe(s) is None:
            return s

        # use single quotes, and put single quotes into double quotes
        # the string $'b is then quoted as '$'"'"'b'
        return "'" + s.replace("'", "'\"'\"'") + "'"

# -----------------------------------------------------------------------


class Installer:
    """Manage the installation of external required or optional features.

        It will browse the Features() to install, according to the OS of
        the computer. Must be sub-classed to create the appropriate Features().
        Then, the installation is launched with:

        >>> class SubInstaller(Installer):
        >>>     def __init__(self):
        >>>         super(SubInstaller, self).__init__()
        >>>         self._features = Features(req="", cmdos="")
        >>> SubInstaller().install()

        # TODO:
        # Update this class for Python >= 3.9 only.
        # Remove legacy Python 2.7 compatibility code.
        # Replace any "pip show" / subprocess-based package inspection
        # with importlib.metadata for installed package versions.
        # Use urllib.request to query PyPI.

    """

    def __init__(self):
        """Create a new Installer instance. """
        # Progression: a progress bar, the percentage value, the nb of features.
        self.__pbar = None
        self.__pvalue = 0
        self.__nb_steps = -1

        # The features to be installed
        self._features = None

        # The python command to be used to install with pip
        self._python = self.__search_python_cmd()
        logging.info(" ... the 'installer' is using the Python command: {:s}"
                     "".format(self._python))

        # Update pip before any further installation.
        self.update_pip()

    # ------------------------------------------------------------------------

    def __search_python_cmd(self):
        """Search for a valid python command. Raise SystemError if not found."""
        logging.info("Search for a 'python' command that this installer can launch...")

        # it should be the currently executed one
        logging.info(" ... Try: {:s}".format(sys.executable))
        command = quote(sys.executable)
        command += " -c 'import sys; print(sys.version_info.major)' "

        pyprocess = sppasExecProcess()
        try:
            pyprocess.run(command)
            out = pyprocess.out().replace("b'", "")
            out = out.replace("'", "")
            out = out.strip()
            logging.info("Command returned: {}".format(out))
            if len(out) == 1:
                return quote(sys.executable)

        except Exception as e:
            logging.error(str(e))

        # if not, which should never happen... try something else!
        command = "python3 -c 'import sys; print(sys.version_info.major)' "
        logging.info(" ... Try: python3")
        try:
            pyprocess.run(command)
            out = pyprocess.out().strip()
            out = out.replace("b'", "")
            out = out.replace("'", "")
            out = out.strip()
            logging.info("Command returned: {}".format(out))
            if len(out) == 1:
                pyversion = int(out)
                if pyversion == 3:
                    return "python3"
        except Exception as e:
            logging.error(str(e))

        command = "python -c 'import sys; print(sys.version_info.major)' "
        logging.info(" ... Try: python")
        try:
            pyprocess.run(command)
            out = pyprocess.out().replace("b'", "")
            out = out.replace("'", "")
            out = out.strip()
            logging.info("Command returned: {}".format(out))
            if len(out) == 1:
                pyversion = int(out)
                if pyversion == 3:
                    return "python"
        except Exception as e:
            logging.error(str(e))

        raise SystemError("No valid python command can be invoked by the "
                          "installer system.")

    # ------------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------------

    def set_progress(self, progress):
        """Set the progress bar.

        :param progress: (BaseProcessProgress) The installation progress.

        """
        # Here, we should test if instance is ok
        self.__pbar = progress

    # ------------------------------------------------------------------------

    def get_fids(self, feat_type=None):
        """Return the list of feature identifiers.

        :param feat_type: (str) Only return features of the given type.
        :returns: (list)

        """
        if feat_type is None:
            return self._features.get_ids()

        f = list()
        for fid in self._features.get_ids():
            if self.feature_type(fid) == feat_type:
                f.append(fid)
        return f

    # ------------------------------------------------------------------------

    def feature_type(self, fid):
        """Return the feature type: deps, lang, annot.

        :param fid: (str) Identifier of a feature

        """
        ft = self._features.feature_type(fid)
        return ft

    # ------------------------------------------------------------------------

    def enable(self, fid, value=None):
        """Return True if the feature is enabled and/or set it.

        :param fid: (str) Identifier of a feature
        :param value: (bool or None) Enable of disable the feature.

        """
        return self._features.enable(fid, value)

    # ------------------------------------------------------------------------

    def available(self, fid, value=None):
        """Return True if the feature is available and/or set it.

        :param fid: (str) Identifier of a feature
        :param value: (bool or None) Make the feature available or not.

        """
        return self._features.available(fid, value)

    # ------------------------------------------------------------------------

    def description(self, fid):
        """Return the long description of the feature.

        :param fid: (str) Identifier of a feature
        :return: (str)

        """
        return self._features.description(fid)

    # ------------------------------------------------------------------------

    def brief(self, fid):
        """Return the brief description of the feature.

        :param fid: (str) Identifier of a feature
        :return: (str)

        """
        return self._features.brief(fid)

    # ------------------------------------------------------------------------

    def update_pip(self):
        """Update the version of pip.

        """
        logging.info("Update pip, the package installer for Python:")
        try:
            process = sppasExecProcess()
            # At least one of these two should work.
            # --break-system-packages was introduced with version 23.0.1
            process.run(self._python + " -m pip install --upgrade pip --break-system-packages")
            process.run(self._python + " -m pip install --upgrade pip")
        except:
            try:
                process = sppasExecProcess()
                process.run(self._python + " -m pip install --upgrade pip")
                process.run(self._python + " -m pip install --upgrade pip --break-system-packages")
            except Exception as e:
                raise sppasInstallationError(str(e))

    # ------------------------------------------------------------------------

    def ckeck_pypis(self):
        """Update the app config file for features depending on pip packages.

        CAUTION: it is supposed that if the PIP dependency is satisfied, the
        feature can be enabled. It is currently True but it could be false...

        :param fid: (str) Identifier of a feature
        :raises: sppasInstallationError

        """
        for fid in self._features.get_ids("deps"):
            for package, version in self._features.pypi(fid).items():
                cfg.set_feature(fid, self._show_pypi(package))
        cfg.save()

    # ------------------------------------------------------------------------

    def install(self, feat_type=None):
        """Launch the installation process.

        None is used to install all feature types.

        :param feat_type: (str or None) Install features of the given type.
        :return: (list) Error messages.

        """
        try:
            return self.__install(feat_type)
        except Exception as e:
            return str(e)

    # ------------------------------------------------------------------------

    def __install(self, feat_type=None):
        """Really process the installation.

        None is used to install all feature types.

        :param feat_type: (str or None) Install features of the given type.
        :return: (list) Error messages.

        """
        errors = list()
        self.__pvalue = 1
        self.__nb_steps = len(self._features.get_ids(feat_type))

        for step, fid in enumerate(self._features.get_ids(feat_type)):
            self.__pheader(self.__message("beginning_feature", fid))

            if self._features.available(fid) is False:
                pmesg = "available_false"

            elif self._features.enable(fid) is False:
                # force to add a package dependency into the .app~ file.
                # even if not enabled. it'll help manual edit of the file.
                if self._features.feature_type(fid) == "deps":
                    if cfg.feature_installed(fid) is False:  # -> already False or unknown
                        cfg.set_feature(fid, False)
                pmesg = "enable_false"

            else:
                # Either install the feature, or update it.
                try:
                    fid_output = self.__install_feature(fid)
                    if len(fid_output) > 0:
                        msg = "Installation of feature {} returned information message(s): " \
                              "".format(fid)
                        errors.append(fid_output)
                        logging.warning(msg + fid_output)

                except sppasInstallationError as e:
                    self._features.enable(fid, False)
                    pmesg = "install_failed"
                    if self._features.feature_type(fid) == "deps":
                        cfg.set_feature(fid, False)
                    errors.append(str(e))
                    logging.error(str(e))

                except NotImplementedError:
                    self._features.available(fid, False)
                    self._features.enable(fid, False)
                    pmesg = "install_failed"
                    msg = "Installation of feature {} is not implemented yet " \
                          "for this os.".format(fid)
                    errors.append(msg)
                    logging.error(msg)

                except Exception as e:
                    logging.debug(traceback.format_exc())
                    self._features.enable(fid, False)
                    pmesg = "install_failed"
                    msg = "An un-expected error occurred: {}".format(str(e))
                    errors.append(msg)
                    logging.error(msg)

                else:
                    self._features.enable(fid, True)
                    cfg.set_feature(fid, True)
                    pmesg = "install_success"

            self.__pvalue = int(100. * float(step+1) / self.__nb_steps)
            self.__pupdate(pmesg, fid)

        cfg.save()
        return errors

    # ------------------------------------------------------------------------
    # Private methods to install
    # ------------------------------------------------------------------------

    def __install_feature(self, fid):
        """Install the given feature depending on its type.

        """
        ft = self._features.feature_type(fid)
        out_msg = list()
        if ft == "deps":

            # At first, the packages are installed on the OS, then pipy
            # packages are installed, then the command is executed

            if len(self._features.packages(fid)) > 0:
                out_install = self.__install_packages(fid)
                if len(out_install) > 0:
                    out_msg.append(out_install)

            if len(self._features.pypi(fid)) > 0:
                try:
                    out_install = self.__install_pypis(fid)
                    if len(out_install) > 0:
                        out_msg.append(out_install)
                except sppasInstallationError as e:
                    # Try with an alternative package --
                    # like, for example, PyAudio is an alternative to sounddevice.
                    try:
                        out_install = self.__install_pypis(fid, alt=True)
                        if len(out_install) > 0:
                            out_msg.append(out_install)
                    except sppasInstallationError as e_alt:
                        logging.error(str(e_alt))
                        raise sppasInstallationError(str(e))

            if len(self._features.cmd(fid)) > 0:
                out_install = self.__install_cmd(fid)
                if len(out_install) > 0:
                    out_msg.append(out_install)

        elif ft == "lang":
            self.__install_lang(fid)

        elif ft == "annot":
            self.__install_annot(fid)

        elif ft == "spin":
            self.__install_spin(fid)

        else:
            self._features.available(fid, False)
            raise sppasInstallationError("Unknown feature type {}.".format(fid))

        return "\n\n".join(out_msg)

    # ------------------------------------------------------------------------

    def __install_lang(self, fid):
        """Download, unzip and install resources for a given language.

        :param fid: (str) Identifier of a feature
        :raises: sppasInstallationError

        """
        self.__pmessage("Download, unzip and install linguistic resources for {} language".format(fid))
        url = paths.url_lang_resources
        if url.endswith("/") is False:
            url += "/"
        Installer.install_resource(url, self._features.lang(fid) + ".zip", paths.resources)

    # ------------------------------------------------------------------------

    def __install_annot(self, fid):
        """Download, unzip and install resources for a given annotation.

        :param fid: (str) Identifier of a feature
        :raises: sppasInstallationError

        """
        self.__pmessage("Download, unzip and install resources for {} annotation".format(fid))
        url = paths.url_annot_resources
        if url.endswith("/") is False:
            url += "/"
        Installer.install_resource(url, self._features.annot(fid) + ".tar", paths.resources)

    # ------------------------------------------------------------------------

    def __install_spin(self, fid):
        """Install a spin-off from its zip archive with targeted folders.

        Expected archive structure:
            - sppas/...     [expected]
            - resources/... [optional]
        Any other entry (file or folder) is ignored.

        Behavior:
            - All entries under "sppas/" are extracted into the spin-off
              installation directory (paths.basedir or equivalent).
            - All entries under "resources/" are extracted into the global
              resources directory defined by paths.resources.
            - If the archive contains only "sppas/", it is installed normally.
            - No other top-level directories are supported.

        :param fid: (str) Identifier of the spin-off archive to install.
        :raises: sppasInstallationError

        """
        self.__pmessage("Download, unzip and install spin-off {}".format(fid))
        url = self._features.spin_url(fid)
        if url.endswith("/") is False:
            url += "/"
        _file_path = "".join([self._features.spin(fid), "-", self._features.spin_version(fid), ".zip"])

        err, tmp_file = Installer.download_resource(url, _file_path, paths.basedir)
        if len(err) > 0:
            raise sppasInstallationError(err)

        # Unzip with routing:
        # - sppas/*     -> paths.basedir
        # - resources/* -> paths.resources
        try:
            with zipfile.ZipFile(tmp_file, 'r') as zf:

                # Extract files.
                for info in zf.infolist():
                    name = info.filename

                    # Skip directories (they will be created implicitly).
                    if name.endswith("/"):
                        continue

                    if name.startswith("resources/"):
                        target_root = paths.resources
                        relative_path = name[len("resources/"):]

                    elif name.startswith("sppas/"):
                        target_root = paths.sppas
                        relative_path = name[len("sppas/"):]

                    else:
                        logging.warning(f"Spin-off {fid}. Ignored entry because outside 'sppas/' "
                                        f"or 'resources/': {name}")
                        continue

                    # Skip empty relative path (defensive, explicit).
                    if relative_path == "":
                        continue

                    # Ensure destination folder exists, then write the file.
                    target_path = os.path.join(target_root, relative_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(info, 'r') as src, open(target_path, 'wb') as dst:
                        dst.write(src.read())

        except sppasInstallationError:
            raise
        except Exception as e:
            logging.debug(traceback.format_exc())
            raise sppasInstallationError(str(e))

        # Remove the downloaded zip if everything succeeded.
        if os.path.exists(tmp_file) is True:
            os.remove(tmp_file)

    # ------------------------------------------------------------------------

    @staticmethod
    def install_resource(web_url, file_path, destination):
        """Install the given tar/zip file in the destination path of SPPAS.

        :param web_url: (str) URL of the repo directory
        :param file_path: (str) Tar/Zip filename to download and install
        :param destination: (str) Destination path

        """
        err, tmp_file = Installer.download_resource(web_url, file_path, destination)
        if len(err) == 0:
            # Uncompress the downloaded resource file
            if tmp_file.lower().endswith("zip") is True:
                err = Installer.__unzip(tmp_file, destination)
            elif tmp_file.lower().endswith("tar") is True:
                err = Installer.__untar(tmp_file, destination)
            else:
                err = ("Unsupported file extension for file {:s}. Expected zip or tar."
                       "").format(tmp_file)

        if os.path.exists(tmp_file) is True and len(err) == 0:
            os.remove(tmp_file)
        if len(err) > 0:
            raise sppasInstallationError(err)

    # ------------------------------------------------------------------------

    @staticmethod
    def download_resource(web_url, file_path, destination):
        """Install the given tar/zip file in the destination path of SPPAS.

        :param web_url: (str) URL of the repo directory
        :param file_path: (str) Tar/Zip filename to download and install
        :param destination: (str) Destination path

        """
        # Annot resources migrated to SourceForge and the URL to download a file
        # is ending by "/download"
        url = web_url + file_path
        url += "/download" if "sourceforge" in web_url else ""
        logging.debug("Downloading resource from: {}".format(url))
        logging.debug("Installing it to: {}".format(destination))

        tmp_file = os.path.join(destination, file_path)
        err = Installer.__download(url, tmp_file)
        return err, tmp_file

    # ------------------------------------------------------------------------

    @staticmethod
    def __download(url, tmp_file):
        """Download the resource at given url and save into the tmp_file.

        :param url: (str) URL of the resource
        :param tmp_file: (str) Filename of the temporary file to download into
        :return: (str) Error message (if any)

        """
        err = ""
        try:
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=60)
            data = response.read()
        except urllib.error.URLError as e:
            logging.debug(traceback.format_exc())
            if hasattr(e, 'reason'):
                err = "Failed to establish a connection to the url {}: {}" \
                      "".format(url, e.reason)
            elif hasattr(e, 'code'):
                err = "The web server couldn't fulfill the request for url {}. " \
                      "Error code: {}".format(url, e.code)
            else:
                err = "Unknown connection error."
        except http.client.IncompleteRead:
            logging.debug(traceback.format_exc())
            err = ("The server closed the connection before sending the complete file. "
                   "The file can be downloaded at the following URL: {} and "
                   "uncompressed in {}.").format(url, paths.resources)
        except Exception as e:
            logging.debug(traceback.format_exc())
            err = str(e)

        else:
            # Everything is fine. Download the file.
            err = ""
            try:
                with open(tmp_file, 'wb') as out_file:
                    # shutil.copyfileobj(response, out_file)
                    out_file.write(data)
            except:  # http.client.HTTPException:
                # See: https://github.com/urllib3/urllib3/issues/1874
                logging.debug(traceback.format_exc())
                # Try to read the file in a different way.
                try:
                    zipped = response.read()
                    with open(tmp_file, "wb") as f:
                        f.write(zipped)
                except Exception as e:  # http.client.HTTPException as e:
                    logging.debug(traceback.format_exc())
                    err = str(e)
            response.close()

        if len(err) > 0 and REQUESTS_AVAILABLE is True:
            # Fallback to 'requests' external library (if standard request failed)
            chunk_size = 1024 * 1024    # 1 Mo
            # Use 'requests' if available
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                with open(tmp_file, 'wb') as out_file:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        out_file.write(chunk)
            except requests.exceptions.RequestException as e:
                err = f"Failed to download file using requests: {e}"

        return err

    # ------------------------------------------------------------------------

    @staticmethod
    def __unzip(zip_filename, dest):
        try:
            z = zipfile.ZipFile(zip_filename)
            z.extractall(dest)
            z.close()
        except zipfile.error as e:
            logging.debug(traceback.format_exc())
            return str(e)

        return ""

    # ------------------------------------------------------------------------

    @staticmethod
    def __untar(tar_filename, dest):
        try:
            with tarfile.open(tar_filename, "r") as tf:
                tf.extractall(path=dest)
        except Exception as e:
            logging.debug(traceback.format_exc())
            return str(e)

        return ""

    # ------------------------------------------------------------------------

    def __install_cmd(self, fid):
        """Execute a system command for a feature.

        :param fid: (str) Identifier of a feature
        :raises: sppasInstallationError

        """
        command = self._features.cmd(fid)
        logging.info("The installer is testing the command '{}' for feature {}".format(command, fid))
        try:
            process = sppasExecProcess()
            process.run(command)
            err = u(process.error().strip())
            stdout = process.out()
            logging.info("Command return code is {}".format(process.status()))
            if len(stdout) > 3:
                logging.info(stdout)
        except Exception as e:
            raise sppasInstallationError(str(e))

        # if len(err) > 3:
        #      raise sppasInstallationError(err)
        # Changed by the following in SPPAS>=4.10:
        if process.status() != 0:
            raise sppasInstallationError(err)

        # and indicates progress of the installed cmd
        # self.__pvalue += (self.__eval_step(fid) // self.__nb_steps)
        # self.__pupdate("install_success", fid)

        return err

    # ------------------------------------------------------------------------

    def __install_packages(self, fid):
        """Manage installation of system packages.

        :param fid: (str) Identifier of a feature
        :raises: sppasInstallationError

        """
        out_cmd = list()
        for package, version in self._features.packages(fid).items():
            logging.info(" ... package: {}".format(package))
            if self._search_package(package) is False:
                logging.info(" ... ... is going to be installed.")
                out_install = self._install_package(package)
                if len(out_install) > 0:
                    out_cmd.append(out_install)

            elif self._version_package(package, version) is False:
                logging.info(" ... ... is going to be updated.")
                try:
                    out_install = self._update_package(package, version)
                    if len(out_install) > 0:
                        out_cmd.append(out_install)
                except Exception as e:
                    logging.error(" ... ... Update failed with the error: {}".format(str(e)))
                    out_cmd.append(str(e))

            else:
                logging.info(" ... ... is already installed and up-to-date.")

            # and indicates progress of the installed of packages
            # it's success: instead an exc was raised!
            self.__pvalue += (self.__eval_step(fid) // self.__nb_steps)
            self.__pupdate("install_success", package+version)

        return "\n".join(out_cmd)

    # ------------------------------------------------------------------------

    def __install_pypis(self, fid, alt=False):
        """Manage the installation of pip packages.

        :param fid: (str) Identifier of a feature
        :param alt: (bool) Install alternative pipys instead of the regular ones.
        :raises: sppasInstallationError

        """
        out_pip = list()
        if alt is False:
            pip_items = self._features.pypi(fid).items()
        else:
            pip_items = self._features.pypi_alt(fid).items()
            if len(pip_items) == 0:
                raise sppasInstallationError("No alternative pip packages found.")

        for package, version in pip_items:
            logging.info(" ... python library: {}".format(package))
            pip_options = self._features.pypi_opt(fid, package)
            if self._show_pypi(package) is False:
                try:
                    logging.info(" ... is going to be installed.")
                    err = self._install_pypi(package, version, pip_options)
                    if len(err) > 0:
                        out_pip.append(err)
                except sppasInstallationError as e:
                    if "DEPRECATION: " in str(e):
                        logging.warning(" ... but returned a warning message. {}".format(str(e)))
                    else:
                        logging.debug(' ... install_pypis re-raise the installation error')
                        raise sppasInstallationError(str(e))

            elif self._version_pypi(package, version) is False:
                try:
                    logging.info(" ... is going to be updated.")
                    self._update_pypi(package, version, pip_options)
                except sppasInstallationError as e:
                    logging.error(" ... but the update failed with the error: {}".format(str(e)))
                    out_pip.append(str(e))

            else:
                logging.info(" ... is already installed and up-to-date.")

            # Under Windows,
            # it takes some time for our changes to be taken into account!
            time.sleep(2)

            self.__pvalue += (self.__eval_step(fid) // self.__nb_steps)
            if self._show_pypi(package) is True:
                self.__pupdate("install_success", package+version)
            else:
                self.__pupdate("install_failed", package+version)

        return "\n".join(out_pip)

    # ------------------------------------------------------------------------
    # Management of package dependencies. OS dependent: must be overridden.
    # ------------------------------------------------------------------------

    def _search_package(self, package):
        """To be overridden. Return True if package is already installed.

        :param package: (str) The system package to search.

        """
        raise NotImplementedError

    # ------------------------------------------------------------------------

    def _install_package(self, package):
        """To be overridden. Install package.

        :param package: (str) The system package to install.
        :returns: False or None

        """
        raise NotImplementedError

    # ------------------------------------------------------------------------

    def _version_package(self, package, req_version):
        """To be overridden. Return True if the package is up to date.

        :param package: (str) The system package to search.
        :param req_version: (str) The minimum version required.

        """
        raise NotImplementedError

    # ------------------------------------------------------------------------

    @staticmethod
    def _need_update_package(stdout_show, req_version):
        """To be overridden. Return True if the package need to be updated.

        :param stdout_show: (str) The stdout of the command.
        :param req_version: (str) The minimum version required.

        """
        raise NotImplementedError

    # ------------------------------------------------------------------------

    def _update_package(self, package, req_version):
        """To be overridden. Update package.

        :param package: (str) The system package to update.
        :returns: False or None

        """
        raise NotImplementedError

    # ------------------------------------------------------------------------
    # Private, for internal use only. Not needed by any sub-class.
    # ------------------------------------------------------------------------

    def __pheader(self, text):
        if self.__pbar is not None:
            self.__pbar.set_header(text)
            self.__pbar.set_fraction(self.__pvalue)
            self.__pbar.set_text("")
        logging.info(" ==> {:d} percents".format(self.__pvalue))
        logging.info("    * * * * *   {}   * * * * * ".format(text))

    def __pmessage(self, text):
        if self.__pbar is not None:
            self.__pbar.set_text(text)
        logging.info("  ==> {text}".format(text=text))

    def __pfraction(self):
        if self.__pbar is not None:
            self.__pbar.set_fraction(self.__pvalue)
        logging.info("  ==> {:d} percents".format(self.__pvalue))

    def __pupdate(self, text, fid):
        """text is either a text or a mid."""
        msg = self.__message(text, fid)
        if self.__pvalue > 95:
            self.__pvalue = 100
        if self.__pbar is not None:
            self.__pbar.update(self.__pvalue, msg)
        logging.info(" ==> {:s} ({:d} percents)".format(str(msg), self.__pvalue))

    def __message(self, mid, fid):
        if mid in MESSAGES:
            return MESSAGES[mid].format(name=fid)
        else:
            return mid

    # ------------------------------------------------------------------------

    def __eval_step(self, fid):
        """Return the percentage of 1 step in progression for a given feature.

        :param fid: (str) Identifier of a feature
        :return: (float)

        """
        nb_total = 0
        ft = self._features.feature_type(fid)
        if ft == "deps":
            nb_cmd = 0
            if len(self._features.cmd(fid)) > 0:
                nb_cmd = 1
            nb_packages = len(self._features.packages(fid))
            nb_pypi = len(self._features.pypi(fid))
            nb_total = nb_cmd + nb_packages + nb_pypi
        elif ft == "annot":
            if len(self._features.annot(fid)) > 0:
                nb_total = 1
        elif ft == "lang":
            if len(self._features.lang(fid)) > 0:
                nb_total = 1

        if nb_total > 0:
            return int(round((1. / float(nb_total)), 2) * 100.)
        return 0

    # ------------------------------------------------------------------------

    def _show_pypi(self, package):
        """Return True if given Pypi package is already installed.

        :param package: (str) The pip package to search.

        """
        try:
            command = self._python + " -m pip show " + package
            process = sppasExecProcess()
            process.run(command)
            logging.debug("Search pypi return status: {}".format(process.status()))
            err = process.error()
            stdout = process.out()
            stdout = stdout.replace("b''", "")

            # pip3 can either:
            #   - show information about the Pypi package,
            #   - show nothing, or
            #   - make an error with a message including 'not found'.
            if len(err) > 3 or len(stdout) == 0:
                return False
        except Exception as e:
            raise sppasInstallationError(str(e))

        return True

    # ------------------------------------------------------------------------

    def _pip_command(self, package, version, options="", args=""):
        """Return the pip command line to install or update a package.

        :param package: (str) The pip package to install or update
        :param version: (str) The version constraint
        :param options: (str) The options of the package, like an index url
        :param args: (str) The arguments of the pip install command
        :return: (str) The command to be executed

        """
        command = self._python + " -m pip install"
        if len(args) > 0:
            command += " " + args
        if len(options) > 0:
            command += " " + options
        command += " '" + package + version + "'"
        if 'env' not in self._python:
            # --user is not compatible with virtual environments
            command += " --user"
        command += " --no-warn-script-location"

        return command

    # ------------------------------------------------------------------------

    def _install_pypi(self, package, version, options=""):
        """Install a Python Pypi package.

        :param package: (str) The pip package to install
        :param version: (str) The version constraint
        :raises: sppasInstallationError
        :return: (str) Error message or empty string

        """
        # Remove the cached version. Instead, pip will use it (even with -U option!)
        command = self._python + " -m pip cache purge"
        process = sppasExecProcess()
        process.run(command)
        logging.debug("python pip cache purge return status: {}".format(process.status()))

        logging.info("Try to install the stable version of {:s} python package.".format(package))
        # Try to download the wheel
        command = self._pip_command(package, version, options, "--only-binary=:all:")

        process = sppasExecProcess()
        process.run(command)
        err = u(process.error().strip())
        stdout = process.out()

        if len(stdout) > 3:
            logging.info(stdout)

        if len(err) > 0:
            if len(options) > 0:
                logging.warning("An error occurred when installing: {} {} (stable)".format(package, version))
                logging.warning("The stable package can't be installed from the official "
                                "python package repository: {:s}.".format(str(err)))
                err = self._install_prerelease_pypi(package, version, options)
            else:
                logging.error("The following error occurred: " + err)
                logging.info(" ... but we'll attempt another way to install the package:")
                # Remove the cached version. Instead, pip will use it (even with -U option!)
                command = self._python + " -m pip cache purge"
                process = sppasExecProcess()
                process.run(command)
                logging.debug(" ... ... python pip cache purge return status: {}".format(process.status()))

                if len(stdout) > 3:
                    logging.info(stdout)

                if len(err) > 0:
                    logging.error("The following error occurred: " + err)
                    logging.info(" ... but we'll attempt a last way to install the package:")
                    # Try (again) then without forcing binary
                    command = self._pip_command(package, version, options)
                    process = sppasExecProcess()
                    process.run(command)
                    err = u(process.error().strip())
                    stdout = process.out()

                    if len(stdout) > 3:
                        logging.info(stdout)

        if len(err) > 0:
            logging.error("The following error occurred: " + err)
            if self._version_pypi(package, version) is False:
                raise sppasInstallationError(err)
            else:
                return err

        return ""

    # ------------------------------------------------------------------------

    def _install_prerelease_pypi(self, package, version, options=""):
        """Install a pre-release version of a Python Pypi package.

        A pre-release is an alpha or beta version, not already released in a
        stable package.

        :param package: (str) The pip package to install
        :param version: (str) The version constraint
        :raises: sppasInstallationError

        """
        # Remove the cached version. Instead, pip will use it (even with -U option!)
        command = self._python + " -m pip cache purge"
        process = sppasExecProcess()
        process.run(command)
        logging.debug("python pip cache purge return status: {}".format(process.status()))

        # Then do the package installation
        logging.info("Try to install a pre-build version of {:s} python package.".format(package))
        command = self._pip_command(package, version, options, "--pre")
        process = sppasExecProcess()
        process.run(command)
        err = u(process.error().strip())
        stdout = process.out()

        if len(stdout) > 3:
            logging.info(stdout)

        if len(err) > 0:
            if self._version_pypi(package, version) is False:
                raise sppasInstallationError(err)
            else:
                return err
        return ""

    # ------------------------------------------------------------------------

    def _version_pypi(self, package, req_version):
        """Returns True if package is up-to-date.

        :param package: (str) The pip package to search.
        :param req_version: (str) The minimum version required.

        """
        try:
            command = self._python + " -m pip show " + package
            process = sppasExecProcess()
            process.run(command)
            logging.debug("Version pypi return status: {}".format(process.status()))
            err = process.error()
            out = process.out()
            if len(err) > 3:
                return False
            return not Installer._need_update_pypi(out, req_version)
        except:
            return False

    # ------------------------------------------------------------------------

    @staticmethod
    def _need_update_pypi(stdout_show, req_version):
        """Return True if the package needs to be updated.

        :param stdout_show: (str) The stdout of the command.
        :param req_version: (str) The minimum version required.

        """
        stdout_show = str(stdout_show)
        req_version = str(req_version)
        version = stdout_show.split("\\r\\n")[1].split(":")[1].replace(" ", "")
        v = ""
        i = 0
        for letter in version:
            if letter.isalpha() is False:
                if letter == ".":
                    i += 1
                if i == 2 or letter == " ":
                    break
                v += letter
            else:
                break

        req_version = req_version.split(";", maxsplit=1)

        comparator = req_version[0]
        comparator += "="

        v = v.strip()
        v = float(v)
        version = float(req_version[1])

        if comparator == ">=":
            return v < version

        raise ValueError("The comparator: " + comparator +
                         " does not refer to a valid comparator")

    # ------------------------------------------------------------------------

    def _update_pypi(self, package, version, options=""):
        """Update package.

        :param package: (str) The pip package to update.
        :param version: (str) The version constraint
        :param options: (str) The options of the package, like an index url
        :raises: sppasInstallationError

        """
        try:
            # Remove the cached version. Instead, pip will use it (even with -U option!)
            command = self._python + " -m pip cache purge"
            process = sppasExecProcess()
            process.run(command)
            logging.debug("python pip cache purge return status: {}".format(process.status()))

            # Then install the requested version!
            command = self._pip_command(package, version, options, "-U")
            process = sppasExecProcess()
            process.run(command)
            logging.debug("Update pypi return status: {}".format(process.status()))
        except Exception as e:
            raise sppasInstallationError(str(e))

        err = u(process.error().strip())
        stdout = u(process.out())
        if len(stdout) > 3:
            logging.info(stdout)

        if len(err) > 0:
            if self._version_pypi(package, version) is False:
                raise sppasInstallationError(err)
            else:
                return err
        return ""

# ---------------------------------------------------------------------------


class WindowsInstaller(Installer):
    """An installer for Microsoft Windows system.

    This WindowsInstaller installer was tested with WindowsInstaller 10.

    """

    def __init__(self):
        """Create a new WindowsInstaller instance."""
        super(WindowsInstaller, self).__init__()
        self._features = Features("req_win", "cmd_win")

    # ------------------------------------------------------------------------

    def _version_package(self, package, req_version):
        """Return True if the package is up to date.

        :param package: (str) The system package to search.
        :param req_version: (str) The minimum version required.

        """
        return True

# ----------------------------------------------------------------------------


class MacOsInstaller(Installer):
    """An installer for MacOS systems.

    """

    def __init__(self):
        """Create a new MacOsInstaller(Installer) instance."""
        super(MacOsInstaller, self).__init__()
        self._features = Features("req_ios", "cmd_ios")

    # ------------------------------------------------------------------------

    def _search_package(self, package):
        """Returns True if package is already installed.

        :param package: (str) The system package to search.
        :return: (bool)

        """
        try:
            package = str(package)
            command = "brew list " + package
            process = sppasExecProcess()
            process.run(command)
            if len(process.out()) > 3:
                return True
            return False
        except Exception as e:
            raise sppasInstallationError(str(e))

    # ------------------------------------------------------------------------

    def _install_package(self, package):
        """Install package.

        :param package: (str) The system package to install.
        :raises: sppasInstallationError
        :return: command output message

        """
        try:
            package = str(package)
            command = "brew install " + package
            process = sppasExecProcess()
            process.run(command)
            err = process.error()
            stdout = process.out()
            if len(stdout) > 3:
                logging.info(stdout)

        except Exception as e:
            raise sppasInstallationError(str(e))

        if len(err) > 3:
            if self._search_package(package) is False:
                raise sppasInstallationError(err)
            # if "Warning: You are using macOS" in err:
            #     if self._search_package(package) is False:
            #         raise sppasInstallationError(err)
            # else:
            #     raise sppasInstallationError(err)
        return err

    # ------------------------------------------------------------------------

    def _version_package(self, package, req_version):
        """Return True if the package is up to date.

        :param package: (str) The system package to search.
        :param req_version: (str) The minimum version required.

        """
        try:
            req_version = str(req_version)
            package = str(package)
            command = "brew info " + package
            process = sppasExecProcess()
            process.run(command)
            err = process.error()
        except Exception as e:
            raise sppasInstallationError(str(e))

        if len(err) > 3:
            raise sppasInstallationError(err)
        stdout = process.out()
        return not self._need_update_package(stdout, req_version)

    # ------------------------------------------------------------------------

    @staticmethod
    def _need_update_package(stdout_show, req_version):
        """Return True if the package need to be update.

        :param stdout_show: (str) The stdout of the command.
        :param req_version: (str) The minimum version required.

        """
        stdout_show = str(stdout_show)
        req_version = str(req_version)
        version = stdout_show.split("\n")[0].split("stable")[1].strip()
        v = ""
        i = 0
        for letter in version:
            if letter.isalpha() is False:
                if letter == ".":
                    i += 1
                if i == 2 or letter == " ":
                    break
                v += letter
            else:
                break

        req_version = req_version.split(";", maxsplit=1)

        comparator = req_version[0]
        comparator += "="

        v = v.strip()
        v = float(v)
        version = float(req_version[1])

        if comparator == ">=":
            return v < version

        raise ValueError("The comparator: " + comparator +
                         " does not refer to a valid comparator")

    # ------------------------------------------------------------------------

    def _update_package(self, package, req_version):
        """Update package.

        :param package: (str) The system package to update.
        :returns: False or None

        """
        try:
            package = str(package)
            command = "brew upgrade " + package
            process = sppasExecProcess()
            process.run(command)
            err = process.error()
            stdout = process.out()
            if len(stdout) > 3:
                logging.info(stdout)
        except Exception as e:
            raise sppasInstallationError(str(e))

        if len(err) > 3:
            if self._version_package(package, req_version) is False:
                raise sppasInstallationError(err)
            # if "Warning: You are using macOS" or "already installed" in err:
            #     if self._version_package(package, req_version) is False:
            #         raise sppasInstallationError(err)
            # else:
            #     raise sppasInstallationError(err)

        return err

# ----------------------------------------------------------------------------
# Linux systems
# ----------------------------------------------------------------------------


class DebianInstaller(Installer):
    """An installer for Debian-based package manager systems.

    This DebianInstaller(Installer) is made for the apt package installer,
    like Debian, Ubuntu or Mint.

    """

    def __init__(self):
        """Create a new DebianInstaller instance."""
        super(DebianInstaller, self).__init__()
        self._features = Features(req="req_deb", cmdos="cmd_deb")

    # -----------------------------------------------------------------------

    def _search_package(self, package):
        """Returns True if package is already installed.

        :param package: (str) The system package to search.

        """
        try:
            command = "dpkg -s " + package
            process = sppasExecProcess()
            process.run(command)
        except Exception as e:
            raise sppasInstallationError(str(e))

        err = process.error()
        if len(err) > 3:
            return False

        return True

    # -----------------------------------------------------------------------

    def _install_package(self, package):
        """Install the given package.

        :param package: (str) The system package to install.
        :returns: command output message

        """
        try:
            # -y option is to answer yes to confirmation questions
            command = "apt install " + package + " -y"
            process = sppasExecProcess()
            process.run(command)
        except Exception as e:
            raise sppasInstallationError(str(e))

        stdout = process.out()
        if len(stdout) > 3:
            logging.info(stdout)

        err = process.error()
        if len(err) > 3 and "WARNING" not in err:
            raise sppasInstallationError(err)

        return err

    # -----------------------------------------------------------------------

    def _version_package(self, package, req_version):
        """Return True if the package is up to date.

        :param package: (str) The system package to search.
        :param req_version: (str) The minimum version required.

        """
        return True

    # -----------------------------------------------------------------------

    @staticmethod
    def _need_update_package(stdout_show, req_version):
        """Return True if the package need to be update.

        :param stdout_show: (str) The stdout of the command.
        :param req_version: (str) The minimum version required.

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def _update_package(self, package, req_version):
        """Update package.

        :param package: (str) The system package to update.
        :returns: False or None

        """
        raise NotImplementedError

# ---------------------------------------------------------------------------


class RpmInstaller(Installer):
    """An installer for RPM-based package manager system.

        :author:       Florian Hocquet
        :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
        :contact:      contact@sppas.org
        :license:      GPL, v3
        :copyright:    Copyright (C) 2011-2020  Brigitte Bigi, CNRS

        This RPM is made for the linux distributions like RedHat, or Suse.

    """

    def __init__(self):
        """Create a new RpmInstaller(Installer) instance."""
        super(RpmInstaller, self).__init__()
        self._features = Features("req_rpm", "cmd_rpm")

    # ------------------------------------------------------------------------

    def _search_package(self, package):
        """Returns True if package is already installed.

        :param package: (str) The system package to search.

        """
        return True

    # ------------------------------------------------------------------------

    def _install_package(self, package):
        """Install the given package.

        :param package: (str) The system package to install.
        :returns: False or None

        """
        raise NotImplementedError

    # ------------------------------------------------------------------------

    def _version_package(self, package, req_version):
        """Return True if the package is up to date.

        :param package: (str) The system package to search.
        :param req_version: (str) The minimum version required.

        """
        return True

    # ------------------------------------------------------------------------

    @staticmethod
    def _need_update_package(stdout_show, req_version):
        """Return True if the package need to be update.

        :param stdout_show: (str) The stdout of the command.
        :param req_version: (str) The minimum version required.

        """
        raise NotImplementedError

    # ------------------------------------------------------------------------

    def _update_package(self, package, req_version):
        """Update package.

        :param package: (str) The system package to update.
        :returns: False or None

        """
        raise NotImplementedError

# ---------------------------------------------------------------------------


class DnfInstaller(Installer):
    """An installer for DNF-based package manager systems.

    This DNF is made for linux distributions like Fedora.

    """

    def __init__(self):
        """Create a new DnfInstaller(Installer) instance."""
        super(DnfInstaller, self).__init__()
        self._features = Features("req_dnf", "cmd_dnf")

    # ------------------------------------------------------------------------

    def _search_package(self, package):
        """Returns True if package is already installed.

        :param package: (str) The system package to search.

        """
        try:
            command = "dnf list --installed " + package
            process = sppasExecProcess()
            process.run(command)
        except Exception as e:
            raise sppasInstallationError(str(e))

        status = process.status()
        err = process.error()
        if status != 0:
            raise sppasInstallationError(err)

        if len(err) >= 1:
            return False

        return True

    # ------------------------------------------------------------------------

    def _install_package(self, package):
        """Install the given package.

        :param package: (str) The system package to install.
        :returns: False or None

        """
        try:
            # -y option is to answer yes to confirmation questions
            command = "dnf install " + package + " -y"
            process = sppasExecProcess()
            process.run(command)
        except Exception as e:
            raise sppasInstallationError(str(e))

        status = process.status()
        err = process.error()
        if status != 0:
            raise sppasInstallationError(err)

        return err

    # ------------------------------------------------------------------------

    def _version_package(self, package, req_version):
        """Return True if the package is up-to-date.

        :param package: (str) The system package to search.
        :param req_version: (str) The minimum version required.

        """
        try:
            command = "dnf check-update " + package
            process = sppasExecProcess()
            process.run(command)
        except Exception as e:
            raise sppasInstallationError(str(e))

        # dnf returns code 100 when there is an update available, see
        # check-update part of dnf's manual for more details
        status = process.status()
        if status != 0 and status != 100:
            raise sppasInstallationError(process.error())

        return status == 0

    # ------------------------------------------------------------------------

    def _update_package(self, package, req_version):
        """Update package.

        :param package: (str) The system package to update.
        :returns: False or None

        """
        try:
            command = "dnf upgrade -y " + package
            process = sppasExecProcess()
            process.run(command)
        except Exception as e:
            raise sppasInstallationError(str(e))

        status = process.status()
        err = process.error()
        if status != 0:
            raise sppasInstallationError(err)

        return err
