"""
:filename: sppas.src.annotations.param.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Parametrization of automatic annotations.

.. _This file is part of SPPAS: <https://sppas.org/>
..
    ---------------------------------------------------------------------

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

    ---------------------------------------------------------------------

"""

from __future__ import annotations
import logging
import json
import os
import sys

from sppas.core.config import paths
from sppas.core.config import annots
from sppas.core.coreutils import msg
from sppas.core.coreutils import sppasTypeError
from sppas.core.coreutils import sppasIOError

from sppas.src.structs import sppasOption
from sppas.src.structs import sppasLangResource
from sppas.src.structs.structsexc import LangNameError
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from .autils import sppasFiles

# ----------------------------------------------------------------------------


class annotationParam(object):
    """Annotation data parameters.

    Class to store meta data of an automatic annotation like its name,
    description, supported languages, etc.

    """

    def __init__(self, filename=None):
        """Create a new annotationParam instance.

        :param filename: (str) Annotation configuration file

        """
        # An identifier to represent this annotation
        self.__key = None
        # The name of the annotation
        self.__name = ""
        # The description of the annotation
        self.__descr = ""
        # Name of the instance class of this annotation
        self.__api = None
        # Percentage of development -- in progress (1-99) or done (100)
        self.__devel = 0
        # The types this annotation can support
        self.__types = []
        # The status of the annotation
        self.__enabled = False
        self.__invalid = False
        # The language resource: sppasLangResource()
        self.__resources = list()
        # The list of options
        self.__options = list()
        # The references dict: key=id, value=url
        self.__refs = dict()
        # The keys of the annotations this annotation requires
        self.__requires = list()

        # Fix all members from a given config file
        if filename is not None:
            self.parse(filename)

    # ------------------------------------------------------------------------

    def parse(self, filename):
        """Parse a configuration file to fill members.

        :param filename: (str) Annotation configuration file (.ini)

        """
        if filename.endswith('.json'):
            if os.path.exists(filename) is False:
                # Use the default path.
                filename = os.path.join(paths.etc, filename)
            if os.path.exists(filename) is False:
                raise IOError('Installation error: the file {:s} to configure '
                              'the automatic annotations does not exist.'
                              ''.format(filename))

            # Read the whole file content
            with open(filename) as fg:
                conf = json.load(fg)

            self.__key = conf['id']
            self.__name = msg(conf.get('name', ''), "annotations")  # translate the name
            self.__descr = conf.get('descr', "")
            self.__types = conf.get('anntype', [annots.types[0]])
            self.__api = conf.get('api', None)
            if self.__api is None:
                self.__enabled = False
                self.__invalid = True
            if 'refs' in conf:
                self.__refs = conf["refs"]
            if 'devel' in conf:
                self.__devel = int(conf["devel"])
            if 'required' in conf:
                self.__requires = conf["required"]

            for new_option in conf['options']:
                opt = sppasOption(new_option['id'])
                opt.set_type(new_option['type'])
                opt.set_value(str(new_option['value']))  # dangerous cast
                opt.set_text(msg(new_option.get('text', ''), "annotations"))   # translated
                self.__options.append(opt)

            for new_resource in conf['resources']:
                lr = sppasLangResource()
                try:
                    lr.set(new_resource['type'],
                           new_resource['path'],
                           new_resource.get('name', ''),
                           new_resource['ext'],
                           new_resource.get('lang', True))
                except Exception as e:
                    logging.error(str(e))
                    raise
                self.__resources.append(lr)

        else:
            raise IOError('Unknown extension for filename {:s}'.format(filename))

    # -----------------------------------------------------------------------
    # Setters
    # -----------------------------------------------------------------------

    def set_activate(self, activate):
        """Enable the annotation but only if this annotation is valid.

        :param activate: (bool) Enable or disable the annotation
        :returns: (bool) enabled or disabled

        """
        self.__enabled = activate
        if activate is True and self.__invalid is True:
            self.__enabled = False
        return self.__enabled

    # -----------------------------------------------------------------------

    def set_lang(self, lang, forced=False):
        """Set the language of the annotation, if this latter is accepted.

        :param lang: (str) Language to fix for the annotation
        :param forced: (bool) Force the lang to be assigned.
        :return: (bool) Language is set or not

        """
        if len(self.__resources) > 0:
            try:
                self.__resources[0].set_lang(lang, forced)
            except LangNameError:
                self.__invalid = True
                self.__enabled = False
                return False
        return True

    # -----------------------------------------------------------------------
    # Getters
    # -----------------------------------------------------------------------

    def get_key(self):
        """Return the identifier of the annotation (str)."""
        return self.__key

    # -----------------------------------------------------------------------

    def get_name(self):
        """Return the name of the annotation (str)."""
        return self.__name

    # -----------------------------------------------------------------------

    def get_devel(self):
        """Return the percentage of development (some kind of progress)."""
        return self.__devel

    # -----------------------------------------------------------------------

    def get_types(self):
        """Return the list of types the annotation can support (list of str)."""
        return self.__types

    # -----------------------------------------------------------------------

    def get_descr(self):
        """Return the description of the annotation (str)."""
        return self.__descr

    # -----------------------------------------------------------------------

    def get_activate(self):
        """Return the activation status of the annotation (bool)."""
        return self.__enabled

    # -----------------------------------------------------------------------

    def get_api(self):
        """Return the name of the class to instantiate to perform this annotation."""
        return self.__api

    # -----------------------------------------------------------------------

    def get_reference_identifiers(self):
        """Return the list of identifiers of the references."""
        return list(self.__refs.keys())

    # -----------------------------------------------------------------------

    def get_reference_url(self, id_ref):
        """Return the url of a given reference or an empty string."""
        return self.__refs.get(id_ref, "")

    # -----------------------------------------------------------------------

    def get_requires(self) -> list:
        """Return the keys of the annotations this annotation requires (list of str)."""
        return list(self.__requires)

    # -----------------------------------------------------------------------

    def get_lang(self):
        """Return the language or an empty string or None."""
        if len(self.__resources) > 0:
            for r in self.__resources:
                if r.is_lang_resource():
                    return r.get_lang()

        # this annotation does not require a lang resource to work with
        return None

    # -----------------------------------------------------------------------

    def get_langlist(self):
        """Return the list of available languages (list of str)."""
        if len(self.__resources) > 0:
            return self.__resources[0].get_langlist()
        return []

    # -----------------------------------------------------------------------

    def get_langresource(self):
        """Return the list of language resources."""
        return [r.get_langresource() for r in self.__resources]

    # -----------------------------------------------------------------------

    def get_options(self):
        """Return the list of options of the annotation."""
        return self.__options

    # -----------------------------------------------------------------------

    def get_option(self, step):
        """Return the step-th option."""
        return self.__options[step]

    # -----------------------------------------------------------------------

    def get_option_by_key(self, key):
        """Return an option from its key."""
        for opt in self.__options:
            if key == opt.get_key():
                return opt

    # -----------------------------------------------------------------------

    def set_option_value(self, key, value):
        """Change value of an option.

        :param key: (str) Identifier of the option
        :param value: (any) New value for the option
        :raises: KeyError

        """
        # the option is already in the list, change its value
        for opt in self.__options:
            if key == opt.get_key():
                opt.set_value(value)
                return

        # the option was not found in the list
        raise KeyError("Unknown option {:s} in annotation parameters."
                       "".format(key))

# ---------------------------------------------------------------------------


class sppasParam(object):
    """Annotation parameters manager.

    Parameters of a set of annotations.

    """

    def __init__(self, annotation_keys: list | None = None):
        """Create a new sppasParam instance with default values.

        :param annotation_keys: (list) List of annotations to load. None=ALL.

        """
        # A log file to communicate to the user
        self._report = None

        # Input files to annotate
        self._workspace = sppasWorkspace()

        # The parameters of all the annotations
        self.annotations = []
        self.load_annotations(annotation_keys)

        # New in SPPAS 3.3 -- modified in 3.9
        # The output extension used by any annotations to create files
        self._out_extensions = dict()
        for filetype in sppasFiles.OUT_FORMATS:
            self._out_extensions[filetype] = sppasFiles.DEFAULT_EXTENSIONS[filetype]

    # ------------------------------------------------------------------------

    def load_annotations(self, annotation_files: list | None = None) -> None:
        """Load the annotation configuration files.

        Load from a list of given file names (without path) or from the
        default sppas ui configuration file.

        :param annotation_files: (list) List of annotations to load. None=ALL.

        """
        if not annotation_files or len(annotation_files) == 0:
            self.parse_config_file()

        else:
            for cfg_file in annotation_files:
                logging.debug("Loading annotation configuration file {:s}".format(cfg_file))
                self.__load(os.path.join(paths.etc, cfg_file))

    # ------------------------------------------------------------------------

    def parse_config_file(self) -> None:
        """Parse all the sppasui.*.json files and load annotation configuration files.

        Parse the file JSON config file and the ones of the spin-off to get the list
        of annotations and parse the corresponding "json" file.

        :raises: IOError: The file sppasui.json does not exist

        """
        # Ensure that the main config file is available
        _config = os.path.join(paths.etc, "sppasui.json")
        if os.path.exists(_config) is False:
            raise IOError(f'Installation error: the file {_config} to configure the '
                          'automatic annotations does not exist.')

        # Load spin-off configurations (sppasui*.json)
        for filename in sorted(os.listdir(paths.etc), key=len):
            if filename.startswith("sppasui.") is False:
                continue
            if filename.endswith(".json") is False:
                continue

            # Open the JSON file
            cfg_path = os.path.join(paths.etc, filename)
            try:
                with open(cfg_path) as cfg:
                    _dict_cfg = json.load(cfg)
            except Exception as e:
                logging.error(f'Configuration file {cfg_path} not loaded: {str(e)}')
                continue

            for ann in _dict_cfg.get("annotate", []):
                self.__load(os.path.join(paths.etc, ann["config"]))

    # -----------------------------------------------------------------------

    def __load(self, cfg_file: str) -> annotationParam | None:
        """Load the parameters of an annotation from its configuration file.

        An annotation which cannot be loaded is logged, and not appended.

        :param cfg_file: (str) Name of the configuration file, with its path
        :return: (annotationParam) None if the file could not be loaded

        """
        try:
            a = annotationParam(cfg_file)
            self.annotations.append(a)
            logging.info("Configuration file {:s} loaded.".format(cfg_file))
        except Exception as e:
            a = None
            logging.error('Configuration file {:s} not loaded: {}'
                          ''.format(cfg_file, str(e)))
        return a

    # -----------------------------------------------------------------------
    # Input entries to annotate
    # -----------------------------------------------------------------------

    def get_workspace(self) -> sppasWorkspace:
        """Return the workspace (sppasWorkspace)."""
        return self._workspace

    # -----------------------------------------------------------------------

    def set_workspace(self, wkp: sppasWorkspace) -> None:
        """Set the workspace holding the files to annotate.

        :param wkp: (sppasWorkspace) The workspace
        :raises: sppasTypeError: The given workspace is not a sppasWorkspace

        """
        if isinstance(wkp, sppasWorkspace) is False:
            raise sppasTypeError("sppasWorkspace", type(wkp))
        logging.debug('New data to set in sppasParam. '
                      'Id={:s}'.format(wkp.id))
        self._workspace = wkp

    # -----------------------------------------------------------------------

    def add_to_workspace(self, files: str | list) -> None:
        """Add a list of files or directories into the workspace.

        The state of all the added files is set to CHECKED.

        :param files: (str or list of str)

        """
        if isinstance(files, list) is False:
            try:
                if os.path.isfile(files):
                    objs = self._workspace.add_file(files)
                    if objs is not None:
                        for obj in objs:
                            self._workspace.set_object_state(States().CHECKED, obj)
                    # if the file was already in the list, it was not "added",
                    # so it was not in the returned list of objs.
                    obj = self._workspace.get_object(files)
                    self._workspace.set_object_state(States().CHECKED, obj)

                elif os.path.isdir(files):
                    for f in os.listdir(files):
                        self.add_to_workspace(os.path.join(files, f))

                else:
                    raise sppasIOError(files)
                    # logging.error("No such file or directory: {!s:s}".format(files))

            except Exception as e:
                logging.error('File {!s:s} not added into the workspace: {:s}'
                              ''.format(files, str(e)))
        else:
            for f in files:
                self.add_to_workspace(f)

    # -----------------------------------------------------------------------
    # deprecated:
    # -----------------------------------------------------------------------

    def get_checked_roots(self) -> list:
        """Return the list of entries to annotate (list of str)."""
        roots = self._workspace.get_fileroot_from_state(States().CHECKED) + self._workspace.get_fileroot_from_state(States().AT_LEAST_ONE_CHECKED)
        return [r.id for r in roots]

    # -----------------------------------------------------------------------
    # Procedure Outcome Report file name
    # -----------------------------------------------------------------------

    def set_report_filename(self, filename: str) -> None:
        """Fix the name of the file to save the report of the annotations.

        :param filename: (str) Filename for the Procedure Outcome Report

        """
        self._report = filename

    # -----------------------------------------------------------------------

    def get_report_filename(self) -> str | None:
        """Return the name of the file for the Procedure Outcome Report, or None."""
        return self._report

    # -----------------------------------------------------------------------
    # selected language
    # -----------------------------------------------------------------------

    def set_lang(self, language: str, step: int | None = None, forced: bool = False) -> None:
        """Set the language of the annotation of a step, or of every annotation.

        :param language: (str) The language
        :param step: (int) Annotation step index, None for every annotation
        :param forced: (bool) Force the language to be assigned

        """
        if step is not None:
            self.annotations[step].set_lang(language, forced)
        else:
            for a in self.annotations:
                a.set_lang(language, forced)

    def get_lang(self, step: int | None = None) -> str | None:
        """Return the language of the annotation of a step, or the first one set.

        Without a step, the language of the first annotation which has one,
        other than the undetermined one, is returned, or the undetermined one.

        :param step: (int) Annotation step index, None for any annotation
        :return: (str) The language, empty or None when the annotation has none

        """
        if step is None:
            for a in self.annotations:
                lang = a.get_lang()
                if lang is not None and lang != annots.UNDETERMINED:
                    return a.get_lang()
            return annots.UNDETERMINED
        return self.annotations[step].get_lang()

    def get_langresource(self, step: int) -> list:
        """Return the language resources of the annotation of a step.

        :param step: (int) Annotation step index
        :return: (list)

        """
        return self.annotations[step].get_langresource()

    # ------------------------------------------------------------------------
    # annotations
    # ------------------------------------------------------------------------

    def activate_annotation(self, stepname: str) -> int:
        """Activate the annotation of the given key, if it is valid.

        :param stepname: (str) Key of the annotation
        :return: (int) Index of its step, -1 if no annotation has that key

        """
        for i, a in enumerate(self.annotations):
            if a.get_key() == stepname:
                a.set_activate(True)
                return i
        return -1

    def activate_step(self, step: int) -> None:
        """Activate the annotation of a step, if it is valid.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range

        """
        step = self.__check_step(step)
        self.annotations[step].set_activate(True)

    def disable_step(self, step: int) -> None:
        """Disable the annotation of a step.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range

        """
        step = self.__check_step(step)
        self.annotations[step].set_activate(False)

    def test_step(self, step: int) -> bool:
        """Test if an annotation step can be instantiated without error.

        :param step: (int) Annotation step index.
        :return: (bool) True if the annotation step can be instantiated without raising any exception.

        """
        step = self.__check_step(step)
        a = self.annotations[step]
        try:
            # The classes of the annotations are imported by the package.
            inst_name = getattr(sys.modules[__package__], a.get_api())
            inst_name()
        except:
            return False

        return True

    def get_step_status(self, step: int) -> bool:
        """Return True if the annotation of a step is activated.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (bool)

        """
        step = self.__check_step(step)
        return self.annotations[step].get_activate()

    def get_step_name(self, step: int) -> str:
        """Return the name of the annotation of a step.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (str)

        """
        step = self.__check_step(step)
        return self.annotations[step].get_name()

    def get_step_types(self, step: int) -> list:
        """Return the types the annotation of a step supports.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (list of str)

        """
        step = self.__check_step(step)
        return self.annotations[step].get_types()

    def get_step_descr(self, step: int) -> str:
        """Return the description of the annotation of a step.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (str)

        """
        step = self.__check_step(step)
        return self.annotations[step].get_descr()

    def get_requires(self, step: int) -> list:
        """Return the keys of the annotations the annotation of a step requires.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (list of str) Empty when it requires none

        """
        step = self.__check_step(step)
        return self.annotations[step].get_requires()

    # ------------------------------------------------------------------------

    def get_step_idx(self, annotation_key: str) -> int:
        """Get the annotation step index from an annotation key.

        :param annotation_key: (str)
        :raises: KeyError: No annotation has that key
        :return: (int)

        """
        for i, a in enumerate(self.annotations):
            if a.get_key() == annotation_key:
                return i

        raise KeyError('No configuration file is available for an annotation'
                       'with key {:s}'.format(annotation_key))

    # ------------------------------------------------------------------------

    def __check_step(self, step: int) -> int:
        """Return the given step as an index of the annotations.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (int)

        """
        try:
            step = int(step)
        except TypeError:
            raise sppasTypeError(step, "int")
        if step < 0:
            raise sppasTypeError(step, "unsigned int")
        if len(self.annotations) <= step:
            raise ValueError("Annotation step index {:d} out of range.".format(step))
        return step

    # ------------------------------------------------------------------------

    def get_step_key(self, step: int) -> str:
        """Return the key of the annotation of a step.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (str)

        """
        step = self.__check_step(step)
        return self.annotations[step].get_key()

    def get_step_numbers(self) -> int:
        """Return the number of annotations (int)."""
        return len(self.annotations)

    def get_steplist(self) -> list:
        """Return the names of the annotations, in their order (list of str)."""
        steps = []
        for i in range(len(self.annotations)):
            steps.append(self.annotations[i].get_name())
        return steps

    def get_langlist(self, step: int = 2) -> list:
        """Return the languages the annotation of a step has resources for.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (list of str)

        """
        step = self.__check_step(step)
        return self.annotations[step].get_langlist()

    def get_step(self, step: int) -> annotationParam:
        """Return the parameters of the annotation of a step.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (annotationParam)

        """
        step = self.__check_step(step)
        return self.annotations[step]

    def get_options(self, step: int) -> list:
        """Return the options of the annotation of a step.

        :param step: (int) Annotation step index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (list of sppasOption)

        """
        step = self.__check_step(step)
        return self.annotations[step].get_options()

    def set_option_value(self, step: int, key: str, value: object) -> None:
        """Change the value of an option of the annotation of a step.

        :param step: (int) Annotation step index
        :param key: (str) Identifier of the option
        :param value: (any) New value of the option
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :raises: KeyError: The annotation has no option of that key

        """
        step = self.__check_step(step)
        self.annotations[step].set_option_value(key, value)

    # -----------------------------------------------------------------------
    # Annotation file output format
    # -----------------------------------------------------------------------

    def get_output_extension(self, out_format: str) -> str:
        """Return the output extension defined for the given out_format.

        :param out_format: (str) Either ANNOT, AUDIO, VIDEO or IMAGE
        :raises: KeyError: Unknown format
        :return: (str) The extension, with its dot

        """
        return self._out_extensions[out_format]

    # -----------------------------------------------------------------------

    def set_output_extension(self, output_ext: str, output_format: str) -> str:
        """Fix the output extension of all the annotations of a given out_format.

        :param output_ext: (str) File extension (with or without a dot)
        :param output_format: (str) Either ANNOT, AUDIO, VIDEO OR IMAGE
        :raises: ValueError: The extension is not one of that format
        :return: (str) the assigned extension

        """
        if not output_ext.startswith("."):
            output_ext = "." + output_ext

        for e in sppasFiles.get_outformat_extensions(output_format):
            if e.startswith(".") is False:
                e = "." + e
            if output_ext.lower() == e.lower():
                self._out_extensions[output_format] = e
                return e

        raise ValueError("{} not in supported extensions of {}"
                         "".format(output_ext, output_format))

    # -----------------------------------------------------------------------
    # Annotation references: URL of the papers // progress
    # -----------------------------------------------------------------------

    def get_ref_ids(self, step: int) -> list:
        """Return a list of identifiers of the reference publications.

        :param step: (int) Annotation index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (list of str)

        """
        step = self.__check_step(step)
        return self.annotations[step].get_reference_identifiers()

    # -----------------------------------------------------------------------

    def get_ref_url(self, step: int, ref_id: str) -> str:
        """Return the URL of the reference publication.

        :param step: (int) Annotation index
        :param ref_id: (str) Identifier of a reference
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (str) Empty if the annotation has no reference of that identifier

        """
        step = self.__check_step(step)
        return self.annotations[step].get_reference_url(ref_id)

    # -----------------------------------------------------------------------

    def get_devel(self, step: int) -> int:
        """Return a percentage of development.

        It is supposed that the annotations which have references are done,
        they're not under development anymore!

        :param step: (int) Annotation index
        :raises: sppasTypeError: The step is not an unsigned integer
        :raises: ValueError: The step is not a number, or it is out of range
        :return: (int) 0=unknown. 1-99=in progress value. 100=done.

        """
        step = self.__check_step(step)
        return self.annotations[step].get_devel()
