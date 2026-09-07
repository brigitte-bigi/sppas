# -*- coding : UTF-8 -*-
"""
:filename: sppas.preinstall.features.py
:author: Brigitte Bigi
:contributor: Florian Hocquet
:contact: contact@sppas.org
:summary: Manager for all the features of SPPAS dependencies.

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
import logging
import configparser as cp

from sppas.core.config import paths
from sppas.core.config import cfg

from .featurecheck import DepsFeatureChecker
from .feature import Feature
from .feature import SpinOffFeature
from .feature import DepsFeature
from .feature import LangFeature
from .feature import AnnotFeature

# ---------------------------------------------------------------------------


class Features:
    """Manager of the list of required external features of the software.

    """

    def __init__(self, req="", cmdos="", filename=None):
        """Create a new Features instance.

        A Features instance is a container for a list of features.
        It parses a '.ini' file to get each feature config. If a filename is
        not specified, the default one will be used.

        :param req: (str)
        :param cmdos: (str)
        :param filename: (str) A custom configuration filename.

        """
        self.__req = req
        self.__cmdos = cmdos
        self.__features = list()
        self.__filename = None
        if filename is not None:
            if os.path.exists(filename) and filename.endswith(".ini"):
                self.__filename = filename

        self.set_features()

    # ------------------------------------------------------------------------

    def get_features_filename(self):
        """Return the name of the file with the features descriptions."""
        if self.__filename is not None:
            return self.__filename

        return os.path.join(paths.etc, "features.ini")

    # ------------------------------------------------------------------------

    def get_ids(self, feat_type=None):
        """Return the list of feature identifiers of the given type.

        :param feat_type: (str) Feature type, or None to get all ids
        :return: (list) Feature identifiers

        """
        if feat_type is None:
            return [f.get_id() for f in self.__features]

        return [f.get_id() for f in self.__features if f.get_type() == feat_type]

    # ------------------------------------------------------------------------

    def feature_type(self, fid):
        """Return the feature type: deps, lang, annot.

        :param fid: (str) Identifier of a feature

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                return feat.get_type()

        logging.error("Unknown feature {}".format(fid))
        return None

    # ------------------------------------------------------------------------

    def enable(self, fid, value=None):
        """Return True if the feature is enabled and/or set it.

        :param fid: (str) Identifier of a feature
        :param value: (bool or None) Enable of disable the feature.

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if value is None:
                    return feat.get_enable()
                return feat.set_enable(value)

        logging.error("Unknown feature {}".format(fid))
        return False

    # ------------------------------------------------------------------------

    def available(self, fid, value=None):
        """Return True if the feature is available and/or set it.

        :param fid: (str) Identifier of a feature
        :param value: (bool or None) Make the feature available or not.

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if value is None:
                    return feat.get_available()
                return feat.set_available(value)

        logging.error("Unknown feature {}".format(fid))
        return False

    # ------------------------------------------------------------------------

    def brief(self, fid):
        """Return the brief description of the feature.

        :param fid: (str) Identifier of a feature

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                return feat.get_brief()

        logging.error("Unknown feature {}".format(fid))
        return None

    # ------------------------------------------------------------------------

    def description(self, fid):
        """Return the description of the feature

        :param fid: (str) Identifier of a feature

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                return feat.get_desc()

        logging.error("Unknown feature {}".format(fid))
        return None

    # ------------------------------------------------------------------------

    def packages(self, fid):
        """Return the dictionary of system dependencies of the feature.

        :param fid: (str) Identifier of a feature
        :return: (dict) key=package; value=version

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, DepsFeature) is True:
                    return feat.get_packages()
                else:
                    logging.error("Feature {} is not a DepsFeature:"
                                  "No packages are defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return dict()

    # ------------------------------------------------------------------------

    def pypi(self, fid):
        """Return the dictionary of pip dependencies of the feature.

        :param fid: (str) Identifier of a feature
        :return: (dict) key=package; value=version

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, DepsFeature) is True:
                    pips = dict()
                    for key in feat.get_pypi_packages():
                        pips[key] = feat.get_pypi_package_version(key)
                    return pips
                else:
                    logging.error("Feature {} is not a DepsFeature:"
                                  "No pypi is defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return dict()

    # ------------------------------------------------------------------------

    def pypi_alt(self, fid):
        """Return the dictionary of alternative pip dependencies of the feature.

        :param fid: (str) Identifier of a feature
        :return: (dict) key=package; value=version

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, DepsFeature) is True:
                    pips = dict()
                    for key in feat.get_pypi_alt_packages():
                        pips[key] = feat.get_pypi_alt_package_version(key)
                    return pips
                else:
                    logging.error("Feature {} is not a DepsFeature:"
                                  "No alt pypi is defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return dict()

    # ------------------------------------------------------------------------

    def pypi_opt(self, fid, package_name=""):
        """Return the options of a pip dependency of the feature.

        :param fid: (str) Identifier of a feature
        :param package_name: (str) Name of a pip package of the feature
        :return: (str)

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, DepsFeature) is True:
                    return feat.get_pip_options(package_name)

        return ""

    # ------------------------------------------------------------------------

    def check_pip_deps(self):
        """Check Python (pip) dependencies for all enabled 'deps' features.

        This method checks each DepsFeature for the presence of required Python modules,
        as specified in the 'pip_test' field (supporting alternatives via '|').
        The feature is set as available if at least one required module (per group) is importable.
        If no module is importable, the feature is set as unavailable and disabled.

        :example:
            > features = Features(filename="/path/to/features.ini")
            > features.check_pip_deps()

        """
        for fid in self.get_pip_test_deps():
            feat = [f for f in self.__features if f.get_id() == fid][0]

            # Only process enabled features
            if feat.get_enable() is False:
                continue

            # Get the pip_test field (should be set during ini parsing)
            pip_test = feat.get_pip_test()
            modules_to_test = self._parse_pip_test(pip_test)
            if modules_to_test is None:
                continue

            try:
                DepsFeatureChecker.check_modules(modules_to_test)
                feat.set_available(True)
            except ImportError:
                feat.set_available(False)
                feat.set_enable(False)
                logging.error(
                    f"Feature '{fid}' disabled: "
                    f"missing Python dependency (see pip_test: '{pip_test}')."
                )

    # ------------------------------------------------------------------------

    def get_pip_test_deps(self):
        """Return the list of deps feature IDs with a non-empty pip_test field.

        :return: (list) List of feature identifiers

        """
        ids = []
        for feat in self.__features:
            if isinstance(feat, DepsFeature) is True:
                # pip_test = feat.get_pip_test()
                pip_test = feat.get_pip_test()
                if pip_test and pip_test.strip() != "":
                    ids.append(feat.get_id())
        return ids

    # ------------------------------------------------------------------------

    def cmd(self, fid):
        """Return the command to execute for the feature.

        :param fid: (str) Identifier of a feature
        :return: (str)

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, DepsFeature) is True:
                    return feat.get_cmd()
                else:
                    logging.error("Feature {} is not a DepsFeature:"
                                  "No cmd is defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return str()

    # ------------------------------------------------------------------------

    def check_cmd_deps(self):
        """Check system command availability for all enabled 'deps' features.

        This method uses the 'cmd_test' field to verify whether the required
        system command is available in the environment. If not found,
        the feature is marked as unavailable and disabled.

        """
        for feat in self.__features:
            # Only process Deps features
            if isinstance(feat, DepsFeature) is False:
                continue

            # Only process enabled features
            if feat.get_enable() is False:
                continue

            # Test only if a test command is given
            test_command = feat.get_cmd_test()
            commands_to_test = self._parse_cmd_test(test_command)
            if commands_to_test is None:
                continue

            available = True
            # All commands in the tuple must succeed
            for cmd in commands_to_test:
                try:
                    DepsFeatureChecker((None, (cmd,))).check()
                except RuntimeError:
                    available = False
                    break

            feat.set_available(available)
            if not available:
                feat.set_enable(False)
                logging.error(
                    f"Feature '{feat.get_id()}' disabled: "
                    f"missing system command (see cmd_test: '{test_command}')."
                )

    # ------------------------------------------------------------------------

    def check_deps(self, test_all=False):
        """Check all dependencies for all enabled 'deps' features.

        Check if both the imports and the commands are available and can
        be enabled for all features, or only the enabled ones.

        :param test_all: (bool) If True, all dependencies are checked, not only the enabled ones

        """
        for feat in self.__features:
            # Only process Deps features
            if isinstance(feat, DepsFeature) is False:
                continue

            # Test all or only enabled ones
            if test_all is False and feat.get_enable() is False:
                continue

            logging.debug("Checking dependencies for feature '{}'".format(feat.get_id()))

            # Get tests of the feature
            test_modules = self._parse_pip_test(feat.get_pip_test())
            test_commands = self._parse_cmd_test(feat.get_cmd_test())

            # Nothing has to be tested for this feature.
            if test_commands is None and test_modules is None:
                continue

            # Test commands and modules:
            # - all commands must be successfully executed
            # - all pip packages must be successfully imported but some of
            #   them can have alternative solutions
            try:
                DepsFeatureChecker((test_modules, test_commands)).check()
                feat.set_available(True)
                feat.set_enable(True)
            except (ImportError, RuntimeError) as e:
                feat.set_available(False)
                feat.set_enable(False)
                logging.info(
                    f"Feature '{feat.get_id()}' disabled: {str(e)}"
                )
                # Do not raise! Just log and disable

    # ------------------------------------------------------------------------

    def lang(self, fid):
        """Return the lang code of the linguistic resource to download.

        :param fid: (str) Identifier of a feature
        :return: (str)

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, LangFeature) is True:
                    return feat.get_lang()
                else:
                    logging.error("Feature {} is not a LangFeature:"
                                  "No lang is defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return str()

    # ------------------------------------------------------------------------

    def annot(self, fid):
        """Return the name the annotation resource to download.

        :param fid: (str) Identifier of a feature
        :return: (str)

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, AnnotFeature) is True:
                    return feat.get_annot()
                else:
                    logging.error("Feature {} is not an AnnotFeature:"
                                  "No annot is defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return str()

    # ------------------------------------------------------------------------

    def spin(self, fid):
        """Return the name of the spin-off resource to download.

        :param fid: (str) Identifier of a feature
        :return: (str)

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, SpinOffFeature) is True:
                    return feat.get_spin()
                else:
                    logging.error("Feature {} is not a SpinOffFeature:"
                                  "No spin is defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return str()

    # ------------------------------------------------------------------------

    def spin_url(self, fid):
        """Return the url of the spin-off resource.

        :param fid: (str) Identifier of a feature
        :return: (str)

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, SpinOffFeature) is True:
                    return feat.get_spin_url()
                else:
                    logging.error("Feature {} is not a SpinOffFeature:"
                                  "No spin is defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return str()

    # ------------------------------------------------------------------------

    def spin_version(self, fid):
        """Return the version of the spin-off resource.

        :param fid: (str) Identifier of a feature
        :return: (str)

        """
        for feat in self.__features:
            if feat.get_id() == fid:
                if isinstance(feat, SpinOffFeature) is True:
                    return feat.get_spin_version()
                else:
                    logging.error("Feature {} is not a SpinOffFeature:"
                                  "No spin is defined.".format(fid))

        logging.error("Unknown feature {}".format(fid))
        return str()

    # ---------------------------------------------------------------------------

    def set_features(self):
        """Browses the features.ini file and instantiate a Feature().

        Only unix-based systems can have package requirements. If they don't,
        the corresponding req_ attribute is missing or empty or with "nil".

        A feature is not available for a system, if none of the corresponding "cmd_"
        and "req_" and the "pip" attributes are defined.

        """
        self.__features = list()
        features_parser = self.__init_features()

        for fid in (features_parser.sections()):
            # Type of the feature
            try:
                feature = self.__set_feature(fid, features_parser)
            except cp.NoOptionError:
                logging.error("Missing or wrong feature type for feature {}"
                              "".format(fid))
                continue

            # Brief description of the feature
            try:
                desc = features_parser.get(fid, "brief")
                feature.set_brief(desc)
            except cp.NoOptionError:
                pass

            # Long description of the feature
            try:
                desc = features_parser.get(fid, "desc")
                feature.set_desc(desc)
            except cp.NoOptionError:
                pass

            # Feature is enabled or not
            try:
                e = features_parser.getboolean(fid, "enable")
                feature.set_enable(e)
            except cp.NoOptionError:
                pass

            # here we should verify if fid is not already in the list of features
            self.__features.append(feature)

        # Disable the installation of the already installed features, but
        # they are still available: they can be updated if selected.
        # ids = self.get_ids()
        # for fid in cfg.get_feature_ids():
        #     if fid in ids:
        #         self.enable(fid, not cfg.feature_installed(fid))
        #     else:
        #         logging.error("The config file contains an unknown "
        #                       "feature identifier {}".format(fid))

    # ------------------------------------------------------------------------

    def __set_feature(self, fid, parser):
        feature = None
        try:
            ft = parser.get(fid, "type")
            if ft == "deps":
                feature = DepsFeature(fid)
                self.__fill_deps_feature(feature, parser)
            if ft == "lang":
                feature = LangFeature(fid)
                self.__fill_lang_feature(feature)
            if ft == "annot":
                feature = AnnotFeature(fid)
                self.__fill_annot_feature(feature)
            if ft == "spin":
                feature = SpinOffFeature(fid)
                self.__fill_spin_feature(feature, parser)
        except cp.NoOptionError:
            pass

        if feature is not None:
            return feature
        raise cp.NoOptionError

    # ------------------------------------------------------------------------

    def __fill_deps_feature(self, feature, parser):
        fid = feature.get_id()
        # System package dependencies
        try:
            d = parser.get(fid, self.__req)
            if len(d) > 0 and d.lower() != "nil":
                depend_packages = self.__parse_depend(d)
                feature.set_packages(depend_packages)
        except cp.NoOptionError:
            pass

        # Pypi dependencies
        try:
            # Regular pip packages
            d = parser.get(fid, "pip")
            if len(d) > 0 and d.lower() != "nil":
                depend_pypi = self.__parse_depend(d)
                for key in depend_pypi:
                    feature.add_pypi(key, depend_pypi[key])
        except cp.NoOptionError:
            pass

        try:
            # Alternative pip package
            d = parser.get(fid, "pip_alt")
            if len(d) > 0 and d.lower() != "nil":
                depend_pypi = self.__parse_depend(d)
                for key in depend_pypi:
                    feature.add_pypi_alt(key, depend_pypi[key])
        except cp.NoOptionError:
            pass

        # Specific options to be applied when installing
        try:
            opt = parser.get(fid, "pip_opt")
            if len(opt) > 0 and opt.lower() != "nil":
                feature.set_pip_options(self.__parse_pip_options(opt))
        except cp.NoOptionError:
            pass

        # Names of imported libraries to be tested (pip_test)
        try:
            pip_test = parser.get(fid, "pip_test")
            if len(pip_test) > 0 and pip_test.lower() != "nil":
                feature.set_pip_test(pip_test)
        except cp.NoOptionError:
            pass

        # Command to be executed
        try:
            cmd = parser.get(fid, self.__cmdos)
            if len(cmd) > 0 and cmd != "none" and cmd != "nil":
                feature.set_cmd(cmd)
        except cp.NoOptionError:
            pass

        # Command line to test the feature (cmd_test)
        try:
            cmd_test = parser.get(fid, "cmd_test")
            if len(cmd_test) > 0 and cmd_test.lower() not in ("none", "nil"):
                feature.set_cmd_test(cmd_test)
        except cp.NoOptionError:
            pass

        # Is available?
        if len(feature.get_cmd()) > 0 or len(feature.get_pypi_packages()) > 0 or len(feature.get_packages()) > 0:
            # It will be turned to True later if required
            # Here, we only say it's existing.
            feature.set_available(True)
            if fid not in cfg.get_feature_ids():
                logging.debug(" -->> newly available feature: {:s}".format(fid))

    # ------------------------------------------------------------------------

    def __fill_lang_feature(self, feature):
        # the identifier of the feature is also the name of the zip file to
        # download and install
        fid = feature.get_id()
        feature.set_lang(fid)
        feature.set_available(True)

    # ------------------------------------------------------------------------

    def __fill_annot_feature(self, feature):
        # the identifier of the feature is also the name of the tar file to
        # download and install
        fid = feature.get_id()
        feature.set_annot(fid)
        feature.set_available(True)
        if fid not in cfg.get_feature_ids():
            cfg.set_feature(fid, False)
            logging.debug(" ----->>> new available feature: {:s}".format(fid))
            # It will be turned to True later if required
            # Here, we only say it's existing.

    # ------------------------------------------------------------------------

    def __fill_spin_feature(self, feature, parser):
        # the identifier of the feature is also the name of the zip file to
        # download and install
        fid = feature.get_id()
        feature.set_spin(fid)

        # URL the spin-off will be downloaded and its version
        try:
            url = parser.get(fid, "url")
            version = parser.get(fid, "version")
            feature.set_spin_url(url)
            feature.set_spin_version(version)
        except:
            logging.error("Missing or invalid url or version for spin-off feature {}"
                          "".format(fid))
            feature.set_available(False)
        else:
            feature.set_available(True)

    # ------------------------------------------------------------------------
    # Private: Internal use only.
    # ------------------------------------------------------------------------

    def __init_features(self):
        """Return a parsed version of the features.ini file.

        """
        cfg_filename = self.get_features_filename()
        if cfg_filename is None or os.path.exists(cfg_filename) is False:
            raise IOError("Installation error: the file {filename} to "
                          "configure the software is missing."
                          .format(filename=cfg_filename))

        features_parser = cp.ConfigParser()
        try:
            features_parser.read(self.get_features_filename())  #, encoding="utf-8")
        except cp.MissingSectionHeaderError:
            raise IOError("Malformed features configuration file {}: "
                          "missing section header.".format(cfg_filename))

        return features_parser

    # ---------------------------------------------------------------------------

    @staticmethod
    def __parse_depend(string_require):
        """Create a dictionary from the string given as an argument.

        :param string_require: (string) The value of one of the req_*** key in one of the section of feature.ini.
        :return: (dict)

        """
        string_require = str(string_require)
        dependencies = string_require.split(" ")
        depend = dict()
        for line in dependencies:
            tab = line.split(":")
            if len(tab) == 1:
                depend[line] = ""
            else:
                # at left of the first ':' there's the package name
                # at right of the first ':' there's version constraints
                depend[tab[0]] = tab[1]
                # With pip<24.x, it was allowed to use brackets:
                # depend[tab[0]] = tab[1:]
        return depend

    # ------------------------------------------------------------------------

    @staticmethod
    def __parse_pip_options(string_options):
        """Create a dictionary from the pip_opt value given as an argument.

        Each line is either the options of a given pip package, in the form
        "package:options", or the options of all the packages of the feature.
        The latter are stored with an empty string as key.

        :param string_options: (string) The value of the pip_opt key in one of the section of features.ini.
        :return: (dict) key=package name or an empty string; value=options

        """
        string_options = str(string_options)
        options = dict()
        for line in string_options.split("\n"):
            line = line.strip()
            if len(line) == 0:
                continue

            # At left of the first ':' there's the package name, but only if
            # this first ':' is part of the package name and not of an option,
            # like in "-f https://wxpython.org/".
            tab = line.split(":", maxsplit=1)
            if len(tab) == 2 and len(tab[0]) > 0 and " " not in tab[0]:
                options[tab[0]] = tab[1].strip()
            else:
                options[""] = line

        return options

    # ------------------------------------------------------------------------

    def _parse_pip_test(self, pip_test_str):
        """Parse a pip_test string into a tuple of tuples (AND/OR structure).

        - If the string contains spaces, each space separates AND groups.
        - Within each group, '|' separates OR alternatives.
        - If there are no spaces but a '|', treat the whole string as one OR group.
        - If there is only one module name, return a single group with one element.

        Examples:
            'a|b c'      -> (('a', 'b'), ('c',))
            'a|b'        -> (('a', 'b'),)
            'a'          -> (('a',),)

        :param pip_test_str: (str|None) The pip_test string from the feature.
        :return: (tuple of tuple of str) or None if input is empty.

        """
        # No dependencies to test
        if pip_test_str is None:
            return None
        pip_test_str = pip_test_str.strip()
        if pip_test_str == "":
            return None

        if ' ' in pip_test_str:
            and_groups = []
            for group in pip_test_str.split():
                or_group = tuple(m.strip() for m in group.split('|') if m.strip())
                and_groups.append(or_group)
            return tuple(and_groups)

        if '|' in pip_test_str:
            or_group = tuple(m.strip() for m in pip_test_str.split('|') if m.strip())
            return (or_group,)

        return ((pip_test_str,),)

    # ------------------------------------------------------------------------

    def _parse_cmd_test(self, cmd_test_str):
        """Parse a cmd_test string into a tuple of commands.

        Parse the cmd_test field and return a tuple of command strings.
        Commands are separated by a semicolon. Each command is stripped of spaces.

        Example:
            "ffmpeg -h;ls" -> ('ffmpeg -h', 'ls')

        :param cmd_test_str: (str|None) The cmd_test string from the feature.
        :return: (tuple of str) or None if input is empty.

        """
        # No commands to test
        if cmd_test_str is None:
            return None
        cmd_test_str = cmd_test_str.strip()
        if cmd_test_str == "":
            return None

        # Split by semicolons and remove empty commands
        return tuple(cmd.strip() for cmd in cmd_test_str.split(";") if cmd.strip() != "")

    # ------------------------------------------------------------------------
    # Overloads
    # ------------------------------------------------------------------------

    def __str__(self):
        """Print each Feature of the list. """
        for f in self.__features:
            print(f.__str__())

    def __format__(self, fmt):
        return str(self).__format__(fmt)

    def __len__(self):
        """Return the number of features."""
        return len(self.__features)

    def __contains__(self, value):
        """Value can be either a Feature or its identifier."""
        if isinstance(value, Feature):
            return value in self.__features
        else:
            for f in self.__features:
                if f.get_id() == value:
                    return True
        return False
