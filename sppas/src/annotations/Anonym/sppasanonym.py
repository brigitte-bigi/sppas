# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.Anonym.sppasanonym.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  SPPAS integration of the Anonymization automatic annotation.

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

    Copyright (C) 2011-2023  Brigitte Bigi, CNRS
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
import audioopy.aio
from audioopy import AudioPCM

from sppas.core.config import annots
from sppas.core.coreutils import sppasKeyError
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel
from sppas.src.analysis import sppasTierFilters

from ..baseannot import sppasBaseAnnotation
from ..param import sppasParam
from ..annotationsexc import BadInputError
from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoInputError
from ..annotationsexc import NoTierInputError
from ..autils import sppasFiles
from ..FaceDetection import sppasFaceDetection

from .anonymaudio import ChannelAnonymizer
from .anonymvideo import sppasVideoAnonymizer

# ---------------------------------------------------------------------------


class sppasAnonym(sppasBaseAnnotation):
    """Anonymization of media from indicated buzz intervals of a tier.

    """

    FILTERS = ["exact", "contains", "startswith", "endswith", "regexp",
               "iexact", "icontains", "istartswith", "iendswith",
               "not_exact", "not_contains", "not_startswith", "not_endswith",
               "not_iexact", "not_icontains", "not_istartswith", "not_iendswith"]

    def __init__(self, log=None):
        """Create a new sppasAnonym instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasAnonym, self).__init__("anonym.json", log)
        try:
            self._fd = sppasFaceDetection(log)
            parameters = sppasParam(["facedetect.json"])
            step_idx = parameters.activate_annotation("facedetect")
            self._fd.load_resources(*parameters.get_langresource(step_idx), lang=parameters.get_lang())
        except Exception as e:
            logging.error(str(e))
            if log is not None:
                self.logfile.print_message(
                    "Anonymization of video is disabled due to the following error: "
                    "Face detection can't be enabled, {}.".format(str(e)),
                    indent=2, status=annots.warning)
            self._fd = None

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()

            if key == "buzztier":
                self.set_tiername(opt.get_value())

            elif key == "buzzname":
                self.set_buzz(opt.get_value())

            elif key == "buzzfilter":
                self.set_filter(opt.get_value())

            elif key == "buzzvideo":
                self.set_video_mode(opt.get_value())

            elif key == "buzzaudio":
                self.set_audio_mode(opt.get_value())

            elif key == "buzzedtierpattern":
                self.set_buzzedtier_pattern(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------
    # Getters and Setters
    # -----------------------------------------------------------------------

    def set_tiername(self, value):
        """Set the name of the tier with the intervals to be anonymized.

        :param value: (str) Tier name, not case-sensitive

        """
        value = str(value)
        self._options["buzztier"] = value

    # -----------------------------------------------------------------------

    def set_buzz(self, value):
        """Set the tag representing the intervals to be anonymized.

        :param value: (str) String to find in intervals to be anonymized

        """
        value = str(value)
        self._options["buzzname"] = value

    # -----------------------------------------------------------------------

    def set_filter(self, name):
        """Relation to be applied on the tag to select buzz intervals.

        :param name: (str) One of: equals, contains, startswith, endswith...
        :raise: KeyError

        """
        name = str(name)
        if name not in sppasAnonym.FILTERS:
            raise sppasKeyError("FilterName", name)
        self._options["buzzfilter"] = name

    # -----------------------------------------------------------------------

    def set_buzzedtier_pattern(self, pattern: str = "-buzz"):
        """Pattern to append to the output tier name.

        :param pattern: (str) Pattern (default: -buzz)

        """
        pattern = str(pattern)
        if len(pattern) == 0:
            msg = "Pattern string cannot be empty."
            if self.logfile is not None:
                self.logfile.print_message(msg, indent=2, status=annots.warning)
            else:
                logging.warning(msg)
        else:
            self._options["buzzedtierpattern"] = pattern

    # -----------------------------------------------------------------------

    def set_video_mode(self, mode: str):
        """Mode to anonymize the video: the whole face, the mouth or nothing.

        :param mode: (str) One of: face, mouth or none
        :raises: sppasKeyError: invalid mode

        """
        mode = str(mode)
        mode = mode.lower()
        if mode not in sppasVideoAnonymizer.VIDEO_MODE:
            raise sppasKeyError("VideoMode", mode)
        self._options["buzzvideo"] = mode

    # -----------------------------------------------------------------------

    def set_audio_mode(self, value: bool):
        """To anonymize the audio.

        :param value: (bool) True of anonymize the audio

        """
        self._options["buzzaudio"] = bool(value)

    # -----------------------------------------------------------------------
    # Workers
    # -----------------------------------------------------------------------

    def filter_intervals(self, tier: sppasTier):
        """Return a tier with only the intervals matching the buzz pattern.

        :param tier: (sppasTier) A tier labelled with string tags.
        :return: (sppasTier)

        """
        if tier.is_string() is False:
            logging.error("Only tiers labelled with strings can be filtered to be buzzed.")
            raise BadInputError

        # Create a filter object
        f = sppasTierFilters(tier)

        # Apply a filter to extract intervals with the given pattern and the given function
        argument = self._options["buzzfilter"]
        value = self._options["buzzname"]
        # explanation: func(**{"argument": "value"}) is equivalent to func(argument=value)
        buzz_set = f.tag(**{argument: value})

        # Convert the buzz set of annotations into a tier
        return buzz_set.to_tier(name="Buzzed")

    # -----------------------------------------------------------------------

    def convert_tier(self, tier, buzz_tier):
        """Return the given tier anonylized at the given intervals.

        :param tier: (sppasTier) A tier to be anonymized
        :param buzz_tier: (sppasTier) A tier with buzz intervals
        :return: (sppasTier)

        """

        # Anonymization of the given tier
        anonym_tier = tier.copy()
        anonym_tier.set_name(tier.get_name() + self._options["buzzedtierpattern"])
        for ann_buzz in buzz_tier:
            # Get the annotation in the given tier
            anns = anonym_tier.find(ann_buzz.get_lowest_localization(),
                                    ann_buzz.get_highest_localization(),
                                    overlaps=True)
            for ann in anns:
                ann.set_labels(sppasLabel(sppasTag("buzz")))
        return anonym_tier

    # -----------------------------------------------------------------------

    def convert_audio(self, tier, audio_filename, output=None):
        """Create an anonymized audio stream.

        :param tier: (sppasTier) A tier with the intervals to be anonymized
        :param audio_filename: (str) An audio filename
        :param output: (str or None) Output filename
        :return: (str or AudioPCM) An audio file or an audio stream

        """
        # Fix the list of time segments to be anonymized.
        segments = list()
        for ann in tier:
            b = ann.get_lowest_localization()
            e = ann.get_highest_localization()
            rb = b.get_radius() if b.get_radius() is not None else 0.
            re = e.get_radius() if e.get_radius() is not None else 0.
            segments.append((b.get_midpoint() - rb, e.get_midpoint() + re))
        if len(segments) == 0:
            return None

        # Open the input audio stream and create the output one
        audio_in = audioopy.aio.open(audio_filename)
        audio_out = AudioPCM()

        # Extract each channel, anonymize segments and add to output
        for channel_idx in range(audio_in.get_nchannels()):
            idx = audio_in.extract_channel(channel_idx)
            channel_in = audio_in.get_channel(idx)
            worker = ChannelAnonymizer(channel_in)
            audio_out.append_channel(worker.ianonymize(segments))
        audio_in.close()

        # Save the converted channels
        if output is not None:
            audioopy.aio.save(output, audio_out)
            return output

        return audio_out

    # -----------------------------------------------------------------------

    def convert_video(self, tier, video_file, output=None):
        """Create an anonymized video stream.

        :param tier: (sppasTier) A tier with the intervals to be anonymized
        :param video_file: (str) An audio filename
        :param output: (str or None) Output filename
        :return: (str or sppasVideo) A video file or a video stream

        """
        if output is None:
            return None

        # Fix the list of time segments to be anonymized.
        segments = list()
        for ann in tier:
            b = ann.get_lowest_localization()
            e = ann.get_highest_localization()
            rb = b.get_radius() if b.get_radius() is not None else 0.
            re = e.get_radius() if e.get_radius() is not None else 0.
            segments.append((b.get_midpoint() - rb, e.get_midpoint() + re))
        if len(segments) == 0:
            return None

        vidconverter = sppasVideoAnonymizer(video_file, self._fd)
        vidconverter.set_mode(self._options["buzzvideo"])
        vidconverter.ianonymize(segments, output)

        return output

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the media filenames.

        :param input_files: (list)
        :raise: NoInputError
        :return: (str) Name of the media file

        """
        ext = self.get_input_extensions()
        trs_ext = [e.lower() for e in ext[0]]
        audio_ext = [e.lower() for e in ext[2]]
        video_ext = [e.lower() for e in ext[1]]
        audio = None
        annot = None
        video = None

        for filename in input_files:
            fn, fe = os.path.splitext(filename)
            if annot is None and fe.lower() in trs_ext and fn.endswith(self._options["inputpattern"]):
                annot = filename
            elif audio is None and fe.lower() in audio_ext and fn.endswith(self._options["inputpattern3"]):
                audio = filename
            elif video is None and fe.lower() in video_ext and fn.endswith(self._options["inputpattern2"]):
                video = filename

        if annot is None:
            logging.error("The annotated file with intervals to be anonymized was not found.")
            raise NoInputError

        return annot, audio, video

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on a single input.

        :param input_files: (list of str) Video or image file
        :param output: (str) the output name
        :returns: (list) List of created filenames or list of instances

        """
        result = list()
        trs_file, audio_file, video_file = self.get_inputs(input_files)

        # Get the tier from which intervals will be extracted
        parser = sppasTrsRW(trs_file)
        trs_input = parser.read()
        tier = trs_input.find(self._options["buzztier"])
        if tier is None:
            logging.error("A tier with name {:s} was not found.".format(self._options["buzztier"]))
            raise NoTierInputError

        # Create a tier with only the intervals matching the defined buzz tag
        trs = sppasTranscription("Anonymization")
        buzzed_tier = self.filter_intervals(tier)
        # Anonymize all tiers of the given transcription
        for tier in trs_input:
            anonymized_tier = self.convert_tier(tier, buzzed_tier)
            trs.append(anonymized_tier)
        # Save into an annotated file
        if output is not None:
            output_file = self.fix_out_file_ext(output, out_format="ANNOT")
            parser = sppasTrsRW(output_file)
            parser.write(trs)
            result.append(output_file)
        else:
            result.append(trs)

        # Anonymize the video file
        av = None
        if video_file is not None and self._options["buzzvideo"] is not None and self._fd is not None:
            output_file = None
            if output is not None:
                output_file = self.fix_out_file_ext(output, out_format="VIDEO")
            av = self.convert_video(buzzed_tier, video_file, output_file)
        result.append(av)

        # Anonymize the audio file
        aa = None
        if audio_file is not None and self._options["buzzaudio"] is True:
            output_file = None
            if output is not None:
                output_file = self.fix_out_file_ext(output, out_format="AUDIO")
            aa = self.convert_audio(buzzed_tier, audio_file, output_file)
        result.append(aa)

        return result

    # -----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern",  "-anonym")

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filenames.

        """
        in_ext_annot = list(sppasFiles.get_informat_extensions("ANNOT_ANNOT"))
        in_ext_audio = list(sppasFiles.get_informat_extensions("AUDIO"))
        in_ext_video = list(sppasFiles.get_informat_extensions("VIDEO"))

        return [in_ext_annot, in_ext_video, in_ext_audio]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_filetypes() -> list:
        """Types of file the annotation expects for its inputs, one list per input.

        The types are those of sppasFiles, and the inputs are in the order of
        get_input_extensions().

        :return: (list of list of str)

        """
        return [["ANNOT_ANNOT"], ["VIDEO"], ["AUDIO"]]
