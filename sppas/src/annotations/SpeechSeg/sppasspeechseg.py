# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.SpeechSeg.sppasspeechseg.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Full automatic process of speech segmentation.

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

    Copyright (C) 2011-2024  Brigitte Bigi, CNRS
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

Description:
============

Perform full speech segmentation process:

    - all options to configure the annotations;
    - can estimate an intensity coefficient;
    - can optionally predict silent pauses (the ones into the IPUs).

"""

import os
import shutil
import codecs
import json
from audioopy import AudioFrames
import audioopy.aio

from sppas.core.config import separators
from sppas.core.config import symbols
from sppas.core.config import paths
from sppas.core.coreutils import info
from sppas.core.config import annots
from sppas.src.calculus import fmean
from sppas.src.calculus import lstdev
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTrsRW
from sppas.src.annotations import sppasTextNorm
from sppas.src.annotations import sppasPhon
from sppas.src.annotations import sppasAlign
from sppas.src.annotations.RMS.irms import IntervalsRMS

from ..baseannot import sppasBaseAnnotation
from ..annotationsexc import AnnotationOptionError
from ..searchtier import sppasFindTier
from ..annotationsexc import NoTierInputError
from ..annotationsexc import EmptyOutputError
from ..autils import sppasFiles
from .segtojson import FormatTrsSeg

# ---------------------------------------------------------------------------
# Constants

SIL_PHON = list(symbols.phone.keys())[list(symbols.phone.values()).index("silence")]

# ---------------------------------------------------------------------------


class sppasSpeechSeg(sppasBaseAnnotation):
    """Full process of speech segmentation.

    With no intermediate results, the process is fully automatic and there's
    no way to check each step...

    The orthographic transcription is supposed to already be time-aligned at
    the IPUs level. Then, Speech Segmentation is:

        1- Text Normalization
        2- Phonetization
        3- Alignment

    """

    def __init__(self, log=None):
        """Create a new sppasAutoSeg instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasSpeechSeg, self).__init__("SpeechSeg.json", log)
        self.__ann_norm = sppasTextNorm(log)
        self.__ann_norm.set_occ_dur(False)
        self.__ann_phon = sppasPhon(log)
        self.__ann_align = sppasAlign(log)
        self.__lang = "und"
        self.__seg_output = FormatTrsSeg()

    # -----------------------------------------------------------------------

    def load_resources(self, lang, phn_map_table=None):
        """

        :param lang: (str) Language code
        :param phn_map_table: (str) Name of a file with phonemes mapping as 'src dest'

        """
        self.__lang = lang

        vocab = os.path.join(paths.resources, "vocab", lang + ".vocab")
        self.__ann_norm.load_resources(vocab, lang=lang)

        prons = os.path.join(paths.resources, "dict", lang + ".dict")
        self.__ann_phon.load_resources(prons)

        acm = os.path.join(paths.resources, "models", "models-" + lang)
        self.__ann_align.load_resources(acm)

        if phn_map_table is not None:
            self.__seg_output = FormatTrsSeg(map_table=phn_map_table)

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        Available options are:

            - duration

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()

            if "pattern" in key:
                self._options[key] = opt.get_value()

            elif "predictsil" in key:
                self.set_predict_sil(opt.get_value())

            elif "intensity" in key:
                self.set_predict_intensity(opt.get_value())

            elif "json" in key:
                self.set_output_json(opt.get_value())

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def set_predict_sil(self, value=False):
        """Attempt to predict short pauses after each word.

        :param value: (bool) False by default because experimental.

        """
        self._options["predictsp"] = bool(value)

    # -----------------------------------------------------------------------

    def set_predict_intensity(self, value=True):
        """Estimate an intensity value.

        :param value: (bool) True by default.

        """
        self._options["intensity"] = bool(value)

    # -----------------------------------------------------------------------

    def set_output_json(self, value=False):
        """Estimate an intensity value.

        :param value: (bool) False by default.

        """
        self._options["json"] = bool(value)

    # -----------------------------------------------------------------------
    # Automatic annotation
    # -----------------------------------------------------------------------

    def convert(self, audio_file, tier_iputrs):
        """Perform speech segmentation fully automatically.

        Audio is:
            - mono -- an exception is raised if not;
            - 16KHz -- if more, the audio is copied and converted by SPPAS to 16kHz;
            - 16 bits -- 24 works too -- but Python audio library randomly works on 32bits.

        :param audio_file: (str) Audio filename
        :param tier_iputrs: (sppasTier) A tier with the transcribed IPUs
        :return: (sppasTranscription)

        """
        # Normalize the transcription inside the ipus
        tier_faked_tokens, tier_std_tokens, tier_custom = self.__ann_norm.convert(tier_iputrs)

        # Phonetize the normalized text
        tier_phon = self.__ann_phon.convert(tier_faked_tokens)
        if self._options["predictsil"] is True:
            self.__add_phon_sil(tier_phon)

        # Forced-alignment to fix the time-aligned phonemes and tokens
        workdir = sppasAlign.fix_workingdir(audio_file)
        try:
            tier_phna, tier_toka, tier_pron = self.__ann_align.convert(tier_phon, tier_std_tokens, tier_faked_tokens, audio_file, workdir)
            tier_phna.set_media(tier_iputrs.get_media())
            tier_toka.set_media(tier_iputrs.get_media())
        except:
            shutil.rmtree(workdir)
            raise

        audio_speech = audioopy.aio.open(audio_file)
        idx = audio_speech.extract_channel()
        input_channel = audio_speech.get_channel(idx)
        audio_speech.close()

        # Create the output transcription object
        trs = self.__create_trs(input_channel.get_framerate(), audio_file)
        trs.append(tier_iputrs)
        trs.append(tier_phna)
        trs.append(tier_toka)

        # RMS estimator
        if self._options['intensity'] is True:
            tier_rms = self.__rms(tier_phna, input_channel)
            tier_rms.set_media(tier_iputrs.get_media())
            trs.append(tier_rms)

        return trs

    # -----------------------------------------------------------------------

    def __rms(self, tier, input_channel):
        """RMS value of each interval in the given tier.

        """
        rms = IntervalsRMS(input_channel)
        all_values = list()
        tier_rms = sppasTier("Intensity")
        for ann in tier:
            labels = ann.get_labels()
            if labels[0].get_best().is_silence() is True:
                rms_tag = sppasTag(0, "int")
                tier_rms.create_annotation(ann.get_location().copy(), sppasLabel(rms_tag))
                continue

            # Localization of the current annotation
            begin = ann.get_lowest_localization()
            end = ann.get_highest_localization()

            # Estimate all RMS values during this ann
            rms.estimate(begin.get_midpoint(), end.get_midpoint())

            # The global RMS of the fragment between begin and end
            rms_tag = sppasTag(rms.get_rms(), "int")
            tier_rms.create_annotation(ann.get_location().copy(), sppasLabel(rms_tag))
            all_values.append(rms.get_rms())

        avg = fmean(all_values)
        stdev = lstdev(all_values)
        for ann in tier_rms:
            b = ann.get_lowest_localization().get_midpoint()
            e = ann.get_highest_localization().get_midpoint()
            # Score based on the amplitude (absolute)
            # ---------------------------------------
            bf = int(b * float(input_channel.get_framerate()))
            ef = int(e * float(input_channel.get_framerate()))
            fragment = input_channel.extract_fragment(begin=bf, end=ef)
            frames_max = AudioFrames(fragment.get_frames(), input_channel.get_sampwidth()).max()
            channel_max = AudioFrames.get_maxval(input_channel.get_sampwidth())
            score = int(10. * (frames_max / channel_max))

            # Score based on the RMS (relative)
            # ---------------------------------
            labels = ann.get_labels()
            rms = labels[0].get_best().get_typed_content()
            if rms == 0:
                continue
            if rms == max(all_values):
                continue

            if rms < avg-stdev:
                # Lower than usual: between 0 and (avg-stdev). Score is 1, 2 or 3
                third = (avg-stdev) / 3.
                if rms < third:
                    ann.set_labels([sppasLabel(sppasTag(score+1, "int"))])
                elif rms > 2*third:
                    ann.set_labels([sppasLabel(sppasTag(score+2, "int"))])
                else:
                    ann.set_labels([sppasLabel(sppasTag(score+3, "int"))])

            elif rms > avg+stdev:
                # Higher than usual: between (avg+stdev) and max. Score is 7, 8 or 9
                third = ((max(all_values))-(avg+stdev)) / 3.
                if rms < avg + stdev + third:
                    ann.set_labels([sppasLabel(sppasTag(score+7, "int"))])
                elif rms > avg + stdev + (2.*third):
                    ann.set_labels([sppasLabel(sppasTag(score+9, "int"))])
                else:
                    ann.set_labels([sppasLabel(sppasTag(score+8, "int"))])

            else:
                # In the average: score is 4, 5 or 6.
                third = 2. * stdev / 3.
                if rms > avg+third:
                    ann.set_labels([sppasLabel(sppasTag(score+6, "int"))])
                elif rms < avg-third:
                    ann.set_labels([sppasLabel(sppasTag(score+4, "int"))])
                else:
                    ann.set_labels([sppasLabel(sppasTag(score+5, "int"))])

        return tier_rms

    # -----------------------------------------------------------------------

    def __add_phon_sil(self, tier_phon):
        """Add an alternative with a silence at the end of each variant.

        """
        for ann in tier_phon:
            # the current labels of this annotation (a phonetized ipu)
            labels = ann.get_labels()
            # the new list of labels of this phonetized ipu
            new_labels = list()
            # each tag is a pronunciation variant of a token
            for label in labels:
                # to not add an optional silence at the end of an IPU
                is_last_label = True if label is labels[-1] else False
                # all tags: with or without ending by a silence
                all_tags = list()
                # each tag is now 2 different variants
                for tag, score in label:
                    if tag is not None:
                        all_tags.append(tag)
                        if tag.is_silence() is False and is_last_label is False:
                            new_tag = tag.copy()
                            content = new_tag.get_content()
                            content = content + separators.phonemes + SIL_PHON
                            new_tag.set_content(content)
                            all_tags.append(new_tag)

                new_labels.append(sppasLabel(all_tags))
            ann.set_labels(new_labels)

    # -----------------------------------------------------------------------

    def __create_trs(self, framerate, filename):
        """Create a sppasTranscription and return it."""
        trs_output = sppasTranscription("SpeechSeg")
        trs_output.set_meta('annotation_result_of', filename)
        trs_output.set_meta("media_sample_rate", str(framerate))
        trs_output.set_meta('language_iso', "iso639-3")
        trs_output.set_meta('language_code_0', self.__lang)
        trs_output.set_meta('language_name_0', "Undetermined")
        trs_output.set_meta('language_url_0', "https://iso639-3.sil.org/code/"+self.__lang)
        return trs_output

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the audio filename and the tier with transcription.

        :param input_files: (list)
        :raise: NoTierInputError
        :return: (str, sppasTier)

        """
        # Get the tier and the channel
        ext = self.get_input_extensions()[0]
        audio_ext = ext[0]
        audio_filename = None
        tier = None
        annot_ext = self.get_input_extensions()[1]

        for filename in input_files:
            fn, fe = os.path.splitext(filename)
            if audio_filename is None and fe in audio_ext:
                audio_filename = filename
            if tier is None and fe in annot_ext[0]:
                parser = sppasTrsRW(filename)
                trs_input = parser.read()
                tier = sppasFindTier.transcription(trs_input)

        if tier is None:
            raise NoTierInputError
        if audio_filename is None:
            raise FileNotFoundError

        return audio_filename, tier

    # -----------------------------------------------------------------------

    def save_trs(self, trs, output_file=None):
        """Write the transcription into the given output.

        :param trs: (sppasTranscription)
        :param output_file: (str or None) Output file name
        :returns: (sppasTranscription or dict or list with a filename)

        """
        self.__seg_output.trs_phn_to_map(trs)

        # Normalize the output if the option is enabled
        if self._options['json'] is True:
            # Fill in a data structure from the objects
            self.__seg_output.trs_to_data_norm(trs)
            if output_file is not None:
                # Write the resulting dictionary into a JSON file
                with codecs.open(output_file, 'w', "UTF-8") as f:
                    json.dump(self.__seg_output.data, f, indent=4, separators=(',', ': '))
                return [output_file]
            else:
                return self.__seg_output.data
        else:
            if output_file is not None:
                # Write result into an annotated file with the given extension (default: xra)
                parser = sppasTrsRW(output_file)
                parser.write(trs)
                return [output_file]

        return trs

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        :param input_files: (list of str) Time-aligned tokens
        :param output: (str) the output name - either filename or basename
        :returns: (sppasTranscription or saved filename or dict)

        """
        # Get the phonemes tier to be time-aligned
        audio_filename, ortho_tier = self.get_inputs(input_files)

        # Perform speech segmentation
        trs_output = self.convert(audio_filename, ortho_tier)

        # Save in a file
        if len(trs_output) > 0:
            if self._options['json'] is True:
                output_file = self.fix_out_file_json_ext(output)
            else:
                output_file = self.fix_out_file_ext(output)
            return self.save_trs(trs_output, output_file)
        else:
            raise EmptyOutputError

    # -----------------------------------------------------------------------

    def fix_out_file_json_ext(self, output):
        """Return the output with an appropriate JSON file extension.

        If the output has already an extension, it is changed.

        :param output: (str) Base name or filename
        :return: (str) filename

        """
        _, fe = os.path.splitext(output)
        if len(fe) == 0:
            # No extension in the output.
            output = output + ".json"
        else:
            output = output.replace(fe, ".json")

        # If output exists, it is overridden
        if os.path.exists(output) and self.logfile is not None:
            self.logfile.print_message(
                (info(1300, "annotations")).format(output),
                indent=2, status=annots.warning)

        return output

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
