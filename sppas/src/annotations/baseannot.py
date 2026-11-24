"""
:filename: sppas.src.annotations.baseannot.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Base class for any SPPAS integration of an automatic annotation.
:license: AGPL, v3

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

import logging
import os
import json

from sppas.core.config import annots
from sppas.core.config import paths
from sppas.core.coreutils import info
from sppas.core.coreutils import sppasExtensionWriteError
from sppas.src.structs import sppasOption
from sppas.src.utils import sppasFileUtils

from .autils import sppasFiles
from .annotationsexc import AnnotationOptionError
from .diagnosis import sppasDiagnosis
from .report import sppasAnnReport

# ---------------------------------------------------------------------------


class sppasBaseAnnotation(object):
    """Base class for any automatic annotation integrated into SPPAS.

    """

    def __init__(self, config, log=None):
        """Base class for any SPPAS automatic annotation.

        Load default options/member values from a configuration file.
        This file must be in paths.etc

        Log is used for a better communication of the annotation process and its
        results. If None, logs are redirected to the default logging system.

        :param config: (str) Name of the configuration file (json) with or without its path.
        :param log: (sppasLog) Human-readable logs.

        """
        # Log messages for the user
        if log is None:
            self.logfile = sppasAnnReport()
        else:
            self.logfile = log

        # The annotation types (standalone, speaker...)
        self.__types = list()
        # The options the annotation can support
        self._options = dict()
        # The name of the annotation
        self.name = self.__class__.__name__

        # The output file extension of the annotation for each filetype out format.
        self._out_extensions = dict()
        self.set_default_out_extensions()

        # Then, fill in the values from a configuration file
        self.__filename = str(config)
        self.__load()

    # -----------------------------------------------------------------------
    # Input and output file name and/or file extension
    # -----------------------------------------------------------------------

    def set_default_out_extensions(self):
        """Return the default output extension of each format.

        The default extension of each format is defined in the config.

        """
        self._out_extensions = dict()
        for filetype in sppasFiles.OUT_FORMATS:
            self._out_extensions[filetype] = sppasFiles.DEFAULT_EXTENSIONS[filetype]

    # -----------------------------------------------------------------------

    def set_out_extension(self, extension, out_format="ANNOT"):
        """Set the extension for a specific out format.

        :param extension: (str) File extension for created files
        :param out_format: (str) One of ANNOT, IMAGE, VIDEO

        """
        all_ext = sppasFiles.get_outformat_extensions(out_format)

        if extension.startswith(".") is False:
            extension = "." + extension

        if extension not in all_ext and len(all_ext) > 0:
            logging.error("Extension {} is not in the {} list.".format(extension, out_format))
            raise sppasExtensionWriteError(extension)

        self._out_extensions[out_format] = extension

    # -----------------------------------------------------------------------

    def fix_out_file_ext(self, output, out_format="ANNOT"):
        """Return the output with an appropriate file extension.

        If the output has already an extension, it is not changed.

        :param output: (str) Base name or filename
        :param out_format: (str) One of ANNOT, IMAGE, VIDEO
        :return: (str) filename

        """
        _, fe = os.path.splitext(output)
        if len(fe) == 0:
            # No extension in the output.
            output = output + self._out_extensions[out_format]

        # If output exists, it is overridden
        if os.path.exists(output) and self.logfile is not None:
            self.logfile.print_message(
                (info(1300, "annotations")).format(output),
                indent=2, status=annots.warning)

        return output

    # -----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern that the annotation uses for its output filename."""
        return self._options.get("outputpattern", "")

    def get_input_patterns(self):
        """List of patterns that the annotation expects for the input filenames.

        :return: (list of str)

        """
        p = list()
        for opt in sorted(self._options):
            if opt.startswith("inputpattern") is True:
                p.append(self._options[opt])
        if len(p) == 0:
            return [""]
        return p

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename.

        By default, the extensions are the annotated files. Can be overridden
        to change the list of supported extensions: they must contain the dot.

        :return: (list of list)

        """
        return [sppasFiles.get_informat_extensions("ANNOT_ANNOT")]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_filetypes() -> list:
        """Types of file the annotation expects for its inputs, one list per input.

        The types are those of sppasFiles, and the inputs are in the order of
        get_input_extensions(): the extensions of an input are some of the
        extensions of its types. By default, the input is an annotated file.
        Can be overridden, together with get_input_extensions().

        :return: (list of list of str)

        """
        return [["ANNOT_ANNOT"]]

    # -----------------------------------------------------------------------

    def get_out_name(self, filename, output_format=""):
        """Return the output filename from the input one.

        Output filename is created from the given filename, the annotation
        output pattern and the given output format (if any).

        :param filename: (str) Name of the input file
        :param output_format: (str) Extension of the output file with the dot
        :returns: (str)

        """
        # remove the extension
        fn, _ = os.path.splitext(filename)

        # remove the existing pattern(s)
        for r in self.get_input_patterns():
            if len(r) > 0 and fn.endswith(r):
                fn = fn[:-len(r)]

        # add the annotation pattern and the extension
        return fn + self.get_output_pattern() + output_format

    # -----------------------------------------------------------------------

    def get_out_name_old(self, filename, output_format=""):
        """Return the output filename from the input one.

        Output filename is created from the given filename, the annotation
        output pattern and the given output format (if any).

        :param filename: (str) Name of the input file
        :param output_format: (str) Extension of the output file with the dot
        :returns: (str)

        """
        # remove the extension
        fn, _ = os.path.splitext(filename)

        # remove the existing pattern
        patterns = self.get_input_patterns()
        r = patterns[0]
        if len(r) > 0 and fn.endswith(r):
            fn = fn[:-len(r)]

        # add the annotation pattern and the extension
        return fn + self.get_output_pattern() + output_format

    # -----------------------------------------------------------------------

    def get_config_filename(self) -> str:
        """Return the name of the JSON configuration file."""
        return self.__filename

    # -----------------------------------------------------------------------
    # Shared methods to fix options and to annotate
    # -----------------------------------------------------------------------

    def __load(self):
        """Fix members from a configuration file.

        """
        if os.path.exists(self.__filename) is False:
            # Use the default path.
            self.__filename = os.path.join(paths.etc, self.__filename)
        if os.path.exists(self.__filename) is False:
            raise IOError('Installation error: the file {:s} to configure '
                          'the automatic annotations does not exist.'
                          ''.format(self.__filename))

        # Read the whole file content
        with open(self.__filename) as cfg:
            dict_cfg = json.load(cfg)

        # Extract options
        for new_option in dict_cfg['options']:
            # Create a sppasOption() instance to convert into the right type
            opt = sppasOption(new_option['id'])
            opt.set_type(new_option['type'])
            opt.set_value(str(new_option['value']))
            # Add key and typed value to the dict of options
            self._options[opt.get_key()] = opt.get_value()

        # Extract other members
        self.name = dict_cfg.get('name', self.__class__.__name__)
        self.__types = dict_cfg.get('anntype', [annots.types[0]])

    # -----------------------------------------------------------------------

    def get_option(self, key):
        """Return the option value of a given key or raise KeyError.

        :param key: (str) Return the value of an option, or None.
        :raises: KeyError

        """
        if key in self._options:
            return self._options[key]
        raise KeyError('{:s} is not a valid option for the automatic '
                       'annotation.'.format(key))

    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options of the annotation from a list of sppasOption().

        :param options: (list of sppasOption)

        """
        for opt in options:
            key = opt.get_key()
            if "pattern" in key:
                self._options[key] = opt.get_value()
            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def get_types(self):
        """Return the list of types this annotation can perform.

        If this annotation is expecting another file, the type allow to
        find it by using the references of the workspace (if any).

        """
        return self.__types

    # -----------------------------------------------------------------------
    # Load the linguistic resources
    # -----------------------------------------------------------------------

    def load_resources(self, *args, **kwargs):
        """Load the linguistic resources."""
        pass

    # -----------------------------------------------------------------------
    # Perform automatic annotation:
    # -----------------------------------------------------------------------

    def run(self, input_files, output=None, **kwargs):
        """Run the automatic annotation process on a given input.

        The input is a list of files the annotation needs: audio, video,
        transcription, pitch, etc.

        Either returns the list of created files if the given output is not
        none, or the created object (often a sppasTranscription) if no
        output was given.

        :param input_files: (list of str) The required and optional input(s)
        :param output: (str) The output name with or without extension
        :param kwargs: The results an annotation estimated on all its inputs
        :returns: (sppasTranscription OR list of created file names)

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def run_for_batch_processing(self, input_files, **kwargs):
        """Perform the annotation on a file.

        This method is called by 'batch_processing'. It fixes the name of the
        output file, and call the run method.

        :param input_files: (list of str) the required input(s) for a run
        :param kwargs: The results an annotation estimated on all its inputs
        :returns: created output file name or None

        """
        if len(input_files) == 0:
            return list()

        # Save a copy of the options ('run' could modify the current ones)
        opt = self._options.copy()

        # Fix the output base name with the appropriate pattern
        if isinstance(input_files[0], (list, tuple)) is True:
            # SPEAKER or INTERACTION
            out_name = self.get_out_name(input_files[0][0])
        else:
            # STANDALONE
            out_name = self.get_out_name(input_files[0])

        # Execute annotation
        try:
            new_files = self.run(input_files, out_name, **kwargs)
        except Exception as e:
            new_files = list()
            self.logfile.print_message(
                "{:s}\n".format(str(e)), indent=2, status=annots.error)

        # Restore the options before returning the result
        self._options = opt
        return new_files

    # -----------------------------------------------------------------------

    def batch_processing(self, file_names, progress=None, **kwargs):
        """Perform the annotation on a bunch of files.

        Can be used by an annotation manager to launch all the annotations on
        all checked files of a workspace in a single process.

        The given list of inputs can then be either:
            - a list of file names: [file1, file2, ...], or
            - a list of lists of file names: [(file1_a, file1_b), (file2_a,)], or
            - a list of mixed files/list of files: [file1, (file2a, file2b), ...].

        :param file_names: (list) List of inputs
        :param progress: ProcessProgressTerminal() or ProcessProgressDialog()
        :param kwargs: The results an annotation estimated on all its inputs
        :return: (list of str) List of created files

        """
        if len(self._options) > 0:
            self.print_options()

        total = len(file_names)
        if total == 0:
            return list()
        files_processed_success = list()
        if progress:
            progress.update(0, "")

        # Execute the annotation for each file in the list
        for i, input_files in enumerate(file_names):
            try:
                inputs = self._fix_inputs(input_files)
            except Exception as e:
                logging.critical(e)
            else:
                self.print_diagnosis(*inputs)
                if progress:
                    progress.set_fraction(round(float(i)/float(total), 2))
                    progress.set_text("{!s:s}".format(*inputs))

                out_names = self.run_for_batch_processing(inputs, **kwargs)
                if out_names is None or (isinstance(out_names, (list, tuple)) and len(out_names) == 0):
                    self.logfile.print_message(info(1306, "annotations"), indent=1, status=annots.info)
                else:
                    files_processed_success.extend([f for f in out_names if f is not None])
                    self.logfile.print_message(out_names[0], indent=1, status=annots.ok)
            self.logfile.print_newline()

        # Indicate completed!
        if progress:
            progress.update(1, (info(9000, "ui").format(len(files_processed_success), total)))

        return files_processed_success

    # -----------------------------------------------------------------------

    @staticmethod
    def transfer_metadata(from_trs, to_trs):
        """Transfer the metadata from a sppasTranscription to another one.

        The identifier is not copied and any already existing metadata is
        not copied.

        """
        for key in from_trs.get_meta_keys():
            if to_trs.get_meta(key, default=None) is None:
                to_trs.set_meta(key, from_trs.get_meta(key))

    # -----------------------------------------------------------------------

    def _fix_inputs(self, input_files):
        """Return a list of input files.

        The given input files can be:

            - a single input: file1
            - several inputs: (file1_a, file1_b)

        :param input_files: (str, list of str)
        :returns: a list of files

        """
        if len(input_files) == 0:
            raise Exception(" ******* A non-empty list of input files was expected.")

        # Most frequently, a single file is given.
        # Can concern only STANDALONE annotation type.
        if isinstance(input_files, (list, tuple)) is False:
            return [input_files]

        return input_files

    # -----------------------------------------------------------------------
    # To communicate with the interface:
    # -----------------------------------------------------------------------

    def print_filename(self, filename):
        """Print the annotation name applied on a filename in the user log.

        :param filename: (str) Name of the file to annotate.

        """
        if self.logfile:
            fn = os.path.basename(filename)
            self.logfile.print_message(
                (info(1056, "annotations")).format(fn), indent=0, status=None)
        else:
            logging.info((info(1056, "annotations")).format(filename))

    # -----------------------------------------------------------------------

    def print_options(self):
        """Print the list of options in the user log.

        """
        self.logfile.print_message(info(1050, "annotations") + ": ",
                                   indent=0, status=None)

        for k, v in self._options.items():
            msg = " ... {!s:s}: {!s:s}".format(k, v)
            self.logfile.print_message(msg, indent=0, status=None)

        self.logfile.print_newline()

    # -----------------------------------------------------------------------

    def print_diagnosis(self, *filenames):
        """Print the diagnosis of a list of files in the user report.

        :param filenames: (list) List of files.

        """
        for filename in filenames:
            if filename is not None:
                if isinstance(filename, (list, tuple)) is True:
                    self.print_diagnosis(*filename)
                elif os.path.exists(filename) is True:
                    fn = os.path.basename(filename)
                    (s, m) = sppasDiagnosis.check_file(filename)
                    msg = (info(1056, "annotations")).format(fn) + ": {!s:s}".format(m)
                    self.logfile.print_message(msg, indent=0, status=None)

    # ------------------------------------------------------------------------
    # Utility methods:
    # ------------------------------------------------------------------------

    @staticmethod
    def _get_filename(filename, extensions):
        """Return a filename corresponding to one of the extensions.

        :param filename: input file name
        :param extensions: the list of expected extension
        :returns: a file name of the first existing file with an expected extension or None

        """
        base_name = os.path.splitext(filename)[0]
        for ext in extensions:
            ext_filename = base_name + ext
            new_filename = sppasFileUtils(ext_filename).exists()
            if new_filename is not None and os.path.isfile(new_filename):
                return new_filename

        return None
