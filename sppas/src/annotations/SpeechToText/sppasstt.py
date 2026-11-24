# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.SpeechToText.sppastt.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS integration of SpeechToText automatic annotation

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
import logging
import shutil
import os
import audioopy.aio
from audioopy import ChannelFrames
from audioopy import AudioPCM
from audioopy import Channel

from sppas.core.config import annots
from sppas.src.utils import sppasFileUtils
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag

from ..baseannot import sppasBaseAnnotation
from ..searchtier import sppasFindTier
from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoTierInputError
from ..annotationsexc import EmptyInputError
from ..annotationsexc import EmptyOutputError
from ..autils import sppasFiles

from .whisperstt import WhisperSTT

# ----------------------------------------------------------------------------


MSG_WHISPER_FAILED = "Whisper failed to be loaded: {error}"

# ----------------------------------------------------------------------------


class sppasSpeechToText(sppasBaseAnnotation):
    """SPPAS integration of the automatic SpeechToText annotation.

    """

    def __init__(self, log=None):
        """Create a new sppasSpeechToText instance.

        Log is used for a better communication of the annotation process and its
        results. If None, logs are redirected to the default logging system.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasSpeechToText, self).__init__("speechtotext.json", log)
        self.__stt = None

    # -----------------------------------------------------------------------

    def load_resources(self, model=None, lang="und", **kwargs):
        """Fix the stt resources from a configuration file.

        :param model: Ignored
        :param lang: (str) Iso639-3 of the language or "und" if unknown.

        """
        # Either the language is forced by the 'lang' argument, or the 'lang' option is used.
        if lang == "und" or lang is None:
            lang = self._options["lang"]
        if lang == "und":
            lang = None

        try:
            self.__stt = WhisperSTT(model=self._options["modelname"], language=lang)
        except Exception as e:
            self.__stt = None
            if self.logfile is None:
                logging.error(MSG_WHISPER_FAILED.format(error=e))
            self.logfile.print_message(MSG_WHISPER_FAILED.format(error=e),
                                       indent=2, status=annots.warning)
            raise

        logging.info(f"The STT system {self.__stt.name} is "
                     f"enabled={self.__stt.enabled} for lang={lang}.")

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        Available options are:

            - modelname

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()

            if "modelname" == key:
                self.set_model_name(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            elif key == "lang":
                self._options[key] = opt.get_value()

            elif key == "prompt":
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def set_model_name(self, model_name: str = "base"):
        """Fix the name of the model for Whisper.

        :param model_name: (str)

        """
        self._options['modelname'] = model_name

    # -----------------------------------------------------------------------

    def set_prompt(self, prompt: str | None = None):
        """Fix an initial prompt for Whisper.

        :param prompt: (str)

        """
        self.__stt.set_prompt(prompt)
        self._options['prompt'] = prompt

    # -----------------------------------------------------------------------
    # Automatic Speech To Text
    # -----------------------------------------------------------------------

    def convert(self, channel, tier):
        """Speech-To-Text of all Inter-Pausal Units of a tier.

        :param channel: (Channel) Input audio channel
        :param tier: (sppasTier) The IPUs to transcribe.
        :return: (sppasTier) automatic approx. transcription
        :raises: ValueError: Speech-To-Text is not enabled
        :raises: IOError: missing input tier
        :raises: EmptyInputError: The input tier has no IPUs

        """
        if self.__stt is None:
            raise ValueError("Speech-To-Text system was not properly initialized.")
        if self.__stt.enabled is False:
            raise ValueError("Speech-To-Text system is not enabled.")

        if tier is None:
            raise IOError('No tier found.')
        if tier.is_empty() is True:
            raise EmptyInputError(name=tier.get_name())
        framerate = channel.get_framerate()
        sampwidth = channel.get_sampwidth()
        tier_stt = sppasTier("SpeechToText")

        # Create a working directory
        working_dir = sppasFileUtils().set_random()
        os.mkdir(working_dir)

        # Browse through the IPUs in order to create its approx. ortho transcription
        for i, ann in enumerate(tier):

            # is an IPU?
            if ann.get_best_tag().is_silence():
                tier_stt.append(ann.copy())
                continue

            logging.info(f" ... {self.__stt.name} transcribes IPU {i+1}")

            # Get localization information
            begin = ann.get_lowest_localization().get_midpoint()
            begin = max(0, begin - 0.1)
            end = ann.get_highest_localization().get_midpoint()

            # Create audio output of the IPU
            # - create a fragment channel from the channel
            fn_i = os.path.join(working_dir, "ipu_{:04d}.wav".format(i+1))
            extracter = channel.extract_fragment(int(begin*framerate), int(end*framerate))
            # - convert to 16bits-16kHz if needed
            if framerate != 16000 or sampwidth != 2:
                c = ChannelFrames(extracter.get_frames())
                c.change_sampwidth(sampwidth, 2)
                c.resample(sampwidth, framerate, 16000)
                extracter = Channel(framerate=16000, sampwidth=2, frames=c.get_frames())
            # - save the (converted) fragment
            audio_out = AudioPCM()
            audio_out.append_channel(extracter)
            audioopy.aio.save(fn_i, audio_out)

            # Launch STT on the given IPU audio file
            # =======================================
            tags = list()
            txt = self.__stt.transcribe(fn_i)
            tags.append(sppasTag(txt))
            tier_stt.create_annotation(ann.get_location().copy(), sppasLabel(tags))

        # Make some cleaning: delete the working dir
        shutil.rmtree(working_dir)

        return tier_stt

    # ------------------------------------------------------------------------
    # Apply the annotation on one given file
    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the audio filename and the tier with IPUs.

        :param input_files: (list)
        :raises: NoTierInputError
        :return: (filename, sppasTier)

        """
        # Get the tier and the channel
        ext = self.get_input_extensions()
        audio_ext = [e.lower() for e in ext[0]]
        tier_ipus = None
        audio_filename = None

        for filename in input_files:
            if filename is None:
                continue
            fn, fe = os.path.splitext(filename)
            if audio_filename is None and fe.lower() in audio_ext:
                audio_filename = filename
            if fe in ext[1] and tier_ipus is None:
                parser = sppasTrsRW(filename)
                trs_input = parser.read()
                tier = sppasFindTier.ipus(trs_input)
                if tier is not None:
                    if self.logfile:
                        self.logfile.print_message("Input tier to be transcribed: "
                                                   "{}".format(tier.get_name()), indent=1)
                    tier_ipus = tier

        # Check input tier
        if tier_ipus is None:
            logging.error("No tier with IPUs was found.")
            raise NoTierInputError
        if audio_filename is None:
            logging.error("No audio file was found.")
            raise IOError("No audio file was found.")

        return audio_filename, tier_ipus

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        :param input_files: (list of str) includes IPUs
        :param output: (str) the output file name
        :returns: (sppasTranscription)

        """
        # Get input tier to transcribe
        audio_filename, tier_input = self.get_inputs(input_files)

        # Get audio and the channel we'll work on
        audio_speech = audioopy.aio.open(audio_filename)
        n = audio_speech.get_nchannels()
        if n != 1:
            raise IOError("An audio file with only one channel is expected. "
                          "Got {:d} channels.".format(n))

        # Extract the channel
        idx = audio_speech.extract_channel(0)
        channel = audio_speech.get_channel(idx)

        # Transcribe the tier
        tier_ortho = self.convert(channel, tier_input)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.append(tier_ortho)

        trs_output.set_meta('speechtotext_result_of', input_files[0])
        trs_output.set_meta('language_iso', "iso639-3")
        trs_output.set_meta('language_name_0', "Undetermined")
        if self.__stt.language is not None:
            trs_output.set_meta('language_code_0', self.__stt.language)
            trs_output.set_meta('language_url_0', "https://iso639-3.sil.org/code/"+self.__stt.language)
        else:
            trs_output.set_meta('language_code_0', "und")
            trs_output.set_meta('language_url_0', "https://iso639-3.sil.org/code/und")

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

    # -----------------------------------------------------------------------

    def get_input_patterns(self):
        """Extensions that the annotation expects for its input filename."""
        return [self._options.get("inputpattern1", ""),       # audio file
                self._options.get("inputpattern2", "-ipus")   # annot with IPUs
                ]

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

    # -----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-stt")

    # -----------------------------------------------------------------------
