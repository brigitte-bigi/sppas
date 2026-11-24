# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.VowelFilter.sppasvowelfilter.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS integration of the filtering of erroneous formant values.

.. _This file is part of SPPAS: <https://sppas.org/>
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
import logging
import os

from sppas.core.config import annots
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoTierInputError
from ..baseannot import sppasBaseAnnotation
from ..searchtier import sppasFindTier
from ..autils import sppasFiles

from .vowel_filter import VowelFilterEstimator
from .vowel_profiles import VowelProfiles

# ----------------------------------------------------------------------------


class sppasVowelFilter(sppasBaseAnnotation):
    """SPPAS integration of the filtering of erroneous formant values.

    Erroneous F1/F2 values are identified with the Mahalanobis distance of
    the tokens to the expected values of their vowel class, as proposed by
    Lancien et al. (2023). Each pair of tiers created by the Formants
    annotation for a method is filtered with its own distributions.

    Such distributions can't be estimated on a file independently of the
    others: they require all the tokens of a corpus. They are then estimated
    by 'batch_processing' on all its files, and given to 'run'.

    """

    def __init__(self, log=None):
        """Create a new sppasVowelFilter instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasVowelFilter, self).__init__("vowelfilter.json", log)

        # The filtering estimator. The distributions it needs are estimated
        # on all the files of the corpus, then given to its methods.
        self.__filter = VowelFilterEstimator(self._options['threshold'])

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if "threshold" == key:
                self.set_threshold(opt.get_value())

            elif "min_occ" == key:
                self.set_min_occ(opt.get_value())

            elif "coda" == key:
                self.set_coda(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------
    # Getters and Setters
    # -----------------------------------------------------------------------

    def get_threshold(self) -> float:
        return self._options['threshold']

    def get_min_occ(self) -> int:
        return self._options['min_occ']

    def get_coda(self) -> bool:
        return self._options['coda']

    # -----------------------------------------------------------------------

    def set_threshold(self, value: float) -> None:
        """Set the maximum distance of a token to the profile of its class.

        :param value: (float) Number of standard deviations
        :raises: TypeError: Given value is not a number.
        :raises: ValueError: Given value is not a positive number.

        """
        self.__filter.set_threshold(value)
        self._options['threshold'] = float(value)

    # -----------------------------------------------------------------------

    def set_min_occ(self, value: int) -> None:
        """Set the number of occurrences a vowel class requires.

        A class with less occurrences has no estimated distribution, so that
        none of its tokens is discarded.

        :param value: (int) Number of occurrences, at least 2
        :raises: TypeError: Given value is not an integer.
        :raises: ValueError: Given value is lower than the lowest accepted one.

        """
        self._options['min_occ'] = VowelProfiles.check_min_tokens(value)

    # -----------------------------------------------------------------------

    def set_coda(self, value: bool) -> None:
        """Set whether the syllable position is part of the vowel class.

        :param value: (bool) Add the position of the vowel to its class

        """
        self._options['coda'] = bool(value)

    # ----------------------------------------------------------------------
    # The vowel filtering is here
    # ----------------------------------------------------------------------

    def convert(self, tier_f1, tier_f2, syll_tier=None, profiles=None, file_id=""):
        """Discard the erroneous formant values of a pair of tiers.

        A value is discarded by assigning it a zero, like the Formants
        annotation is doing. No value is discarded if no distributions are
        given: they are estimated on all the files of a corpus.

        :param tier_f1: (sppasTier) Tier with the F1 values of a method
        :param tier_f2: (sppasTier) Tier with the F2 values of a method
        :param syll_tier: (sppasTier) Tier with time-aligned syllables, or None
        :param profiles: (VowelProfiles) Estimated distributions, or None
        :param file_id: (str) Identifier of the file the tiers come from
        :return: (sppasTier, sppasTier, sppasTier) Filtered F1, F2 and distances

        """
        return self.__filter.filter(profiles, tier_f1, tier_f2, syll_tier, file_id)

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files: list) -> tuple:
        """Return the filename with formants and the one with syllables.

        :param input_files: (list) The inputs of a file root
        :raises: NoTierInputError: No file with formant values
        :return: (str, str) Formants filename and syllables filename or None

        """
        _patterns = self.get_input_patterns()
        _formants_filename = None
        _syll_filename = None

        for filename in input_files:
            _fn, _ = os.path.splitext(filename)
            if _formants_filename is None and _fn.endswith(_patterns[0]) is True:
                _formants_filename = filename
            elif _syll_filename is None and len(_patterns[1]) > 0 and _fn.endswith(_patterns[1]) is True:
                _syll_filename = filename

        if _formants_filename is None:
            logging.error("No file with formant values, i.e. with pattern '{:s}'."
                          "".format(_patterns[0]))
            raise NoTierInputError

        if self._options['coda'] is False:
            return _formants_filename, None

        return _formants_filename, _syll_filename

    # ----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def run(self, input_files, output=None, **kwargs):
        """Run the automatic annotation process on an input.

        Input file is a tuple with 2 files: the file with the formant values
        and the optional one with the time-aligned syllables.

        :param input_files: (list of str) (formants, time-aligned syllables)
        :param output: (str) the output name
        :param kwargs: (VowelProfiles) profiles=the estimated distributions
        :return: (sppasTranscription)

        """
        _profiles = kwargs.get("profiles", None)
        if _profiles is None:
            self.logfile.print_message(
                "No estimated distributions: no value can be discarded.",
                indent=2, status=annots.warning)
        _formants_filename, _syll_filename = self.get_inputs(input_files)
        _pairs, _syll_tier = self.__read_tiers(_formants_filename, _syll_filename)

        # Create the transcription result
        _trs_output = sppasTranscription(self.name)
        _trs_output.set_meta('annotation_result_of', _formants_filename)
        self.__append_filtered(_trs_output, _pairs, _syll_tier, _profiles, _formants_filename)

        # Save in a file
        if output is not None:
            _output_file = self.fix_out_file_ext(output)
            _parser = sppasTrsRW(_output_file)
            _parser.write(_trs_output)
            return [_output_file]

        return _trs_output

    # ----------------------------------------------------------------------
    # Apply the annotation on a set of files
    # -----------------------------------------------------------------------

    def batch_processing(self, file_names, progress=None, **kwargs):
        """Filter the erroneous formant values of a bunch of files.

        The feature distributions are estimated on the tokens of all the
        given files, then each file is annotated with these distributions.

        :param file_names: (list) List of inputs
        :param progress: ProcessProgressTerminal() or ProcessProgressDialog()
        :return: (list of str) List of created files

        """
        if len(file_names) == 0:
            return list()

        # First pass: estimate the distributions on the whole set of files.
        _profiles = self.__collect_profiles(file_names)

        # Then, annotate each file with these distributions.
        return super(sppasVowelFilter, self).batch_processing(
            file_names, progress, profiles=_profiles, **kwargs)

    # ----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-vfilter")

    def get_input_patterns(self):
        """Pattern this annotation expects for its input filename."""
        return [
            self._options.get("inputpattern1", "-formants"),   # formant values
            self._options.get("inputpattern2", "-syll")        # syllables
        ]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename."""
        return [
            sppasFiles.get_informat_extensions("ANNOT_ANNOT"),
            sppasFiles.get_informat_extensions("ANNOT_ANNOT")
        ]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_filetypes() -> list:
        """Types of file the annotation expects for its inputs, one list per input.

        The types are those of sppasFiles, and the inputs are in the order of
        get_input_extensions().

        :return: (list of list of str)

        """
        return [["ANNOT_ANNOT"], ["ANNOT_ANNOT"]]

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __collect_profiles(self, file_names: list) -> VowelProfiles:
        """Return the estimated feature distributions of all the given files.

        The vowels of each file are added to the distributions, then these
        latter are estimated by VowelProfiles.

        :param file_names: (list) List of inputs
        :return: (VowelProfiles) The estimated distributions

        """
        _profiles = VowelProfiles(self._options['min_occ'])
        for input_files in file_names:
            try:
                _inputs = self._fix_inputs(input_files)
                _formants_filename, _syll_filename = self.get_inputs(_inputs)
                _pairs, _syll_tier = self.__read_tiers(_formants_filename, _syll_filename)
            except Exception as e:
                logging.error(str(e))
                continue

            for tier_f1, tier_f2 in _pairs:
                self.__filter.collect(_profiles, tier_f1, tier_f2, _syll_tier,
                                      _formants_filename)

        self.__print_profiles(_profiles.estimate(), _profiles.get_class_names())

        return _profiles

    # -----------------------------------------------------------------------

    def __print_profiles(self, nb_profiles: int, class_names: tuple) -> None:
        """Print the number of estimated distributions in the user log.

        :param nb_profiles: (int) Number of estimated distributions
        :param class_names: (tuple) Names of the collected vowel classes

        """
        self.logfile.print_message(
            "Estimated {:d} distributions of {:d} vowel classes."
            "".format(nb_profiles, len(class_names)),
            indent=1, status=annots.info)
        self.logfile.print_newline()

    # -----------------------------------------------------------------------

    def __append_filtered(self, trs_output, pairs: list, syll_tier: sppasTier,
                          profiles: VowelProfiles, file_id: str) -> None:
        """Add the filtered tiers of each pair of tiers to the result.

        :param trs_output: (sppasTranscription) The result the tiers are added to
        :param pairs: (list) List of (F1 tier, F2 tier)
        :param syll_tier: (sppasTier) Tier with time-aligned syllables, or None
        :param profiles: (VowelProfiles) Estimated distributions, or None
        :param file_id: (str) Identifier of the file the tiers come from

        """
        for tier_f1, tier_f2 in pairs:
            for filtered_tier in self.convert(tier_f1, tier_f2, syll_tier, profiles, file_id):
                trs_output.append(filtered_tier)
            self.__print_filtered(tier_f1)

    # -----------------------------------------------------------------------

    def __print_filtered(self, tier_f1: sppasTier) -> None:
        """Print the result of the last filtered pair of tiers in the user log.

        :param tier_f1: (sppasTier) The filtered tier with the F1 values

        """
        self.logfile.print_message(
            "{:s}: filtered {:d} formant values among {:d}."
            "".format(tier_f1.get_name(), self.__filter.get_nb_filtered(),
                      self.__filter.get_nb_values()),
            indent=2, status=annots.info)

    # -----------------------------------------------------------------------

    @staticmethod
    def __read_tiers(formants_filename: str, syll_filename: str) -> tuple:
        """Return the pairs of tiers with formant values and the syllables.

        :param formants_filename: (str) Name of a file with formant values
        :param syll_filename: (str) Name of a file with syllables, or None
        :raises: NoTierInputError: A tier with formant values is missing
        :return: (list, sppasTier) Pairs of F1/F2 tiers and syllables tier

        """
        _parser = sppasTrsRW(formants_filename)
        _trs_input = _parser.read()

        _pairs = sppasVowelFilter.__get_formant_pairs(_trs_input)
        if len(_pairs) == 0:
            logging.error("No tier with formant values found in {:s}."
                          "".format(formants_filename))
            raise NoTierInputError

        return _pairs, sppasVowelFilter.__read_syll_tier(syll_filename)

    # -----------------------------------------------------------------------

    @staticmethod
    def __get_formant_pairs(trs) -> list:
        """Return the pairs of F1/F2 tiers to be filtered, one of each method.

        The F1 and F2 tiers are storing the values of all the methods as the
        alternative tags of a label: they are the candidate values of the
        formant, not the value of a given method. The tier of a method is
        then required to filter it, and the F1 and F2 tiers are used only if
        the Formants annotation enabled one method, i.e. if it didn't create
        a tier for each of them.

        :param trs: (sppasTranscription) The read formant values
        :return: (list) List of (F1 tier, F2 tier)

        """
        _pairs = list()
        for tier in trs:
            _name = tier.get_name()
            if _name.startswith("F1-") is False:
                continue
            _tier_f2 = trs.find("F2-" + _name[3:], case_sensitive=False)
            if _tier_f2 is not None:
                _pairs.append((tier, _tier_f2))

        if len(_pairs) == 0:
            _tier_f1 = sppasFindTier.formants(trs, "F1")
            _tier_f2 = sppasFindTier.formants(trs, "F2")
            if _tier_f1 is not None and _tier_f2 is not None:
                _pairs.append((_tier_f1, _tier_f2))

        return _pairs

    # -----------------------------------------------------------------------

    @staticmethod
    def __read_syll_tier(syll_filename: str) -> sppasTier:
        """Return the tier with time-aligned syllables of a file.

        :param syll_filename: (str) Name of a file with syllables, or None
        :return: (sppasTier|None)

        """
        if syll_filename is None:
            return None

        _parser = sppasTrsRW(syll_filename)
        _trs_syll = _parser.read()
        _syll_tier = sppasFindTier.aligned_syllables(_trs_syll)
        if _syll_tier is None:
            logging.warning("No tier with time-aligned syllables in {:s}. The "
                            "position of the vowels is ignored.".format(syll_filename))

        return _syll_tier
