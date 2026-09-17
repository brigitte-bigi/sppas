# -*- coding: utf8 -*-
"""
:filename: tests.annotations.test_align.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Tests of Alignment automatic annotation.

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

import unittest
import os
import shutil
import codecs

from sppas.core.config import sg
from sppas.core.config import paths
import sppas.src.anndata.aio.aioutils as aioutils
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasPoint
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasAnnotation
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasXRA
from sppas.src.utils.fileutils import sppasFileUtils
from sppas.src.resources import sppasMapping

from sppas.src.annotations.annotationsexc import SizeInputsError

from sppas.src.annotations.Align.tracksio import ListOfTracks
from sppas.src.annotations.Align.tracksio import TrackNamesGenerator
from sppas.src.annotations.Align.tracksio import TracksWriter
from sppas.src.annotations.Align.tracksio import TracksReader
from sppas.src.annotations.Align.tracksio import TracksReaderWriter
from sppas.src.annotations.Align.sppasalign import sppasAlign

from sppas.src.annotations.Align.aligners import sppasAligners
from sppas.src.annotations.Align.aligners.basealigner import BaseAligner
from sppas.src.annotations.Align.aligners.basicalign import BasicAligner
from sppas.src.annotations.Align.aligners.juliusalign import JuliusAligner
from sppas.src.annotations.Align.aligners.hvitealign import HviteAligner
from sppas.src.annotations.Align.aligners.alignerio import BaseAlignersReader
from sppas.src.annotations.Align.aligners.alignerio import palign, walign, mlf

# ---------------------------------------------------------------------------

TEMP = sppasFileUtils().set_random()
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MODELDIR = os.path.join(paths.resources, "models")

# ---------------------------------------------------------------------------


class TestAlignersIO(unittest.TestCase):
    """Readers/writer of the output files of the aligners."""

    def test_BaseAlignersReader(self):
        b = BaseAlignersReader()
        self.assertEqual('', b.extension)
        with self.assertRaises(NotImplementedError):
            b.read('toto')

    def test_getlines(self):
        b = BaseAlignersReader()
        lines = b.get_lines(os.path.join(DATA, "track_000002.palign"))
        self.assertEqual(311, len(lines))

    def test_get_time_units_palign(self):
        b = BaseAlignersReader()
        lines = b.get_lines(os.path.join(DATA, "track_000002.palign"))
        expected_units = [(0, 2), (3, 5), (6, 15), (16, 22), (23, 31),\
                          (32, 34), (35, 37), (38, 40), (41, 60), (61, 63),\
                          (64, 69), (70, 75), (76, 80), (81, 84), (85, 102),\
                          (103, 108), (109, 120), (121, 127), (128, 137),\
                          (138, 141), (142, 145), (146, 155), (156, 167),\
                          (168, 175), (176, 187), (188, 193), (194, 196),\
                          (197, 208), (209, 214), (215, 227), (228, 236),\
                          (237, 240), (241, 252), (253, 264), (265, 282)]

        units = b.get_units_julius(lines)
        self.assertEqual(expected_units, units)
        units = b.units_to_time(units, 100)
        self.assertEqual(0., units[0][0])
        self.assertEqual(0.03, units[0][1])
        self.assertEqual(2.65, units[-1][0])
        self.assertEqual(2.82, units[-1][1])

    def test_shift_time_units(self):
        units = [(0., 0.03), (0.03, 1.)]
        shifted = BaseAlignersReader.shift_time_units(units, 0.01)
        self.assertEqual([(0., 0.04), (0.04, 1.)], shifted)
        shifted = BaseAlignersReader.shift_time_units(shifted, -0.01)
        self.assertEqual(units, shifted)

    def test_get_words_julius_phonemes(self):
        b = BaseAlignersReader()
        lines = b.get_lines(os.path.join(DATA, "track_000002.palign"))
        phonemes = b.get_phonemes_julius(lines)
        words = b.get_words_julius(lines)
        scores = b.get_word_scores_julius(lines)
        self.assertEqual(11, len(words))
        self.assertEqual(11, len(phonemes))
        self.assertEqual(11, len(scores))

    def test_read_palign(self):
        b = palign()
        self.assertEqual("palign", b.extension)
        expected_tokens = \
            [(0.0, 0.07, 'the', None), (0.07, 0.36, 'flight', None),\
             (0.36, 0.62, 'was', None), (0.62, 0.86, 'twelve', None),\
             (0.86, 1.22, 'hours', None), (1.22, 1.43, 'long', None),\
             (1.43, 1.57, 'and', None), (1.57, 1.77, 'we', None),\
             (1.77, 2.1, 'really', None), (2.10, 2.38, 'got', None),\
             (2.38, 2.82, 'bored', None)]

        phones, tokens, prons = b.read(os.path.join(DATA, "track_000002.palign"))
        self.assertEqual(expected_tokens, tokens)
        self.assertEqual(len(expected_tokens), len(prons))
        self.assertEqual(35, len(phones))
        self.assertEqual((0., 0.07, 'dh-ax', '0.618'), prons[0])
        self.assertEqual((1.43, 1.57, 'n-d', '0.510'), prons[6])

    def test_read_walign(self):
        b = walign()
        self.assertEqual("walign", b.extension)
        tokens = b.read(os.path.join(DATA, "track_000000.walign"))
        self.assertEqual(21, len(tokens))
        self.assertEqual((0.21, 0.38, '感', '0.306'), tokens[1])

    def test_get_time_units_mlf(self):
        b = mlf()
        lines = b.get_lines(os.path.join(DATA, "track_sample.mlf"))
        expected_units = [
            (0, 200000), (200000, 400000), (400000, 800000),\
            (800000, 1200000), (1200000, 1500000), (1500000, 1800000),\
            (1800000, 1900000), (1900000, 2400000), (2400000, 2800000)]
        units = b.get_units(lines)
        self.assertEqual(expected_units, units)
        units = b.units_to_time(units, 10e6)
        self.assertEqual(0., units[0][0])
        self.assertEqual(0.02, units[0][1])
        self.assertEqual(0.28, units[-1][1])

    def test_get_phonemes_mlf(self):
        b = mlf()
        lines = b.get_lines(os.path.join(DATA, "track_sample.mlf"))
        phonemes = b.get_phonemes(lines)
        words = b.get_words(lines)
        self.assertEqual(3, len(phonemes))
        self.assertEqual(3, len(words))

    def test_read_mlf(self):
        b = mlf()
        self.assertEqual("mlf", b.extension)
        phones, tokens, prons = b.read(os.path.join(DATA, "track_sample.mlf"))
        expected_tokens = \
            [(0.0, 0.09, 'h#', None),\
             (0.09, 0.19, 'q', None),\
             (0.19, 0.28, 'iy', None)]
        self.assertEqual(expected_tokens, tokens)
        self.assertEqual(len(expected_tokens), len(prons))
        self.assertEqual((0., 0.09, 'h#_s2-h#_s3-h#_s4', None), prons[0])
        self.assertEqual(9, len(phones))

# ---------------------------------------------------------------------------


class TestAligners(unittest.TestCase):
    """Manager of the aligners implemented in the package."""

    def test_check(self):
        """Check whether the aligner name is known or not."""
        aligners = sppasAligners()
        for a in aligners.names():
            self.assertEqual(a, aligners.check(a))

        with self.assertRaises(KeyError):
            aligners.check("invalid")

    # -----------------------------------------------------------------------

    def test_instantiate(self):
        """Instantiate an aligner to the appropriate Aligner system."""
        aligners = sppasAligners()
        for a in aligners.names():
            aligner = aligners.instantiate(None, a)
            self.assertTrue(isinstance(aligner,
                                       aligners.classes(a)))

        with self.assertRaises(KeyError):
            aligners.instantiate(None, "invalid")

# ---------------------------------------------------------------------------


class TestBaseAligner(unittest.TestCase):
    """Base class for any automatic alignment system."""

    def setUp(self):
        self._aligner = BaseAligner()

    def test_get_members(self):
        self.assertEqual("", self._aligner.outext())
        self.assertEqual(list(), self._aligner.extensions())
        self.assertEqual("", self._aligner.name())
    #
    # def test_infersp(self):
    #     self.assertFalse(self._aligner.get_infersp())
    #     self._aligner.set_infersp(True)
    #     self.assertTrue(self._aligner.get_infersp())
    #     self._aligner.set_infersp("ejzkjg")
    #     self.assertFalse(self._aligner.get_infersp())

    def test_norun(self):
        with self.assertRaises(NotImplementedError):
            self._aligner.run_alignment("audio", "output")

    def test_set_data(self):
        # tokens and phones must be strings
        with self.assertRaises(Exception):
            self._aligner.set_phones(3)
        with self.assertRaises(Exception):
            self._aligner.set_tokens(3)

        # tokens matching phones
        self._aligner.set_phones("a b c")
        self._aligner.set_tokens("w1 w2 w3")
        self.assertEqual("", self._aligner.check_data())  # no error msg
        self.assertEqual("w1 w2 w3", self._aligner._tokens)

        # tokens not matching phones
        self._aligner.set_tokens("w1www")
        self.assertTrue(len(self._aligner.check_data()) > 20)  # error msg
        self.assertEqual("w_0 w_1 w_2", self._aligner._tokens)

# ---------------------------------------------------------------------------


class TestBasicAlign(unittest.TestCase):
    """Basic automatic alignment system."""

    def setUp(self):
        self._aligner = BasicAligner()

    def test_run_basic_indexes(self):
        self._aligner.set_phones("")
        self.assertEqual([(0, 0, "")], self._aligner.run_basic(0.))
        self.assertEqual([(0, 1, "")], self._aligner.run_basic(0.01))
        self.assertEqual([(0, 2, "")], self._aligner.run_basic(0.02))
        self.assertEqual([(0, 20, "")], self._aligner.run_basic(0.2))
        self.assertEqual([(0, 1000, "")], self._aligner.run_basic(10.))

        self._aligner.set_phones("a")
        self.assertEqual([(0, 0, "")], self._aligner.run_basic(0.))
        self.assertEqual([(0, 1, "a")], self._aligner.run_basic(0.02))
        self.assertEqual([(0, 1, "a")], self._aligner.run_basic(0.02))

        self._aligner.set_phones("a b c")
        self.assertEqual([(0, 2, "")], self._aligner.run_basic(0.02))

        self._aligner.set_phones("a b")
        self.assertEqual([(0, 9, "a"), (10, 19, "b")],
                          self._aligner.run_basic(0.2))

        self._aligner.set_phones("a|aa b|bb")
        self.assertEqual([(0, 9, "a"), (10, 19, "b")],
                          self._aligner.run_basic(0.2))

        self._aligner.set_phones("a|A b|B")
        self.assertEqual([(0, 9, "a"), (10, 19, "b")],
                          self._aligner.run_basic(0.2))

    def test_run_basic_times(self):
        # No phoneme
        self._aligner.set_phones("")
        self.assertEqual([(0., 0., "")], self._aligner.run_basic())

        # Only one phoneme
        self._aligner.set_phones("a")
        self.assertEqual([(0., 0.12, "a")], self._aligner.run_basic())
        self._aligner.set_phones("#")
        self.assertEqual([(0., 0.5, "#")], self._aligner.run_basic())

        # A sequence of phonemes
        self._aligner.set_phones("a b|bb")
        self.assertEqual([(0., 0.12, "a"), (0.12, 0.24, "b")],
                         self._aligner.run_basic())

        # Phonemes and events
        self._aligner.set_phones("a + b|bb")
        self.assertEqual([(0., 0.12, "a"), (0.12, 0.62, "+"), (0.62, 0.74, "b")],
                         self._aligner.run_basic())

# ---------------------------------------------------------------------------


class TestJuliusAlign(unittest.TestCase):

    def setUp(self):
        self._modeldir = os.path.join(MODELDIR, "models-fra")
        self._aligner = JuliusAligner(self._modeldir)

# ---------------------------------------------------------------------------


class TestHviteAlign(unittest.TestCase):

    def setUp(self):
        self._modeldir = os.path.join(MODELDIR, "models-fra")
        self._aligner = HviteAligner(self._modeldir)

# ---------------------------------------------------------------------------


class TestTrackNamesGenerator(unittest.TestCase):
    """Manage names of the files for a given track number."""

    def test_names(self):
        """Test all generators: audio, phones, tokens, align."""
        # audio
        self.assertEqual("track_000001.wav",
                         TrackNamesGenerator.audio_filename("", 1))
        # phones
        self.assertEqual("track_000001.phn",
                         TrackNamesGenerator.phones_filename("", 1))
        # tokens
        self.assertEqual("track_000001.tok",
                         TrackNamesGenerator.tokens_filename("", 1))
        # aligned file
        self.assertEqual("track_000001",
                         TrackNamesGenerator.align_filename("", 1))
        self.assertEqual("track_000001.palign",
                         TrackNamesGenerator.align_filename("", 1, "palign"))

# ---------------------------------------------------------------------------


class TestListOfTracks(unittest.TestCase):
    """Write track files."""

    def setUp(self):
        if os.path.exists(TEMP) is False:
            os.mkdir(TEMP)

    def tearDown(self):
        shutil.rmtree(TEMP)

    # -----------------------------------------------------------------------

    def test_read_write_interval(self):
        """Manage the file with a list of tracks (units, ipus...)."""
        units = [(1., 2.), (2., 3.), (3., 4.)]
        ListOfTracks.write(TEMP, units)
        read_units = ListOfTracks.read(TEMP)
        self.assertEqual(units, read_units)

        with self.assertRaises(IOError):
            ListOfTracks.read("toto")

    # -----------------------------------------------------------------------

    def test_read_write_point(self):
        units = [1, 2]
        ListOfTracks.write(TEMP, units)
        read_units = ListOfTracks.read(TEMP)
        self.assertEqual([(1.0, 2.0), (2.0, 3.0)], read_units)

# ---------------------------------------------------------------------------


class TestTracksWriter(unittest.TestCase):
    """Write track files."""

    def setUp(self):
        if os.path.exists(TEMP) is False:
            os.mkdir(TEMP)

    def tearDown(self):
        shutil.rmtree(TEMP)

    # -----------------------------------------------------------------------

    def test_write_tokens(self):
        """Write the tokenization of a track in a file."""
        # test to write an annotation with complex labels
        l1 = sppasLabel([sppasTag("option1"), sppasTag("alt1")])
        l2 = sppasLabel([sppasTag("option2"), sppasTag("alt2")])
        ann = sppasAnnotation(sppasLocation(sppasPoint(1)), [l1, l2])
        TracksWriter._write_tokens(ann, TEMP, 1)
        fn = os.path.join(TEMP, "track_000001.tok")
        self.assertTrue(os.path.exists(fn))
        with codecs.open(fn, "r", sg.__encoding__) as fp:
            lines = fp.readlines()
            fp.close()
        self.assertEqual(1, len(lines))
        self.assertEqual("{option1|alt1} {option2|alt2}", lines[0])

        # test to write an annotation with already serialized labels
        sentence = "A serialized list of {labels|tags}"
        ann = sppasAnnotation(
            sppasLocation(sppasPoint(1)),
            sppasLabel(sppasTag(sentence)))
        TracksWriter._write_tokens(ann, TEMP, 2)
        fn = os.path.join(TEMP, "track_000002.tok")
        self.assertTrue(os.path.exists(fn))
        with codecs.open(fn, "r", sg.__encoding__) as fp:
            lines = fp.readlines()
            fp.close()
        self.assertEqual(1, len(lines))
        self.assertEqual(sentence, lines[0])

    # -----------------------------------------------------------------------

    def test_write_phonemes(self):
        """Write the phonetization of a track in a file."""
        # test to write an annotation with complex labels
        l1 = sppasLabel([sppasTag("j"), sppasTag("S")])
        l2 = sppasLabel([sppasTag("e"), sppasTag("E")])
        ann = sppasAnnotation(sppasLocation(sppasPoint(1)), [l1, l2])
        TracksWriter._write_phonemes(ann, TEMP, 1)
        fn = os.path.join(TEMP, "track_000001.phn")
        self.assertTrue(os.path.exists(fn))
        with codecs.open(fn, "r", sg.__encoding__) as fp:
            lines = fp.readlines()
            fp.close()
        self.assertEqual(1, len(lines))
        self.assertEqual("{j|S} {e|E}", lines[0])

        # test to write an annotation with already serialized labels
        sentence = "A serialized list of {labels|tags}"
        ann = sppasAnnotation(
            sppasLocation(sppasPoint(1)),
            sppasLabel(sppasTag(sentence)))
        TracksWriter._write_phonemes(ann, TEMP, 2)
        fn = os.path.join(TEMP, "track_000002.phn")
        self.assertTrue(os.path.exists(fn))
        with codecs.open(fn, "r", sg.__encoding__) as fp:
            lines = fp.readlines()
            fp.close()
        self.assertEqual(1, len(lines))
        self.assertEqual(sentence, lines[0])

    # -----------------------------------------------------------------------

    def test_create_tok_tier(self):
        """Create a tier with tokens like 'w_1 w_2...w_n' from phonemes."""
        l1 = sppasLabel([sppasTag("j"), sppasTag("S")])
        l2 = sppasLabel([sppasTag("e"), sppasTag("E")])
        tier = sppasTier("phonemes")
        tier.create_annotation(sppasLocation(sppasPoint(1)),
                               [l1, l2])
        tier.create_annotation(sppasLocation(sppasPoint(2)),
                               sppasLabel(sppasTag("{j|S} {e|E}")))
        tok_tier = TracksWriter._create_tok_tier(tier)
        self.assertEqual(2, len(tok_tier))
        content_a1 = tok_tier[0].get_best_tag().get_content()
        self.assertEqual("w_1 w_2", content_a1)
        content_a2 = tok_tier[1].get_best_tag().get_content()
        self.assertEqual("w_1 w_2", content_a2)

    # -----------------------------------------------------------------------

    def test_write_text_tracks(self):
        """Write tokenization and phonetization into separated track files."""
        l1 = sppasLabel([sppasTag("j"), sppasTag("S")])
        l2 = sppasLabel([sppasTag("e"), sppasTag("E")])
        tier_phn = sppasTier("phonemes")
        tier_phn.create_annotation(sppasLocation(sppasPoint(1)),
                                   [l1, l2])
        tier_phn.create_annotation(sppasLocation(sppasPoint(2)),
                                   sppasLabel(sppasTag("j-e s-H-i")))
        tier_tok = sppasTier("tokens")
        tier_tok.create_annotation(sppasLocation(sppasPoint(1)),
                                   sppasLabel(sppasTag("j' ai")))
        tier_tok.create_annotation(sppasLocation(sppasPoint(2)),
                                   sppasLabel(sppasTag('je suis')))

        with self.assertRaises(SizeInputsError):
            TracksWriter._write_text_tracks(tier_phn, sppasTier('toto'), None, TEMP)

        dir_tracks = os.path.join(TEMP, "test_write_text_tracks_1")
        os.mkdir(dir_tracks)
        TracksWriter._write_text_tracks(tier_phn, None, None, dir_tracks)
        created_files = os.listdir(dir_tracks)
        self.assertEqual(4, len(created_files))
        lines = list()
        for fn in created_files:
            with codecs.open(os.path.join(dir_tracks, fn), "r", sg.__encoding__) as fp:
                new_lines = fp.readlines()
                fp.close()
            self.assertEqual(1, len(new_lines))
            lines.append(new_lines[0])
        self.assertTrue("w_1 w_2" in lines)
        self.assertTrue("{j|S} {e|E}" in lines)
        self.assertTrue("j-e s-H-i" in lines)

        dir_tracks = os.path.join(TEMP, "test_write_text_tracks_2")
        os.mkdir(dir_tracks)
        TracksWriter._write_text_tracks(tier_phn, tier_tok, None, dir_tracks)
        created_files = os.listdir(dir_tracks)
        self.assertEqual(4, len(created_files))
        lines = list()
        for fn in created_files:
            with codecs.open(os.path.join(dir_tracks, fn), "r", sg.__encoding__) as fp:
                new_lines = fp.readlines()
                fp.close()
            self.assertEqual(1, len(new_lines))
            lines.append(new_lines[0])
        self.assertTrue("j' ai" in lines)
        self.assertTrue("je suis" in lines)
        self.assertTrue("{j|S} {e|E}" in lines)
        self.assertTrue("j-e s-H-i" in lines)

    # -----------------------------------------------------------------------

    def test_write_audio_tracks(self):
        """Write the first channel of an audio file into separated track files."""
        pass

    # -----------------------------------------------------------------------

    def test_write_tracks(self):
        """Main method to write tracks from the given data."""
        pass

# ---------------------------------------------------------------------------


class TestTracksReader(unittest.TestCase):
    """Read time-aligned track files."""

    def test_read(self):
        tier_phn, tier_tok, tier_pron = TracksReader().read_aligned_tracks(DATA)
        self.assertEqual(36, len(tier_phn))
        self.assertEqual(12, len(tier_tok))
        self.assertEqual(12, len(tier_pron))

        self.assertEqual("dh", aioutils.serialize_labels(tier_phn[1].get_labels()))
        self.assertEqual("ax", aioutils.serialize_labels(tier_phn[2].get_labels()))
        self.assertEqual("f", aioutils.serialize_labels(tier_phn[3].get_labels()))
        self.assertEqual("l", aioutils.serialize_labels(tier_phn[4].get_labels()))
        self.assertEqual("ay", aioutils.serialize_labels(tier_phn[5].get_labels()))
        self.assertEqual("t", aioutils.serialize_labels(tier_phn[6].get_labels()))

        # The score of a time-aligned token is serialized with its content
        self.assertEqual("dh-ax=0.618", aioutils.serialize_labels(tier_pron[1].get_labels()))
        self.assertTrue("f-l-ay-t" in aioutils.serialize_labels(tier_pron[2].get_labels()))

# ---------------------------------------------------------------------------


class TestTracksReaderWriter(unittest.TestCase):
    """Read/Write track files."""

    def setUp(self):
        if os.path.exists(TEMP) is False:
            os.mkdir(TEMP)

    def tearDown(self):
        shutil.rmtree(TEMP)

    # -----------------------------------------------------------------------

    def test_init(self):
        with self.assertRaises(TypeError):
            TracksReaderWriter("")
        t1 = TracksReaderWriter(sppasMapping())
        t2 = TracksReaderWriter(None)

    # -----------------------------------------------------------------------

    def test_split_into_tracks_alternatives_with_scores(self):
        """Test the tracks of alternative tags having a score."""
        phon_tier = sppasTier("Phones")
        phon_tier.create_annotation(
            sppasLocation(sppasInterval(sppasPoint(0.), sppasPoint(1.))),
            [sppasLabel([sppasTag("D-@"), sppasTag("D-i:")], [0.5, 0.5]),
             sppasLabel(sppasTag("f-l-aI-t"), 0.8)])
        tok_tier = sppasTier("Tokens")
        tok_tier.create_annotation(
            sppasLocation(sppasInterval(sppasPoint(0.), sppasPoint(1.))),
            [sppasLabel([sppasTag("the"), sppasTag("a")], [0.5, 0.5]),
             sppasLabel(sppasTag("flight"))])

        t = TracksReaderWriter(sppasMapping())
        t.split_into_tracks(None, phon_tier, tok_tier, None, TEMP)

        # None of the aligners supports the score of a tag, so the tracks
        # are expected to be written without any of them.
        with codecs.open(os.path.join(TEMP, "track_000001.phn"), "r", sg.__encoding__) as fp:
            phonemes = fp.read()
        self.assertEqual("D-@|D-i: f-l-aI-t", phonemes)

        with codecs.open(os.path.join(TEMP, "track_000001.tok"), "r", sg.__encoding__) as fp:
            tokens = fp.read()
        self.assertEqual("{the|a} flight", tokens)

    # -----------------------------------------------------------------------

    def test_split_into_tracks_without_mapping(self):
        """Test to read and write tracks without mapping."""
        audio = os.path.join(DATA, "oriana1.wav")
        phon = os.path.join(DATA, "oriana1-phon.xra")
        token = os.path.join(DATA, "oriana1-token.xra")
        t = sppasXRA()
        t.read(phon)
        t.read(token)
        phn_tier = t.find('Phones')
        tok_tier = t.find('Tokens')

        trks = TracksReaderWriter(None)  # no mapping table
        temp = os.path.join(TEMP, "test_split1")
        os.mkdir(temp)

        trks.split_into_tracks(audio, phn_tier, tok_tier, None, temp)
        created_files = os.listdir(temp)
        self.assertEqual(22, len(created_files))   # 21 tracks + List

        # Tokenization of the 1st IPU
        with codecs.open(os.path.join(temp, "track_000002.tok"),
                         "r", sg.__encoding__) as fp:
            new_lines = fp.readlines()
            fp.close()
        self.assertEqual(1, len(new_lines))
        self.assertEqual("the flight was twelve hours long and "
                         "we really got bored",
                         new_lines[0])

        # Phonetization of the 1st IPU
        with codecs.open(os.path.join(temp, "track_000002.phn"),
                         "r", sg.__encoding__) as fp:
            new_lines = fp.readlines()
            fp.close()
        self.assertEqual(1, len(new_lines))
        self.assertEqual("D-@|D-i:|D-V "
                         "f-l-aI-t "
                         "w-@-z|w-V-z|w-O:-z|w-A-z "
                         "t-w-E-l-v "
                         "aU-3:r-z|aU-r\-z "
                         "l-O:-N "
                         "{-n-d|@-n-d "
                         "w-i: "
                         "r\-I-l-i:|r\-i:-l-i: "
                         "g-A-t "
                         "b-O:-r\-d",
                         new_lines[0])

    # -----------------------------------------------------------------------

    def test_split_into_tracks_with_mapping(self):
        """Test to read and write tracks with mapping."""
        audio = os.path.join(DATA, "oriana1.wav")
        phon = os.path.join(DATA, "oriana1-phon.xra")
        token = os.path.join(DATA, "oriana1-token.xra")
        t = sppasXRA()
        t.read(phon)
        t.read(token)
        phn_tier = t.find('Phones')
        tok_tier = t.find('Tokens')

        trks = TracksReaderWriter(sppasMapping(
            os.path.join(DATA, "monophones.repl")
        ))
        temp = os.path.join(TEMP, "test_split2")
        os.mkdir(temp)

        trks.split_into_tracks(audio, phn_tier, tok_tier, None, temp)
        created_files = os.listdir(temp)
        self.assertEqual(22, len(created_files))  # 21 tracks + List

        # Tokenization of the 1st IPU
        with codecs.open(os.path.join(temp, "track_000002.tok"),
                         "r", sg.__encoding__) as fp:
            new_lines = fp.readlines()
            fp.close()
        self.assertEqual(1, len(new_lines))
        self.assertEqual("the flight was twelve hours long and "
                         "we really got bored",
                         new_lines[0])

        # Phonetization of the 1st IPU
        with codecs.open(os.path.join(temp, "track_000002.phn"),
                         "r", sg.__encoding__) as fp:
            new_lines = fp.readlines()
            fp.close()
        self.assertEqual(1, len(new_lines))
        self.assertEqual("dh-ax|dh-iy|dh-ah "
                         "f-l-ay-t "
                         "w-ax-z|w-ah-z|w-ao-z|w-aa-z "
                         "t-w-eh-l-v "
                         "aw-er-z|aw-r-z "
                         "l-ao-ng "
                         "ae-n-d|ax-n-d "
                         "w-iy "
                         "r-ih-l-iy|r-iy-l-iy "
                         "g-aa-t "
                         "b-ao-r-d",
                         new_lines[0])

    # -----------------------------------------------------------------------

    def test_read_aligned_tracks(self):
        trks = TracksReaderWriter(sppasMapping(
            os.path.join(DATA, "monophones.repl")
        ))

        tier_phn, tier_tok, tier_pron = trks.read_aligned_tracks(DATA)
        self.assertEqual(36, len(tier_phn))
        self.assertEqual(12, len(tier_tok))
        self.assertEqual(12, len(tier_pron))

        self.assertEqual("D", aioutils.serialize_labels(tier_phn[1].get_labels()))
        self.assertEqual("@", aioutils.serialize_labels(tier_phn[2].get_labels()))
        self.assertEqual("f", aioutils.serialize_labels(tier_phn[3].get_labels()))
        self.assertEqual("l", aioutils.serialize_labels(tier_phn[4].get_labels()))
        self.assertEqual("aI", aioutils.serialize_labels(tier_phn[5].get_labels()))
        self.assertEqual("t", aioutils.serialize_labels(tier_phn[6].get_labels()))

        self.assertTrue(aioutils.serialize_labels(tier_pron[1].get_labels()).startswith("D-@"))
        ann = tier_pron[2]
        self.assertEqual("f-l-aI-t", aioutils.serialize_labels(ann.get_labels()))

# ---------------------------------------------------------------------------


class TestAlign(unittest.TestCase):
    """SPPAS Alignment."""

    def setUp(self):
        if os.path.exists(TEMP) is False:
            os.mkdir(TEMP)

    def tearDown(self):
        shutil.rmtree(TEMP)

    # -----------------------------------------------------------------------

    def test_init(self):
        model = os.path.join(paths.resources, "models", 'models-eng')
        model1 = os.path.join(paths.resources, "models", 'models-fra')
        s = sppasAlign()
        s.load_resources(model)
        s.load_resources(model, model1)
        # with self.assertRaises(IOError):
        #     s.load_resources("toto")

    # -----------------------------------------------------------------------

    def test_convert(self):
        model = os.path.join(paths.resources, "models", 'models-eng')
        audio = os.path.join(DATA, "oriana1.wav")
        phon = os.path.join(DATA, "oriana1-phon.xra")
        token = os.path.join(DATA, "oriana1-token.xra")
        t = sppasXRA()
        t.read(phon)
        t.read(token)
        phn_tier = t.find('Phones')
        tok_tier = t.find('Tokens')

        a = sppasAlign()
        a.load_resources(model)

        tier_phn, tier_tok, tier_pron = a.convert(phn_tier, tok_tier, None, audio, TEMP)

        self.assertEqual(123, len(tier_phn))
        self.assertEqual(39, len(tier_tok))
        self.assertEqual(39, len(tier_pron))

        self.assertEqual("D", aioutils.serialize_labels(tier_phn[1].get_labels()))
        self.assertEqual("@", aioutils.serialize_labels(tier_phn[2].get_labels()))
        self.assertEqual("f", aioutils.serialize_labels(tier_phn[3].get_labels()))
        self.assertEqual("l", aioutils.serialize_labels(tier_phn[4].get_labels()))
        self.assertEqual("aI", aioutils.serialize_labels(tier_phn[5].get_labels()))
        self.assertEqual("t", aioutils.serialize_labels(tier_phn[6].get_labels()))
        # The aligner selected the "@-n-d" variant of "and" among the others
        self.assertEqual("@", aioutils.serialize_labels(tier_phn[21].get_labels()))
        self.assertEqual("@-n-d=0.812", aioutils.serialize_labels(tier_pron[7].get_labels()))

    # -----------------------------------------------------------------------

    def test_samples_fra(self):
        """... Compare if the current result is the same as the existing one."""
        self.compare_samples("fra")

    # -----------------------------------------------------------------------
    #
    def test_samples_cat(self):
        """... Compare if the current result is the same as the existing one."""
        self.compare_samples("cat")

    # -----------------------------------------------------------------------

    def test_samples_cmn(self):
        """... Compare if the current result is the same as the existing one."""
        self.compare_samples("cmn")

    # -----------------------------------------------------------------------

    def test_samples_eng(self):
        """... Compare if the current result is the same as the existing one."""
        self.compare_samples("eng")

    # -----------------------------------------------------------------------
    # internal
    # -----------------------------------------------------------------------

    def compare_samples(self, lang):
        samples_folder = os.path.join(paths.samples, "samples-"+lang)

        # the place where are the existing results samples.
        expected_result_dir = os.path.join(paths.samples,
                                           "annotation-results",
                                           "samples-" + lang)

        # Create an Aligner for the given set of samples of the given language
        sa = sppasAlign()
        sa.load_resources(os.path.join(paths.resources, "models", "models-"+lang))
        self.compare_folders(samples_folder, expected_result_dir, sa)

    # -----------------------------------------------------------------------

    def compare_folders(self, samples_folder, expected_result_dir, sa):
        # Apply Alignment on each sample
        for filename in os.listdir(os.path.join(paths.samples, samples_folder)):
            if filename.endswith(".wav") is False:
                continue

            # Get the expected result
            expected_result_filename = os.path.join(
                expected_result_dir,
                filename[:-4] + "-palign.xra")
            if os.path.exists(expected_result_filename) is False:
                print("no existing alignment result {:s}".format(expected_result_filename))
                continue
            parser = sppasTrsRW(expected_result_filename)
            expected_result = parser.read()
            expected_tier_phones = expected_result.find('PhonAlign')
            if expected_tier_phones is None:
                print("malformed alignment result for:", filename)
                continue

            # Estimate a result and check if it's like expected.
            audio_file = os.path.join(paths.samples, samples_folder, filename)
            phn_file = os.path.join(expected_result_dir, filename.replace('.wav', '-phon.xra'))
            tok_file = os.path.join(expected_result_dir, filename.replace('.wav', '-token.xra'))
            result_file = os.path.join(paths.samples, samples_folder, filename.replace('.wav', '-palign.xra'))
            expected_result = sa.run([phn_file, audio_file, tok_file], result_file)
            print('Evaluate:', audio_file)

            self.compare_tiers(expected_tier_phones,
                               expected_result.find('PhonAlign'))

    # -----------------------------------------------------------------------

    def compare_tiers(self, expected, result):
        self.assertEqual(len(expected), len(result))
        for a1, a2 in zip(expected, result):
            self.assertEqual(a1.get_location(), a2.get_location())
            self.assertEqual(len(a1.get_labels()), len(a2.get_labels()))
            for l1, l2 in zip(a1.get_labels(), a2.get_labels()):
                self.assertEqual(l1, l2)
            for key in a1.get_meta_keys():
                if key != 'id':
                    self.assertEqual(a1.get_meta(key), a2.get_meta(key))
        for key in expected.get_meta_keys():
            if key != 'id':
                self.assertEqual(expected.get_meta(key), result.get_meta(key))
