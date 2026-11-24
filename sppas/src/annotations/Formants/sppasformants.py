# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.Formants.sppasformants.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS integration of Formants automatic annotation

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
import audioopy.aio

from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasMedia
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata.anndataexc import AnnDataTypeError

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoChannelInputError
from ..annotationsexc import NoTierInputError
from ..annotationsexc import EmptyInputError
from ..annotationsexc import EmptyOutputError
from ..baseannot import sppasBaseAnnotation
from ..searchtier import sppasFindTier
from ..autils import sppasFiles

from .formants import FormantsEstimator

# ----------------------------------------------------------------------------


class sppasFormants(sppasBaseAnnotation):
    """SPPAS integration of the automatic Formants estimator on intervals.

    Estimate the formants of the center of segments, i.e. phonemes.

    """

    def __init__(self, log=None):
        """Create a new sppasRMS instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasFormants, self).__init__("formants.json", log)

        # The formant estimators. None of the methods are actually enabled.
        self.__estimator = FormantsEstimator()

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

            elif "win_length" == key:
                self.set_win_length(opt.get_value())

            elif "order" == key:
                self.set_lpc_order(opt.get_value())

            elif "floor_freq" == key:
                self.set_floor_frequency(opt.get_value())

            elif "praat_max_freq" == key:
                self.set_praat_max_freq(opt.get_value())

            elif "output_type" == key:
                self.set_output_type(opt.get_value())

            elif key in self.__estimator.get_available_method_names():
                self.__estimator.enable_method(key, opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------
    # Getters and Setters
    # -----------------------------------------------------------------------

    def get_threshold(self) -> float:
        return self._options['threshold']

    def get_win_length(self) -> float:
        return self._options['win_length']

    def get_lpc_order(self) -> int:
        return self._options['lpc_order']

    def get_floor_freq(self) -> float:
        return self._options['floor_freq']

    def get_praat_max_freq(self) -> float:
        return self._options['praat_max_freq']

    def get_enabled_method_names(self) -> tuple:
        """Return the list of active method names.

        :return: (tuple) Names of the currently selected methods

        """
        return self.__estimator.get_enabled_method_names()

    # -----------------------------------------------------------------------

    def set_threshold(self, value: int):
        """Set the RMS threshold value: 0 for automatic.

        :param value: (int) RMS value used as volume threshold
        :raises: TypeError: Given value is not an integer.
        :raises: ValueError: Given value must be between a positive integer.

        """
        self.__estimator.set_rms_threshold(value)
        self._options['threshold'] = value

    # -----------------------------------------------------------------------

    def set_win_length(self, value: float):
        """Set a new length of window for the estimation of formant values.

        :param value: (float) Hamming window duration in seconds.
        :raises: TypeError: Given value is not a number.
        :raises: ValueError: Given value must range 0.01 - 0.1.

        """
        self.__estimator.set_win_dur(value)
        self._options['win_length'] = value

    # -----------------------------------------------------------------------

    def set_lpc_order(self, value: int) -> None:
        """Set the LPC order.

        :param value: (int) Order value, between 6 and samplerate/100
        :raises: TypeError: Given value is not an integer.

        """
        self.__estimator.set_order(value)
        self._options['lpc_order'] = value

    # -----------------------------------------------------------------------

    def set_floor_frequency(self, value: float) -> None:
        """Set the minimum frequency to consider for formants.

        :param value: (float)
        :raises: TypeError: Given value is not a number.
        :raises: ValueError: Given value must be between 50 and 500.

        """
        self.__estimator.set_floor_frequency(value)
        self._options['floor_freq'] = value

    # -----------------------------------------------------------------------

    def set_praat_max_freq(self, value: float) -> None:
        """Set the highest frequency the Praat-based methods are analyzing.

        :param value: (float) Frequency in Hz, ranging 1000 - 10000
        :raises: TypeError: Given value is not a number.
        :raises: ValueError: Given value is out of range.

        """
        self.__estimator.set_max_freq(value)
        self._options['praat_max_freq'] = float(value)

    # -----------------------------------------------------------------------

    def set_output_type(self, value: str) -> None:
        """Set the type of output, among center, mean or all.

        :param value: (str) One of the expected output type
        :raises: ValueError: if out_type is invalid.

        """
        self.__estimator.set_output_type(value)

    # -----------------------------------------------------------------------
    # Annotate
    # -----------------------------------------------------------------------

    def get_inputs(self, input_files: list) -> tuple:
        """Return the audio filename and the tier with time-aligned phonemes.

        :param input_files: (list)
        :raise: NoTierInputError
        :return: (str, sppasTier)

        """
        # Get the tier and the channel
        ext = self.get_input_extensions()
        audio_ext = ext[0]
        annot_ext = ext[1]
        tier = None
        audio_filename = None

        for filename in input_files:
            fn, fe = os.path.splitext(filename)

            if audio_filename is None and fe in audio_ext:
                audio_speech = audioopy.aio.open(filename)
                n = audio_speech.get_nchannels()
                audio_speech.close()
                if n != 1:
                    logging.error("An audio file with only one channel was expected.")
                    raise NoChannelInputError()
                audio_filename = filename

            elif tier is None and fe in annot_ext:
                parser = sppasTrsRW(filename)
                trs_input = parser.read()
                tier = sppasFindTier.aligned_phones(trs_input)

        # Check input tier
        if tier is None:
            logging.error("A tier with time-aligned phonemes was not found in "
                          "the given files: {:s}.".format(str(input_files)))
            raise NoTierInputError
        if tier.is_interval() is False:
            logging.error("The tier should be of type: Interval.")
            raise AnnDataTypeError(tier.get_name(), 'IntervalTier')
        if tier.is_empty() is True:
            raise EmptyInputError(tier.get_name())

        # Set the media to the input tier
        extm = os.path.splitext(audio_filename)[1].lower()[1:]
        media = sppasMedia(os.path.abspath(audio_filename), mime_type="audio/"+extm)
        tier.set_media(media)

        return audio_filename, tier

    # ----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        Input file is a tuple with 2 files:
        the audio file and the annotation file

        :param input_files: (list of str) (audio, time-aligned phonemes)
        :param output: (str) the output name
        :return: (sppasTranscription)

        """
        audio_filename, tier = self.get_inputs(input_files)
        tiers = self.__estimator.estimate(audio_filename, tier)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('annotation_result_of', input_files[0])
        for formant_tier in tiers:
            trs_output.append(formant_tier)

        # Save in a file
        if output is not None:
            if len(trs_output) > 0:
                output_file = self.fix_out_file_ext(output)
                parser = sppasTrsRW(output_file)
                parser.write(trs_output)
                return [output_file]
            else:
                raise EmptyOutputError

        return trs_output

    # ----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-formants")

    def get_input_patterns(self):
        """Pattern this annotation expects for its input filename."""
        return [
            self._options.get("inputpattern1", ""),         # audio
            self._options.get("inputpattern2", "-palign")   # intervals
        ]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename."""
        return [
            sppasFiles.get_informat_extensions("AUDIO"),
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
        return [["AUDIO"], ["ANNOT_ANNOT"]]
