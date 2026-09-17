"""
:filename: sppas.src.annotations.Align.tracksio.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Automatic segmentation of the data into tracks

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

import os
import codecs
import logging
import traceback
import audioopy.audioutils as audioutils
import audioopy.aio

from sppas.core.config import sg
from sppas.core.config import separators
from sppas.core.coreutils import NoDirectoryError
from sppas.core.coreutils import sppasUnicode
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasAnnotation
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasPoint
from sppas.src.anndata.aio.aioutils import serialize_labels
from sppas.src.resources.mapping import sppasMapping
from sppas.src.anndata import sppasTag, sppasLabel

from ..annotationsexc import BadInputError
from ..annotationsexc import SizeInputsError
from ..annotationsexc import AudioChannelError

from .aligners.alignerio import AlignerIO

# ------------------------------------------------------------------


class TracksReaderWriter(object):
    """Manager for tracks from/to tiers.

    """

    DELIMITERS = (" ", separators.variants, separators.phonemes)

    # ------------------------------------------------------------------------

    def __init__(self, mapping, radius=None):
        """Create a new TracksReaderWriter instance.

        :param mapping: (Mapping) a mapping table to convert the phone set

        """
        self.__reader = TracksReader(radius)
        # Phonetizations of the alternative tags of the tokens of each track
        self.__alternatives = dict()
        # Mapping system for the phonemes
        if mapping is None:
            mapping = sppasMapping()
        if isinstance(mapping, sppasMapping) is False:
            raise TypeError('Expected a sppasMapping() as argument.'
                            'Got {:s} instead.'.format(type(mapping)))
        self._mapping = mapping

    # ------------------------------------------------------------------------

    def set_radius(self, radius):
        """Set the radius of the reader."""
        self.__reader = TracksReader(radius)

    # ------------------------------------------------------------------------

    def get_units(self, dir_name):
        """Return the time units of all tracks.

        :param dir_name: (str) Input directory to get files.

        """
        return ListOfTracks.read(dir_name)

    # ------------------------------------------------------------------------
    # Alternatives of the tokens
    # ------------------------------------------------------------------------

    @staticmethod
    def get_alternatives(annotation):
        """Return the phonetizations of the alternative tags of the tokens.

        The phonetization of each alternative tag of a token is lost in the
        tags of a label, so the Phonetization is storing them into the
        metadata of its annotations, addressed by the key of a label and the
        rank of a tag. An empty list is returned for a token without any
        alternative, or if the annotation has no such metadata.

        :param annotation: (sppasAnnotation) An annotation of a phonetization
        :return: (list) For each label, the phonetizations of each of its tags

        """
        alternatives = list()
        for label in annotation.get_labels():
            key = label.get_key()
            tag_phonetizations = list()
            if key is not None:
                rank = 1
                phonetizations = annotation.get_meta("phon-" + key + "-" + str(rank), None)
                while phonetizations is not None:
                    tag_phonetizations.append(phonetizations.split(separators.variants))
                    rank += 1
                    phonetizations = annotation.get_meta("phon-" + key + "-" + str(rank), None)

            alternatives.append(tag_phonetizations)

        return alternatives

    # ------------------------------------------------------------------------

    def _score_alternatives(self, dir_name, tier_tok, tier_pron):
        """Score the alternative tags of the tokens with the aligned pronunciation.

        The tag of a token is scored with the score of the pronunciation the
        aligner selected if one of its phonetizations is this pronunciation,
        and with 0. if not. The tags of homophones are then sharing the same
        score, so no word is selected among them.

        Nothing is done if the phonetizations of the alternatives are missing
        or if they are not matching the aligned tokens, which happens when the
        tokenization was rescued or re-created.

        :param dir_name: (str) Input directory with the aligned tracks
        :param tier_tok: (sppasTier) The time-aligned tokens
        :param tier_pron: (sppasTier) The time-aligned pronunciations

        """
        if len(self.__alternatives) == 0:
            return

        for track_number, unit in enumerate(ListOfTracks.read(dir_name), 1):
            alternatives = self.__alternatives.get(track_number, list())
            if len(alternatives) == 0:
                continue

            begin = sppasPoint(unit[0])
            end = sppasPoint(unit[1])
            tok_anns = tier_tok.find(begin, end, overlaps=False)
            pron_anns = tier_pron.find(begin, end, overlaps=False)
            if len(tok_anns) != len(alternatives) or len(pron_anns) != len(tok_anns):
                logging.warning(
                    "The phonetizations of the alternatives of the track {:d} are "
                    "ignored: {:d} tokens were aligned but {:d} were phonetized."
                    "".format(track_number, len(tok_anns), len(alternatives)))
                continue

            for tok_ann, pron_ann, tag_phonetizations in zip(tok_anns, pron_anns, alternatives):
                if len(tag_phonetizations) > 1:
                    TracksReaderWriter._score_token(tok_ann, pron_ann, tag_phonetizations)

    # ------------------------------------------------------------------------

    @staticmethod
    def _score_token(tok_ann, pron_ann, tag_phonetizations):
        """Score the tags of a time-aligned token with its aligned pronunciation.

        :param tok_ann: (sppasAnnotation) One time-aligned token
        :param pron_ann: (sppasAnnotation) The pronunciation of this token
        :param tag_phonetizations: (list) The phonetizations of each of its tags

        """
        label = tok_ann.get_labels()[0]
        tags = [tag for tag, score in label]
        if len(tags) != len(tag_phonetizations):
            logging.warning(
                "The token '{:s}' has {:d} tags but {:d} of them were phonetized. "
                "Its tags are not scored.".format(
                    serialize_labels(tok_ann.get_labels()), len(tags), len(tag_phonetizations)))
            return

        pron_label = pron_ann.get_labels()[0]
        pron_tag = pron_label.get_best()
        pronunciation = pron_tag.get_content()

        matching = list()
        for rank, phonetizations in enumerate(tag_phonetizations):
            if pronunciation in phonetizations:
                matching.append(rank)

        # The guard: an aligned pronunciation of none of the alternatives means
        # that the phonetizations can't be trusted - a defective mapping table
        # of the phone set, for example. The label is then left as it is.
        if len(matching) == 0:
            logging.warning(
                "The aligned pronunciation '{:s}' of the token '{:s}' is none of "
                "its phonetizations. Its tags are not scored.".format(
                    pronunciation, serialize_labels(tok_ann.get_labels())))
            return

        # All the alternatives are kept and their scores are the probability
        # of each of them to be the aligned word. A word the transcriber
        # judged possible is never impossible, so none of them is scored 0.
        confidence = pron_label.get_score(pron_tag)
        if confidence is None or confidence <= 0. or confidence > 1.:
            # Without the confidence of the aligner, nothing can be departed
            scores = [1. / float(len(tags))] * len(tags)
        else:
            # The pronunciations of a word being equiprobable between them, a
            # word with 'k' of them is giving only one chance out of 'k' to
            # the selected one: the words matching it are weighted by 1/k.
            # The dilution of the confidence by the number of variants is the
            # same for all the words of the track, so it does not bias this
            # weighting.
            weights = list()
            for rank in matching:
                weights.append(1. / float(len(tag_phonetizations[rank])))
            total_weight = sum(weights)

            # The confidence of an aligner in the pronunciation it selected is
            # diluted by the number of candidate pronunciations: 0.82 in
            # average with one of them, 0.42 with five ones. So "1 -
            # confidence" is mixing two errors: to have selected the wrong
            # word, and the wrong variant of the right word. Only the first
            # one is an error on the word, hence the division by the number of
            # candidate pronunciations of the matching words.
            candidates = list()
            for rank in matching:
                for phonetization in tag_phonetizations[rank]:
                    if phonetization not in candidates:
                        candidates.append(phonetization)

            error_mass = (1. - confidence) / float(len(candidates))
            if len(matching) == len(tags):
                # There's no other word the error could be attributed to
                error_mass = 0.
            matching_mass = 1. - error_mass

            scores = list()
            for rank in range(len(tags)):
                if rank in matching:
                    weight = 1. / float(len(tag_phonetizations[rank]))
                    scores.append(matching_mass * weight / total_weight)
                else:
                    scores.append(error_mass / float(len(tags) - len(matching)))

        aligned_label = sppasLabel(tags, scores)
        aligned_label.set_key(label.get_key())
        tok_ann.set_labels([aligned_label])

    # ------------------------------------------------------------------------
    # Read files
    # ------------------------------------------------------------------------

    def read_aligned_tracks(self, dir_name):
        """Read time-aligned tracks in a directory.

        :param dir_name: (str) Input directory to get files.
        :returns: (sppasTier, sppasTier, sppasTier)

        """
        tier_phn, tier_tok, tier_pron = self.__reader.read_aligned_tracks(dir_name)

        # map-back phonemes
        self._mapping.set_keep_miss(True)
        self._mapping.set_reverse(False)

        # Map-back time-aligned phonemes to SAMPA
        # include the mapping of alternative tags
        for ann in tier_phn:
            labels = list()
            for label in ann.get_labels():
                tags = list()
                scores = list()
                for tag, score in label:
                    text = tag.get_content()
                    tags.append(sppasTag(self._mapping.map_entry(text)))
                    scores.append(score)
                labels.append(sppasLabel(tags, scores))
            ann.set_labels(labels)

        for ann in tier_pron:
            labels = list()
            for label in ann.get_labels():
                tags = list()
                scores = list()
                for tag, score in label:
                    text = tag.get_content()
                    tags.append(sppasTag(self._mapping.map(text, [separators.phonemes])))
                    scores.append(score)
                labels.append(sppasLabel(tags, scores))
            ann.set_labels(labels)

        # The pronunciations are back to the phone set of the phonetization,
        # so the alternatives of the tokens can be scored with them.
        self._score_alternatives(dir_name, tier_tok, tier_pron)

        return tier_phn, tier_tok, tier_pron

    # ------------------------------------------------------------------------
    # Write files
    # ------------------------------------------------------------------------

    def split_into_tracks(self, input_audio, phon_tier, tok_tier, tok_rescue_tier, dir_align):
        """Write tracks from the given data.

        :param input_audio: (str|None) Audio file name. Or None if no needed (basic alignment).
        :param phon_tier: (sppasTier) The phonetization tier.
        :param tok_tier: (sppasTier) The tokens tier, or None.
        :param tok_rescue_tier: (sppasTier) The tokens rescue tier, or None.
        :param dir_align: (str) Output directory to store files.

        :return: PhonAlign, TokensAlign

        """
        errmsg = ""
        # Map phonemes from SAMPA to the expected ones.
        self._mapping.set_keep_miss(True)
        self._mapping.set_reverse(True)

        # Map phonetizations (even the alternatives)
        self.__alternatives = dict()
        for track_index, ann in enumerate(phon_tier):
            # The phonetizations of the alternatives are collected before the
            # labels of the annotation are replaced by the mapped ones.
            self.__alternatives[track_index + 1] = \
                TracksReaderWriter.get_alternatives(ann)

            text = TracksWriter.serialize_labels_for_aligner(ann.get_labels(), separator="\n")
            tab = text.split('\n')
            content = list()
            for item in tab:
                item = item.replace('|', separators.variants)
                if item.startswith('{') and item.endswith('}'):
                    content.append(item[1:-1])
                else:
                    content.append(item)

            mapped = self._mapping.map(" ".join(content), TracksReaderWriter.DELIMITERS)
            ann.set_labels(sppasLabel(sppasTag(mapped)))

        try:
            msg = TracksWriter.write_tracks(input_audio, phon_tier, tok_tier, tok_rescue_tier, dir_align)
            errmsg += msg
        except SizeInputsError as e:
            errmsg += str(e)
            # number of intervals are not matching. Try to create a matching tokenization.
            rescue = self.__recreate_rescue_tier(
                phon_tier,
                tok_rescue_tier if tok_rescue_tier is not None else tok_tier
            )
            # rescue is either None (the tokenization was not rescued)
            # or a valid tier in terms of number of intervals
            try:
                msg = TracksWriter.write_tracks(input_audio, phon_tier, rescue, None, dir_align)
                errmsg += msg
            except Exception as e:
                errmsg += str(e)
        except BadInputError as e:
            errmsg += str(e)
            # either phonemes or tokens is wrong... re-try with phonemes only
            try:
                msg = TracksWriter.write_tracks(input_audio, phon_tier, None, None, dir_align)
            except Exception as e:
                msg = str(e)
            errmsg += msg

        return errmsg

    # ------------------------------------------------------------------------

    def __recreate_rescue_tier(self, phon_tier, tok_rescue_tier):
        if tok_rescue_tier is None:
            return None
        rescue = sppasTier("TokensRescued")
        for ann in phon_tier:
            begin = ann.get_lowest_localization()
            end = ann.get_highest_localization()
            tokanns = tok_rescue_tier.find(begin, end, overlaps=False)
            if len(tokanns) == 0:
                logging.error("No tokens are matching the interval: {:.3f}-{:.3f}"
                              "".format(begin.get_midpoint(), end.get_midpoint()))
                tokanns.append(sppasAnnotation(
                    sppasLocation(sppasInterval(begin.copy(), end.copy()))))
            rescue.append(tokanns[0].copy())
        return rescue

    # ------------------------------------------------------------------------

    @staticmethod
    def get_filenames(track_dir, track_number):
        """Return file names corresponding to a given track.

        :param track_dir: (str)
        :param track_number: (int)
        :returns: (audio, phn, tok, align) file names

        """
        audio = TrackNamesGenerator.audio_filename(track_dir, track_number)
        phn = TrackNamesGenerator.phones_filename(track_dir, track_number)
        tok = TrackNamesGenerator.tokens_filename(track_dir, track_number)
        align = TrackNamesGenerator.align_filename(track_dir, track_number)
        return audio, phn, tok, align

# ----------------------------------------------------------------------------


class TrackNamesGenerator:
    """Manage names of the files for a given track number.

    """

    @staticmethod
    def audio_filename(track_dir, track_number):
        """Return the name of the audio file."""
        return os.path.join(track_dir, "track_{:06d}.wav".format(track_number))

    @staticmethod
    def phones_filename(track_dir, track_number):
        """Return the name of the file with Phonetization."""
        return os.path.join(track_dir, "track_{:06d}.phn".format(track_number))

    @staticmethod
    def tokens_filename(track_dir, track_number):
        """Return the name of the file with Tokenization."""
        return os.path.join(track_dir, "track_{:06d}.tok".format(track_number))

    @staticmethod
    def align_filename(track_dir, track_number, ext=None):
        """Return the name of the time-aligned file, without extension."""
        if ext is None:
            return os.path.join(track_dir, "track_{:06d}".format(track_number))
        return os.path.join(track_dir, "track_{:06d}.{:s}".format(track_number, ext))

# ----------------------------------------------------------------------------


class TracksReader(object):
    """Read time-aligned tracks.

    Manage tracks for the time-aligned phonemes and tokens.

    """

    RADIUS = 0.005  # Half-size of a frame in the acoustic model

    # ------------------------------------------------------------------------

    def __init__(self, radius=None):
        """Create an instance."""
        self.__radius = TracksReader.RADIUS
        if radius is not None:
            r = float(radius)
            if 0. <= r <= 0.2:
                self.__radius = r

    # ------------------------------------------------------------------------

    def read_aligned_tracks(self, dir_name):
        """Read a set of alignment files and set as tiers.

        :param dir_name: (str) input directory containing a set of units
        :returns: PhonAlign, TokensAlign

        """
        # Read the time values of each track from a file
        units = ListOfTracks.read(dir_name)

        # Check if the directory exists
        if os.path.exists(dir_name) is False:
            raise NoDirectoryError(dirname=dir_name)

        # Create new tiers
        tier_phn = sppasTier("PhonAlign")
        tier_tok = sppasTier("TokensAlign")
        tier_pron = sppasTier("PronTokAlign")

        # Explore each unit to get alignments
        track_number = 1
        for unit_start, unit_end in units:

            # Fix filename to read, and load the content
            basename = TrackNamesGenerator.align_filename(dir_name, track_number)
            try:
                _phons, _words, _prons = AlignerIO.read_aligned(basename)
            except IOError:
                _phons, _words, _prons = [], [], []

            # Append alignments in tiers
            self._add_aligned_track_into_tier(tier_phn, _phons, unit_start, unit_end)
            self._add_aligned_track_into_tier(tier_tok, _words, unit_start, unit_end)
            self._add_aligned_track_into_tier(tier_pron, _prons, unit_start, unit_end)

            track_number += 1

        return tier_phn, tier_tok, tier_pron

    # ------------------------------------------------------------------------

    def _add_aligned_track_into_tier(self, tier, tdata, delta, unitend):
        """Append a list of (start, end, text, score) into the tier.

        Shift start/end of a delta value and set the last end value.

        """
        try:
            for i, t in enumerate(tdata):
                # fix the location - an interval
                (loc_s, loc_e, contents, scores) = t
                loc_s += delta
                loc_e += delta
                if i == (len(tdata)-1):
                    loc_e = unitend
                location = sppasLocation(sppasInterval(sppasPoint(loc_s, self.__radius), sppasPoint(loc_e, self.__radius)))

                # fix the label
                # allow to work with alternative tags. The aligners are
                # returning the alternatives as they were given to them, so
                # with the "{|}" system of the tracks.
                if contents.startswith('{') is True and contents.endswith('}') is True:
                    contents = contents[1:-1]
                tags = [sppasTag(c) for c in contents.split('|')]
                if scores is not None:
                    tag_scores = [float(s) for s in scores.split('|')]
                else:
                    tag_scores = None

                # An aligner returns one score for a whole alternative, so its
                # tags are made equiprobable. Alternative tags always have a
                # score, even when the aligner gave none of them.
                if len(tags) > 1:
                    if tag_scores is None or len(tag_scores) != len(tags):
                        tag_scores = [1. / float(len(tags))] * len(tags)

                label = sppasLabel(tags, tag_scores)

                tier.create_annotation(location, label)

        except:
            logging.error('The following data were not added to the tier '
                          '{:s} at position {:f}: {:s}'
                          ''.format(tier.get_name(), delta, str(tdata)))
            logging.error(traceback.format_exc())
            return False

        return True

# ---------------------------------------------------------------------------


class TracksWriter:
    """Write non-aligned track files.

    Manage tracks for the audio, the phonetization and the tokenization.

    """

    @staticmethod
    def serialize_labels_for_aligner(labels, separator=" "):
        """Return the serialized labels, without the score of the tags.

        The aligners are expecting the alternative tags with the "{|}"
        system but none of them supports the "=score" of a tag.

        :param labels: (list of sppasLabel) The labels to serialize
        :param separator: (str) String separating the labels
        :return: (str)

        """
        unscored_labels = list()
        for label in labels:
            tags = [tag for tag, score in label]
            unscored_labels.append(sppasLabel(tags))

        return serialize_labels(unscored_labels, separator=separator, empty="", alt=True)

    # ------------------------------------------------------------------------

    @staticmethod
    def write_tracks(input_audio, phon_tier, tok_tier, tok_rescue_tier, dir_align):
        """Main method to write tracks from the given data.

        :param input_audio: (src) File name of the audio file.
        :param phon_tier: (Tier) Tier with phonetization to split.
        :param tok_tier: (Tier) Tier with tokenization to split.
        :param tok_rescue_tier: (Tier) Tier with tokens to split.
        :param dir_align: (str) Directory to put units.

        :returns: List of tracks with (start-time end-time)

        """
        # Write phonetization and tokenization which is eventually rescued,
        # or raise SizeInputError.
        msg = TracksWriter._write_text_tracks(phon_tier, tok_tier, tok_rescue_tier, dir_align)

        if input_audio is not None:
            if phon_tier.is_interval() is False:
                raise BadInputError
            if tok_tier is not None:
                if tok_tier.is_interval() is False:
                    if tok_rescue_tier.is_interval() is False:
                        raise BadInputError

            tracks = phon_tier.get_midpoint_intervals()
            TracksWriter._write_audio_tracks(input_audio, tracks, dir_align)

        else:
            # No need of an audio if basic alignment
            if phon_tier.is_interval() is True:
                tracks = phon_tier.get_midpoint_intervals()
            else:
                # probably basic alignment of a written text!
                tracks = phon_tier.get_midpoint_points()

        # Write the time values of each track into a file
        ListOfTracks.write(dir_align, tracks)
        return msg

    # ------------------------------------------------------------------------

    @staticmethod
    def _write_audio_tracks(input_audio, units, dir_align, silence=0.):
        """Write the first channel of an audio file into separated track files.

        Re-sample to 16000 Hz, 16 bits.

        :param input_audio: (src) File name of the audio file.
        :param units: (list) List of tuples (start-time,end-time) of tracks.
        :param dir_align: (str) Directory to write audio tracks.
        :param silence: (float) Duration of a silence to surround the tracks.

        """
        audio = audioopy.aio.open(input_audio)
        nbc = audio.get_nchannels()
        if nbc != 1:
            raise AudioChannelError(nb=nbc)
        i = audio.extract_channel(0)
        channel = audio.get_channel(i)
        audio.close()

        channel = audioutils.format_channel(channel, 16000, 2)

        for track, u in enumerate(units):
            (s, e) = u
            track_channel = audioutils.extract_channel_fragment(channel, s, e, silence)
            track_name = TrackNamesGenerator.audio_filename(dir_align, track + 1)
            audioutils.write_channel(track_name, track_channel)

    # ------------------------------------------------------------------------

    @staticmethod
    def _write_text_tracks(phon_tier, tok_tier, tok_rescue_tier, dir_align):
        """Write tokenization and phonetization into separated track files.

        :param phon_tier: (sppasTier) time-aligned tier with phonetization
        :param tok_tier: (sppasTier) time-aligned tier with tokenization
        :param tok_rescue_tier: (sppasTier) time-aligned tier with tokenization
        :param dir_align: (str) the directory to write tracks.
        :raise: SizeInputsError
        :return: (str) warning messages.

        """
        errmsg = ""
        last_chance_tier = TracksWriter._create_tok_tier(phon_tier)
        if tok_rescue_tier is None:
            tok_rescue_tier = last_chance_tier
        if tok_tier is None:
            tok_tier = tok_rescue_tier

        if len(phon_tier) != len(tok_tier):
            msg = "The tier with phonetization is {:d} in length but the tier "\
                  "with tokenization is {:d}.\n".format(len(phon_tier), len(tok_tier))
            logging.warning(msg)
            errmsg += msg
            raise SizeInputsError(len(phon_tier), len(tok_tier))

        for i in range(len(phon_tier)):
            phon_ann = phon_tier[i]
            phon_ann_labels = serialize_labels(phon_ann.get_labels())
            TracksWriter._write_phonemes(phon_ann, dir_align, i + 1)

            tok_ann = tok_tier[i]
            tok_ann_labels = serialize_labels(tok_ann.get_labels())
            if len(phon_ann_labels.split()) != len(tok_ann_labels.split()):
                tok_ann = tok_rescue_tier[i]
                tok_ann_labels = serialize_labels(tok_ann.get_labels())
                msg = "Alignment of tokens rescued at interval {:d}.\n".format(i)
                msg += "The interval with phonetization is {:d} in length but the one " \
                       "with tokenization is {:d}."\
                       "".format(len(phon_ann_labels.split()), len(tok_ann_labels.split()))
                logging.warning(msg)
                errmsg += msg
                if len(phon_ann_labels.split()) != len(tok_ann_labels.split()):
                    tok_ann = last_chance_tier[i]
            TracksWriter._write_tokens(tok_ann, dir_align, i + 1)
        return errmsg

    # ------------------------------------------------------------------------

    @staticmethod
    def _create_tok_tier(phon_tier):
        """Create a tier with tokens like 'w_1 w_2...w_n' from phonemes.

        :param phon_tier: (sppasTier) time-aligned tier with phonetization
        :returns: (sppasTier)

        """
        tok_tier = phon_tier.copy()
        for ann in tok_tier:
            tag = ann.get_best_tag()
            if tag.is_silence() is False:
                phonemes = serialize_labels(ann.get_labels(), " ", "", alt=True)
                nb_phonemes = len(phonemes.split(' '))
                tokens = " ".join(
                    ["w_" + str(i + 1) for i in range(nb_phonemes)]
                )
                ann.set_labels([sppasLabel(sppasTag(tokens))])

        return tok_tier

    # ------------------------------------------------------------------------

    @staticmethod
    def _write_phonemes(annotation, dir_align, number):
        """Write the phonetization of a track in a file.

        :param annotation: (sppasAnnotation)
        :param dir_align: (str)
        :param number: (int)

        """
        phonemes = TracksWriter.serialize_labels_for_aligner(annotation.get_labels())
        fnp = TrackNamesGenerator.phones_filename(dir_align, number)
        with codecs.open(fnp, "w", sg.__encoding__) as fp:
            fp.write(phonemes)

    # ------------------------------------------------------------------------

    @staticmethod
    def _write_tokens(annotation, dir_align, number):
        """Write the tokenization of a track in a file.

        :param annotation: (sppasAnnotation)
        :param dir_align: (str)
        :param number: (int)

        """
        tokens = TracksWriter.serialize_labels_for_aligner(annotation.get_labels())
        fnt = TrackNamesGenerator.tokens_filename(dir_align, number)
        with codecs.open(fnt, "w", sg.__encoding__) as fp:
            fp.write(tokens)

# ---------------------------------------------------------------------------


class ListOfTracks:
    """Manage the file with a list of tracks (units, ipus...).

    """

    DEFAULT_FILENAME = "tracks.list"

    # ------------------------------------------------------------------

    @staticmethod
    def read(dir_name):
        """Return a list of (start-time end-time).

        :param dir_name: Name of the directory with the file to read.
        :returns: list of units

        """
        filename = os.path.join(dir_name, ListOfTracks.DEFAULT_FILENAME)
        if os.path.exists(filename) is False:
            raise IOError('The list of tracks is missing of the directory '
                          '{:s}'.format(dir_name))

        with open(filename, 'r') as fp:
            lines = fp.readlines()
            fp.close()

        # Each line corresponds to a track,
        # with a couple 'start end' of float values.
        _units = list()
        for line in lines:
            s = sppasUnicode(line)
            line = s.to_strip()
            _tab = line.split()
            if len(_tab) >= 2:
                _units.append((float(_tab[0]), float(_tab[1])))

        return _units

    # ------------------------------------------------------------------

    @staticmethod
    def write(dir_name, units):
        """Write a list file (start-time end-time).

        :param dir_name: Name of the directory with the file to read.
        :param units: List of units to write.

        """
        if len(units) == 0:
            raise IOError('No filled tracks were founds in the annotations.')

        # convert points into intervals
        # can happen mainly when written text: IPUs are ranked (1, 2, 3 ...)
        u = units[0]
        if isinstance(u, (tuple, list)) is False:
            u = list()
            for i, midpoint in enumerate(units):
                midpoint = float(midpoint)
                if i+1 < len(units):
                    end = float(units[i+1])
                else:
                    end = midpoint + 1.
                # bug... corrected in SPPAS 4.11.
                # end_midpoint = midpoint + (0.9 * (end-midpoint))
                # u.append((midpoint, end_midpoint))
                u.append((midpoint, end))
            units = u

        filename = os.path.join(dir_name, ListOfTracks.DEFAULT_FILENAME)
        with open(filename, 'w') as fp:
            for start, end in units:
                fp.write("{:6f} {:6f}\n".format(start, end))
            fp.close()
