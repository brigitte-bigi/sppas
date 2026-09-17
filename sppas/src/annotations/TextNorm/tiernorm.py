# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.TextNorm.tiernorm.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Text Normalization of a tier.

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

from sppas.core.config import symbols
from sppas.core.coreutils import info
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasPoint
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasLocation

from .normalize import TextNormalizer

# ---------------------------------------------------------------------------

SIL_ORTHO = list(symbols.ortho.keys())[list(symbols.ortho.values()).index("silence")]

# ---------------------------------------------------------------------------


class TierNormalizer(TextNormalizer):
    """Text normalization automatic annotation of a tier.

    Required resources in order to normalize a text:

        - vocabulary: (sppasVocabulary) List of tokens of a given language
        - dict_replace: (sppasDictRepl) Replacement dictionary
        - vocab_punct: (sppasVocabulary) Punctuation list
        - dict_numbers: (sppasDictRepl) Number convertion dictionary
        - lang: (str) the language code in iso639-3 (fra, eng, vie...).

    """

    def __init__(self, vocab=None, lang="und", logfile=None):
        """Instantiate a text normalizer.

        """
        super(TierNormalizer, self).__init__(vocab, lang)
        self._logfile = logfile

    # -----------------------------------------------------------------------

    def normalize_tier(self, tier, actions):
        """Normalize all tags of all labels of a tier.

        """
        cut_tier = self.__annotations_cut(tier)
        tokens_tier = sppasTier("TextNorm")
        for i, ann in enumerate(cut_tier):
            logging.info((info(1220, "annotations")).format(number=i + 1))
            location = ann.get_location().copy()
            labels = list()
            # Normalize all labels of the orthographic transcription
            for label in ann.get_labels():
                try:
                    # Normalize only the best tag because each label of an ortho
                    # should only concern 1 tag!
                    tokens = self.__do_normalize(label.get_best(), actions)
                except Exception as e:
                    tokens = list()
                    message = (info(1258, "annotations")).format(i) + "{:s}".format(str(e))
                    if self._logfile is not None:
                        self._logfile.print_message((info(1220, "annotations")).format(number=i + 1), indent=1)
                        self._logfile.print_message(message, indent=2)
                    else:
                        logging.info(message)

                # New in SPPAS 1.9.6.
                #  - The result is a sequence of labels.
                #  - Token variants are stored into alternative tags
                # New in SPPAS 5.1.
                #  - Each token is identified by the key of its label
                for tok in tokens:
                    if tok.startswith('{') and tok.endswith('}'):
                        tok = tok[1:-1]
                        tags = [sppasTag(p) for p in tok.split('|')]
                    else:
                        tags = sppasTag(tok)
                    token_label = sppasLabel(tags)
                    token_label.set_key("w_" + str(len(labels) + 1))
                    labels.append(token_label)

            tokens_tier.create_annotation(location, labels)

        self.__add_meta_in_normalized_tier(tokens_tier, actions)
        return tokens_tier

    # -----------------------------------------------------------------------

    def parse_cut_label(self, label, begin=None, end=None):
        """Return the list of cuts of the best tag of a label.

        Caution: Recursion is used...

        :param label: (sppasLabel)
        :param begin: (sppasPoint or -1)
        :param end: (sppasPoint or -1)
        :return: List of tuple(label,from,to) in seconds

        """
        if label.is_string() is False:
            return list()
        tag = label.get_best()
        text = tag.get_typed_content()
        cut_texts = self._cutp.parse_cut(text, begin, end)
        cuts = list()
        for (text, begin, end) in cut_texts:
            label = sppasLabel(sppasTag(text))
            cuts.append((label, begin, end))
        return cuts

    # -----------------------------------------------------------------------

    def __annotations_cut(self, tier):
        """Check if annotations need split by using a "cut" HTML-style tag.

        Do not do anything if the given tier is of type "Point".

        :return: (sppasTier) a copy of the tier with annotation split if "cut" tag

        """
        if tier.is_point() is True:
            return tier

        new_tier = sppasTier("No-name")
        for ann in tier:
            loc = ann.get_location()
            if ann.is_labelled() is False:
                new_tier.append(ann.copy())
            else:
                labels = ann.get_labels()
                b = loc.get_lowest_localization().copy()
                e = loc.get_highest_localization().copy()
                new_labels = list()
                for label in labels:
                    cuts = self.parse_cut_label(label, b, e)
                    if len(cuts) == 0:
                        new_labels.append(label)
                    else:
                        # there are cut tags in the label
                        for i in range(len(cuts)-1):  # ignore the last one
                            # Create an annotation corresponding to the cut information
                            new_labels.append(cuts[i][0])
                            if isinstance(cuts[i][1], sppasPoint) is False:
                                start_time = sppasPoint(cuts[i][1])
                            else:
                                start_time = cuts[i][1]
                            if isinstance(cuts[i][2], sppasPoint) is False:
                                end_time = sppasPoint(cuts[i][2])
                            else:
                                end_time = cuts[i][2]
                            # Create an annotation corresponding to the cut information
                            if end_time > start_time:
                                new_tier.create_annotation(
                                    sppasLocation(sppasInterval(start_time, end_time)),
                                    new_labels)
                                new_labels = list()
                            else:
                                msg = "Invalid cut: from={} to={}".format(cuts[i][1], cuts[i][2])
                                logging.warning(msg)

                        new_labels = list()
                        new_labels.append(cuts[-1][0])
                        b = sppasPoint(cuts[-1][1])

                if e > b:
                    new_tier.create_annotation(sppasLocation(sppasInterval(b, e)), new_labels)
                else:
                    msg = "Invalid interval: from={} to={}".format(b, e)
                    logging.warning(msg)

        return new_tier

    # -----------------------------------------------------------------------

    def __do_normalize(self, text, actions):
        """Return the list of tokens of the text."""
        # Do not tokenize an empty label, noises, laughter...
        if text.is_speech() is True:
            return self.normalize(text.get_content(), actions)
        elif text.is_silence():
            # in ortho a silence could be one of "#" or "gpf_".
            # we normalize!
            return [SIL_ORTHO]
        else:
            return [text.get_content()]

    # -----------------------------------------------------------------------

    def __add_meta_in_normalized_tier(self, tier, enable_actions):
        """Add metadata into a normalized tier.

        """
        tier.set_meta("linguistic_resource_vocab", self.get_vocab_filename())
        tier.set_meta("language", "0")
        for action in ['replace', "tokenize", "numbers", "lower", "punct"]:
            if action in enable_actions:
                tier.set_meta('text_normalization_enable_action_' + action, 'true')
            else:
                tier.set_meta('text_normalization_enable_action_' + action, 'false')
