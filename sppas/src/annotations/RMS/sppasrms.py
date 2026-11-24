# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.RMS.sppasrms.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  SPPAS integration of RMS automatic annotation

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

    Copyright (C) 2011-2021  Brigitte Bigi, CNRS
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

from sppas.core.coreutils import sppasUnicode
import audioopy.aio
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasMedia
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata.aio.aioutils import serialize_labels
from sppas.src.anndata.anndataexc import AnnDataTypeError

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoChannelInputError
from ..annotationsexc import NoTierInputError
from ..annotationsexc import EmptyInputError
from ..annotationsexc import EmptyOutputError
from ..baseannot import sppasBaseAnnotation
from ..autils import sppasFiles

from .irms import IntervalsRMS

# ----------------------------------------------------------------------------


class sppasRMS(sppasBaseAnnotation):
    """SPPAS integration of the automatic RMS estimator on intervals.

    Estimate the root-mean-square of segments, i.e. sqrt(sum(S_i^2)/n).
    This is a measure of the power in an audio signal.

    """

    def __init__(self, log=None):
        """Create a new sppasRMS instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasRMS, self).__init__("rms.json", log)
        self.__rms = IntervalsRMS()

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if key == "tiername":
                self.set_tiername(opt.get_value())

            elif key == "minmax":
                self.set_minmax(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------
    # Getters and Setters
    # -----------------------------------------------------------------------

    def set_tiername(self, tier_name):
        """Fix the tiername option.

        :param tier_name: (str)

        """
        self._options['tiername'] = sppasUnicode(tier_name).to_strip()

    # -----------------------------------------------------------------------

    def set_minmax(self, value):
        """Fix the minmax option.

        :param value: (bool) Add 2 more tiers in the result with min and max

        """
        self._options['minmax'] = bool(value)

    # ----------------------------------------------------------------------
    # The RMS estimator is here
    # ----------------------------------------------------------------------

    def convert(self, tier):
        """Estimate RMS on all non-empty intervals.

        :param tier: (sppasTier)

        """
        rms_avg = sppasTier("RMS")
        rms_values = sppasTier("RMS-values")
        rms_mean = sppasTier("RMS-mean")
        rms_min = sppasTier("RMS-min")
        rms_max = sppasTier("RMS-max")
        rms_avg.set_media(tier.get_media())
        rms_values.set_media(tier.get_media())
        rms_mean.set_media(tier.get_media())
        rms_min.set_media(tier.get_media())
        rms_max.set_media(tier.get_media())

        for ann in tier:

            content = serialize_labels(ann.get_labels())
            if len(content) == 0:
                continue

            # Localization of the current annotation
            begin = ann.get_lowest_localization()
            end = ann.get_highest_localization()

            # Estimate all RMS values during this ann
            self.__rms.estimate(begin.get_midpoint(), end.get_midpoint())

            # The global RMS of the fragment between begin and end
            rms_tag = sppasTag(self.__rms.get_rms(), "int")
            rms_avg.create_annotation(ann.get_location().copy(), sppasLabel(rms_tag))

            # All the RMS values (one every 10 ms)
            labels = list()
            for value in self.__rms.get_values():
                labels.append(sppasLabel(sppasTag(value, "int")))
            rms_values.create_annotation(ann.get_location().copy(), labels)

            # The mean RMS of values of the fragment between begin and end
            rms_mean_tag = sppasTag(self.__rms.get_mean(), "float")
            rms_mean.create_annotation(ann.get_location().copy(), sppasLabel(rms_mean_tag))

            # The min RMS value of the fragment between begin and end
            rms_min_tag = sppasTag(self.__rms.get_min(), "float")
            rms_min.create_annotation(ann.get_location().copy(), sppasLabel(rms_min_tag))

            # The max RMS value of the fragment between begin and end
            rms_max_tag = sppasTag(self.__rms.get_max(), "float")
            rms_max.create_annotation(ann.get_location().copy(), sppasLabel(rms_max_tag))

        return rms_avg, rms_values, rms_mean, rms_min, rms_max

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the channel and the tier with ipus.

        :param input_files: (list)
        :raise: NoTierInputError
        :return: (Channel, sppasTier)

        """
        # Get the tier and the channel
        ext = self.get_input_extensions()
        audio_ext = ext[0]
        annot_ext = ext[1]
        tier = None
        channel = None
        audio_filename = ""

        for filename in input_files:
            fn, fe = os.path.splitext(filename)

            if channel is None and fe in audio_ext:
                audio_speech = audioopy.aio.open(filename)
                n = audio_speech.get_nchannels()
                if n == 1:
                    idx = audio_speech.extract_channel()
                    channel = audio_speech.get_channel(idx)
                    audio_filename = filename
                audio_speech.close()

            elif tier is None and fe in annot_ext:
                parser = sppasTrsRW(filename)
                trs_input = parser.read()
                tier = trs_input.find(self._options['tiername'], case_sensitive=False)

        # Check input tier
        if tier is None:
            logging.error("Tier with name '{:s}' not found."
                          "".format(self._options['tiername']))
            raise NoTierInputError
        if tier.is_interval() is False:
            logging.error("The tier should be of type: Interval.")
            raise AnnDataTypeError(tier.get_name(), 'IntervalTier')
        if tier.is_empty() is True:
            raise EmptyInputError(self._options['tiername'])

        # Check input channel
        if channel is None:
            logging.error("No audio file found or invalid one. "
                          "An audio file with only one channel was expected.")
            raise NoChannelInputError

        # Set the media to the input tier
        extm = os.path.splitext(audio_filename)[1].lower()[1:]
        media = sppasMedia(os.path.abspath(audio_filename), mime_type="audio/"+extm)
        tier.set_media(media)

        return channel, tier

    # ----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        Input file is a tuple with 2 files:
        the audio file and the annotation file

        :param input_files: (list of str) (audio, time-aligned items)
        :param output: (str) the output name
        :return: (sppasTranscription)

        """
        channel, tier = self.get_inputs(input_files)
        self.__rms.set_channel(channel)

        # RMS Automatic Estimator
        rms_avg, rms_values, rms_mean, rms_min, rms_max = self.convert(tier)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('annotation_result_of', input_files[0])
        trs_output.append(rms_avg)
        trs_output.append(rms_values)
        trs_output.append(rms_mean)
        if self._options["minmax"] is True:
            trs_output.append(rms_min)
            trs_output.append(rms_max)

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
        return self._options.get("outputpattern", "-rms")

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
