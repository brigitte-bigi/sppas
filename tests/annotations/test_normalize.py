# -*- coding: UTF-8 -*-
"""
:filename: tests.annotations.test_normalize.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Tests of Text Normalization automatic annotation.

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

import unittest
import os
import shutil

from sppas.core.config import paths

from sppas.src.anndata.anndataexc import AioEncodingError
from sppas.core.coreutils import u
from sppas.src.resources.vocab import sppasVocabulary
from sppas.src.resources.dictrepl import sppasDictRepl
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag
from sppas.src.anndata.transcription import sppasTranscription
from sppas.src.anndata.tier import sppasTier
from sppas.src.anndata.aio.aioutils import serialize_labels
from sppas.src.anndata.ann.annotation import sppasAnnotation
from sppas.src.anndata.ann.annlocation import sppasLocation
from sppas.src.anndata.ann.annlocation import sppasInterval
from sppas.src.anndata.ann.annlocation import sppasPoint
from sppas.src.structs.baseoption import sppasOption
from sppas.src.utils.fileutils import sppasFileUtils

from sppas.src.annotations.TextNorm.normalize import TextNormalizer
from sppas.src.annotations.TextNorm.orthotranscription import sppasOrthoTranscription
from sppas.src.annotations.TextNorm.tokenize import sppasTokenSegmenter
from sppas.src.annotations.TextNorm.splitter import sppasSimpleSplitter
from sppas.src.annotations.TextNorm.tiernorm import TierNormalizer
from sppas.src.annotations.TextNorm.cutparser import ParseCut
from sppas.src.annotations.TextNorm.sppastextnorm import sppasTextNorm

# ---------------------------------------------------------------------------

TEMP = sppasFileUtils().set_random()

# ---------------------------------------------------------------------------


class TestOrthoTranscription(unittest.TestCase):
    """Test of the class sppasOrthoTranscription.
    Manager of an orthographic transcription.

    """

    def test_clean_toe(self):
        """... Clean Enriched Orthographic Transcription to get a standard ortho."""

        s = sppasOrthoTranscription().clean_toe(u('(il) (ne) faut pas rêver'))
        self.assertEqual(u("faut pas rêver"), s)

        s = sppasOrthoTranscription().clean_toe(u('i(l) (ne) faut pas réver'))
        self.assertEqual(u("i(l) faut pas réver"), s)

        s = sppasOrthoTranscription().clean_toe(u('i(l) (ne) faut pas réver'))
        self.assertEqual(u("i(l) faut pas réver"), s)

        s = sppasOrthoTranscription().clean_toe(u(' (il) faut pas réver i(l)'))
        self.assertEqual(u("faut pas réver i(l)"), s)

        s = sppasOrthoTranscription().clean_toe(u(' euh [je sais, ché] pas '))
        self.assertEqual(u("euh [je_sais,ché] pas"), s)

        s = sppasOrthoTranscription().clean_toe(u("  j'[ avais,  avé ] "))
        self.assertEqual(u("j' [avais,avé]"), s)

        s = sppasOrthoTranscription().clean_toe(u("  [j(e) sais,  ché ] "))
        self.assertEqual(u("[je_sais,ché]"), s)

        s = sppasOrthoTranscription().clean_toe(u("  [peut-êt(re),  pe êt] "))
        self.assertEqual(u("[peut-être,peêt]"), s)

        s = sppasOrthoTranscription().clean_toe(u(" (pu)tai(n) j'ai"))
        self.assertEqual(u("(pu)tai(n) j'ai"), s)

        s = sppasOrthoTranscription().clean_toe(u("gpd_100y en a un  qu(i) est devenu complèt(e)ment  "))
        self.assertEqual(u("y en a un qu(i) est devenu complèt(e)ment"), s)

        s = sppasOrthoTranscription().clean_toe(u("gpd_1324ah euh"))
        self.assertEqual(u("ah euh"), s)

        s = sppasOrthoTranscription().clean_toe(u("ipu_1324ah euh"))
        self.assertEqual(u("ah euh"), s)

        s = sppasOrthoTranscription().clean_toe(u("ah a/b euh"))
        self.assertEqual(u("ah a/b euh"), s)

        s = sppasOrthoTranscription().clean_toe(u("l'abat-jour"))
        self.assertEqual(u("l'abat-jour"), s)

        # Proper names with "$" convention has changed in SPPAS 4.12.
        # The following is no longer supported:
        # s = sppasOrthoTranscription().clean_toe(u("[$Londre, T/$, Londreu]"))
        # self.assertEqual(u("[Londre,Londreu]"), s)
        # s = sppasOrthoTranscription().clean_toe(u("t(u) vois [$Isabelle,P /$, isabelleu] $Armelle,P /$ t(out) ça"))
        # self.assertEqual(u("t(u) vois [Isabelle,isabelleu] Armelle t(out) ça"), s)
        # Use this instead:
        s = sppasOrthoTranscription().clean_toe(u("[Londre, Londreu]"))
        self.assertEqual(u("[Londre,Londreu]"), s)
        s = sppasOrthoTranscription().clean_toe(u("t(u) vois [$Isabelle$, isabelleu] $Armelle$ t(out) ça"))
        self.assertEqual(u("t(u) vois [$Isabelle$,isabelleu] $Armelle$ t(out) ça"), s)
        s = sppasOrthoTranscription().clean_toe(u("Here are proper names $John_Doe$ and $D-J._Doe$"))
        self.assertEqual(u("Here are proper names $John_Doe$ and $D-J._Doe$"), s)

    # -----------------------------------------------------------------------

    def test_toe_spelling(self):
        """... Create a specific spelling from an Enriched Orthographic Transcription."""

        s = sppasOrthoTranscription().toe_spelling(u('je, fais: "un essai".'))
        self.assertEqual(u('je , fais : " un essai " .'), s)

        s = sppasOrthoTranscription().toe_spelling(u('€&serie de punctuations!!!):-)".'))
        self.assertEqual(u('€ & serie de punctuations ! ! ! ) : - ) " .'), s)

        s = sppasOrthoTranscription().toe_spelling(u('123,2...'))
        self.assertEqual(u('123,2 . . .'), s)

        # this is sampa to be sent directly to the phonetizer
        s = sppasOrthoTranscription().toe_spelling(u(" /l-e-f-o~-n/ "))
        self.assertEqual(u('/l-e-f-o~-n/'), s)

        # this is not sampa, because sampa can't contain whitespace.
        s = sppasOrthoTranscription().toe_spelling(u('/le mot/'))
        self.assertEqual(u('/ le mot /'), s)

        s = sppasOrthoTranscription().toe_spelling(u('(/'))
        self.assertEqual(u('( / '), s)

        s = sppasOrthoTranscription().toe_spelling("un {commentaire} chat")
        self.assertEqual("un chat", s)
        s = sppasOrthoTranscription().toe_spelling("un {com-mentaire} chat")
        self.assertEqual("un chat", s)
        s = sppasOrthoTranscription().toe_spelling("un [commentaire: hello] chat")
        self.assertEqual("un chat", s)
        s = sppasOrthoTranscription().toe_spelling("@@ un @ chat @@")
        self.assertEqual("un @  chat", s)
        s = sppasOrthoTranscription().toe_spelling("un*chat")
        self.assertEqual("un *  chat", s)
        s = sppasOrthoTranscription().toe_spelling("l(e) chat")
        self.assertEqual("l chat", s)
        s = sppasOrthoTranscription().toe_spelling("le chat $Gros-Minet$")
        self.assertEqual("le chat $Gros-Minet$", s)

    # -----------------------------------------------------------------------

    def test_toe(self):
        """... Apply both clean_toe then toe_spelling."""

        s = sppasOrthoTranscription().clean_toe(u(" /l-e-f-o~-n/ "))
        s = sppasOrthoTranscription().toe_spelling(s)
        self.assertEqual(u('/l-e-f-o~-n/'), s)

        s = sppasOrthoTranscription().clean_toe(u(" /le mot/ "))
        s = sppasOrthoTranscription().toe_spelling(s)
        self.assertEqual(u('/ le mot /'), s)

# ---------------------------------------------------------------------------


class TestSimpleSplitter(unittest.TestCase):
    """Test of Utterance splitter."""

    def test_split_characters(self):
        """... Split a character-based string."""

        splitter = sppasSimpleSplitter("cmn")
        result = splitter.split_characters("干脆就把那部蒙人的闲法给废了拉倒")
        expected = u("干 脆 就 把 那 部 蒙 人 的 闲 法 给 废 了 拉 倒")
        self.assertEqual(expected, result)

        result = splitter.split_characters("abc123")
        expected = u(" abc123 ")
        self.assertEqual(expected, result)

        splitter = sppasSimpleSplitter("fra")
        result = splitter.split_characters("l'abat-jour")
        expected = u(" l ' abat - jour ")
        self.assertEqual(expected, result)

    # -----------------------------------------------------------------------

    def test_split(self):
        """... Split a character-based or romanized string."""

        splitter = sppasSimpleSplitter("cmn")
        result = splitter.split("干脆就把那部蒙人.的闲法给废了拉倒")
        expected = u("干 脆 就 把 那 部 蒙 人 . 的 闲 法 给 废 了 拉 倒")
        self.assertEqual(expected.split(), result)

        splitter = sppasSimpleSplitter("fra")
        result = splitter.split("abc~ /sa~mpa/")
        expected = u("abc~ /sa~mpa/")
        self.assertEqual(expected.split(), result)

        result = splitter.split("abc. abc")
        expected = u("abc. abc")
        self.assertEqual(expected.split(), result)

        result = splitter.split_characters("l'abat-jour")
        expected = u(" l ' abat - jour ")
        self.assertEqual(expected, result)

# ---------------------------------------------------------------------------


class TestNormalizer(unittest.TestCase):

    def setUp(self):
        dir = os.path.join(paths.resources, "vocab")
        vocab_file = os.path.join(dir, "fra.vocab")
        punct_file = os.path.join(dir, "Punctuations.txt")
        wds = sppasVocabulary(vocab_file)
        puncts = sppasVocabulary(punct_file)
        self.tok = TextNormalizer(wds, "fra")
        self.tok.set_punct(puncts)

    # -----------------------------------------------------------------------

    def test_replace(self):
        """... Examine tokens and performs some replacements."""

        repl = sppasDictRepl(os.path.join(paths.resources, "repl", "fra.repl"), nodump=True)
        self.tok.set_repl(repl)
        s = self.tok.replace([u("un"), u("taux"), u("de"), u("croissance"), u("de"), u("0,5"), u("%")])
        self.assertEqual(s, [u("un"), u("taux"), u("de"), u("croissance"), u("de"), u("0"), u("virgule"), u("5"),
                              u("pourcents")])

        text = [u("² % °c  km/h  etc   €  ¥ $ ")]

        repl = sppasDictRepl(os.path.join(paths.resources, "repl", "eng.repl"), nodump=True)
        self.tok.set_repl(repl)
        s = self.tok.replace(text)
        self.assertEqual(u("square percent degrees_Celsius km/h etc euros yens dollars"),
                          " ".join(s))

        repl = sppasDictRepl(os.path.join(paths.resources, "repl", "fra.repl"), nodump=True)
        self.tok.set_repl(repl)
        s = self.tok.replace(text)
        self.assertEqual(u("carrés pourcents degrés_celcius kilomètres_heure etcetera euros yens dollars"),
                          " ".join(s))

        spa = os.path.join(paths.resources, "repl", "spa.repl")
        if os.path.exists(spa):
            repl = sppasDictRepl(spa, nodump=True)
            self.tok.set_repl(repl)
            s = self.tok.replace(text)
            self.assertEqual(u("quadrados por_ciento grados_Celsius km/h etc euros yens dollars"),
                              " ".join(s))

        ita = os.path.join(paths.resources, "repl", "ita.repl")
        if os.path.exists(ita):
            repl = sppasDictRepl(ita, nodump=True)
            self.tok.set_repl(repl)
            s = self.tok.replace(text)
            self.assertEqual(u("quadrato percento gradi_Celsius km/h etc euros yens dollars"),
                              " ".join(s))

        cmn = os.path.join(paths.resources, "repl", "cmn.repl")
        if os.path.exists(cmn):
            repl = sppasDictRepl(ita, nodump=True)
            self.tok.set_repl(repl)
            s = self.tok.replace(text)
            self.assertEqual(u("的平方 个百分比 摄氏度 公里每小时 etc € ¥ $"),
                               " ".join(s))

    # -----------------------------------------------------------------------

    def test_tokenize(self):
        """... Tokenize is the text segmentation, i.e. to segment into tokens."""

        self.tok.set_lang("fra")
        splitfra = self.tok.tokenize(u("l'assiette").split())
        self.assertEqual(splitfra, u("l' assiette").split())

        splitfra = self.tok.tokenize(u("l'abat-jour").split())
        self.assertEqual(splitfra, u("l' abat-jour").split())

        splitfra = self.tok.tokenize(u("un paris-brest").split())
        self.assertEqual(splitfra, u("un paris-brest").split())

        splitfra = self.tok.tokenize(u("le paris-roubaix").split())
        self.assertEqual(splitfra, u("le paris-roubaix").split())

        splitfra = self.tok.tokenize(u("un trajet paris-marseille").split())
        self.assertEqual(splitfra, u("un trajet paris - marseille").split())

        self.assertEqual(u("ah a/b euh").split(), self.tok.normalize(u("ah a/b euh")))

        # sampa
        self.assertEqual([u('/l-e-f-o~-n/')], self.tok.normalize(u("/l-e-f-o~-n/")))

        # not sampa...
        self.assertEqual(u('le mot').split(), self.tok.normalize(u("/le mot/")))

        self.assertEqual(u("here are proper names $john_doe$ and $d-j._doe$").split(),
                         self.tok.normalize(u("here are proper names $john_doe$ and $d-j._doe$")))

    # -----------------------------------------------------------------------

    def test_num2letter(self):
        """... Integration of num2letter into the TextNormalizer."""

        num = sppasDictRepl(os.path.join(paths.resources, "num", "fra_num.repl"), nodump=True)
        repl = sppasDictRepl(os.path.join(paths.resources, "repl", "fra.repl"), nodump=True)
        self.tok.set_repl(repl)
        self.tok.set_num(num)
        self.tok.set_lang("fra")

        self.assertEqual([u("cent_vingt_trois")], self.tok.normalize(u("123")))

        self.assertEqual([u("un")], self.tok.normalize(u("1")))
        self.assertEqual([u("vingt_quatre")], self.tok.normalize(u("24")))
        self.assertEqual(u("un virgule vingt_quatre").split(), self.tok.normalize(u("1,24")))

        # self.tok.set_lang("deu")
        # with self.assertRaises(ValueError):
        #     self.tok.normalize(u("123"))

    # -----------------------------------------------------------------------

    def test_remove_punct(self):
        """... Remove data of an utterance if included in a dictionary."""

        self.tok.set_lang("fra")
        self.assertEqual(u("un deux").split(), self.tok.normalize(u("/un, deux!!!")))
        self.assertEqual(u("n assiette").split(), self.tok.normalize(u("n ' assiette")))
        # self.assertEqual(u("l' assiette").split(), self.tok.normalize(u("l' assiette")))

    # -----------------------------------------------------------------------

    def test_stick(self):
        """... Token Segmenter on compound words."""

        t = sppasTokenSegmenter(self.tok.vocab)
        s = t.bind([u("123")])
        self.assertEqual(s, [u("123")])
        s = t.bind([u("au fur et à mesure")])
        self.assertEqual(s, [u("au_fur_et_à_mesure")])
        s = t.bind([u("rock'n roll")])   # not in lexicon
        self.assertEqual(s, [u("rock'n")])

        s = t.bind([u("l' assiette")])
        self.assertEqual(s, [u("l'")])
        s = t.bind([u("L' assiette")])
        self.assertEqual(s, [u("L'")])

    # -----------------------------------------------------------------------

    def test_sampa(self):
        """... X-SAMPA included into the ortho transcription."""

        repl = sppasDictRepl(os.path.join(paths.resources, "repl", "fra.repl"), nodump=True)
        self.tok.set_repl(repl)

        self.assertEqual([u("/lemot/")], self.tok.normalize(u("[le mot,/lemot/]"), []))
        self.assertEqual([u("le_mot")], self.tok.normalize(u("[le mot,/lemot/]"), ["std"]))
        self.assertEqual([u("/lemot/")], self.tok.normalize(u("[le mot,/lemot/]")))

        # minus is accepted in sampa transcription (it is the phonemes separator)
        self.assertEqual([u("/l-e-f-o~-n/")], self.tok.normalize(u(" /l-e-f-o~-n/ ")))
        self.assertEqual([u("/le~/")], self.tok.normalize(u(" /le~/ ")))

        # whitespace is not accepted in sampa transcription
        self.assertEqual(u("le mot").split(), self.tok.normalize(u(" /le mot/ ")))

    # -----------------------------------------------------------------------

    def test_code_switching(self):
        """... [TO DO] support of language switching."""

        dictdir = os.path.join(paths.resources, "vocab")
        vocabfra = os.path.join(dictdir, "fra.vocab")
        vocabcmn = os.path.join(dictdir, "eng.vocab")

        #self.tok.set_vocab(wds)
        #splitswitch = self.tok.tokenize(u'et il m\'a dit : "《干脆就把那部蒙人的闲法给废了拉倒！》RT @laoshipukong : 27日"')
        #self.assertEqual(splitswitch, u"et il m' a dit 干脆 就 把 那 部 蒙 人 的 闲 法 给 废 了 拉倒 rt @ laoshipukong 二十七 日")

    # -----------------------------------------------------------------------
    #
    # def test_acronyms(self):
    #
    #     self.tok.set_lang("fra")
    #     # todo

# ---------------------------------------------------------------------------


class TestTierNormalizer(unittest.TestCase):
    """Test TierNormalizer class. Introduced in SPPAS 4.11."""

    def test_parse_cut_label(self):
        """Test label cut. """
        tn = TierNormalizer()
        label = sppasLabel(sppasTag(3, tag_type="int"))
        self.assertEqual(0, len(tn.parse_cut_label(label)))
        label = sppasLabel(sppasTag("un texte normal"))
        self.assertEqual(0, len(tn.parse_cut_label(label)))
        label = sppasLabel(sppasTag("un texte <cut> normal"))
        self.assertEqual(0, len(tn.parse_cut_label(label)))
        label = sppasLabel(sppasTag("un texte <tag/> normal"))
        self.assertEqual(0, len(tn.parse_cut_label(label)))

        # Each cut adds an entry for the event it delimits. Its name is the
        # value of the "event" attribute, or "dummy" if not given.

        # cut is surrounded by whitespace
        label = sppasLabel(sppasTag('un texte <cut units="sec" from="23" to="54"/> à couper'))
        cuts = tn.parse_cut_label(label)
        self.assertEqual(3, len(cuts))
        self.assertEqual("un texte", cuts[0][0].get_best().get_typed_content())
        self.assertEqual("dummy", cuts[1][0].get_best().get_typed_content())
        self.assertEqual("à couper", cuts[2][0].get_best().get_typed_content())

        # cut is inside a word (no whitespace)
        label = sppasLabel(sppasTag('un tex<cut unit="sec" from="23" to="54"/>te'))
        cuts = tn.parse_cut_label(label)
        self.assertEqual(3, len(cuts))
        self.assertEqual("un tex", cuts[0][0].get_best().get_typed_content())
        self.assertEqual(None, cuts[0][1])
        self.assertEqual(23., cuts[0][2])
        self.assertEqual("dummy", cuts[1][0].get_best().get_typed_content())
        self.assertEqual(23., cuts[1][1])
        self.assertEqual(54., cuts[1][2])
        self.assertEqual("te", cuts[2][0].get_best().get_typed_content())
        self.assertEqual(54., cuts[2][1])
        self.assertEqual(None, cuts[2][2])

        # several cuts
        label = sppasLabel(sppasTag('un texte <cut unit="sec" from="23" to="54"/> à '
                                    'cou<cut unit="sec" from="62" to="64"/>per'))
        cuts = tn.parse_cut_label(label)
        self.assertEqual(5, len(cuts))
        self.assertEqual("un texte", cuts[0][0].get_best().get_typed_content())
        self.assertEqual(None, cuts[0][1])
        self.assertEqual(23., cuts[0][2])
        self.assertEqual("dummy", cuts[1][0].get_best().get_typed_content())
        self.assertEqual(23., cuts[1][1])
        self.assertEqual(54., cuts[1][2])
        self.assertEqual("à cou", cuts[2][0].get_best().get_typed_content())
        self.assertEqual(54., cuts[2][1])
        self.assertEqual(62., cuts[2][2])
        self.assertEqual("dummy", cuts[3][0].get_best().get_typed_content())
        self.assertEqual(62., cuts[3][1])
        self.assertEqual(64., cuts[3][2])
        self.assertEqual("per", cuts[4][0].get_best().get_typed_content())
        self.assertEqual(64., cuts[4][1])
        self.assertEqual(None, cuts[4][2])

    def test_transcription_alternatives(self):
        """Test the alternatives of the transcription: the "<a,b>" convention."""
        vocab = sppasVocabulary(os.path.join(paths.resources, "vocab", "fra.vocab"))
        tier = sppasTier("Transcription")
        tier.create_annotation(
            sppasLocation(sppasInterval(sppasPoint(0.), sppasPoint(1.))),
            sppasLabel(sppasTag("J'ai <jamais,panais> réussi")))
        tier.create_annotation(
            sppasLocation(sppasInterval(sppasPoint(1.), sppasPoint(2.))),
            sppasLabel(sppasTag("j'ai <il chante,ils chantent> bien")))
        tier.create_annotation(
            sppasLocation(sppasInterval(sppasPoint(2.), sppasPoint(3.))),
            sppasLabel(sppasTag("J'ai jamais réussi")))

        tokens_tier = TierNormalizer(vocab).normalize_tier(
            tier, ["replace", "tokenize", "numbers", "lower", "punct"])
        self.assertEqual(3, len(tokens_tier))

        # A label alternative is a label with several tags. The number of
        # labels is the same, with or without alternatives.
        self.assertEqual(4, len(tokens_tier[0].get_labels()))
        self.assertEqual(4, len(tokens_tier[1].get_labels()))
        self.assertEqual(4, len(tokens_tier[2].get_labels()))

        # Each token is identified by the key of its label
        for annotation in tokens_tier:
            self.assertEqual(["w_1", "w_2", "w_3", "w_4"],
                             [label.get_key() for label in annotation.get_labels()])

        labels = tokens_tier[0].get_labels()
        self.assertEqual(1, len(labels[0]))
        self.assertEqual(2, len(labels[2]))
        self.assertEqual("jamais", labels[2].get_best().get_content())
        self.assertEqual(["jamais", "panais"],
                         [tag.get_content() for tag, score in labels[2]])
        self.assertEqual("j' ai {jamais|panais} réussi",
                         serialize_labels(labels, separator=" "))

        # The whitespace of a tag made of several tokens is replaced
        labels = tokens_tier[1].get_labels()
        self.assertEqual(2, len(labels[2]))
        self.assertEqual("j' ai {il_chante|ils_chantent} bien",
                         serialize_labels(labels, separator=" "))

    def test_cut_units(self):
        """Test label cut with different units."""
        label = sppasLabel(sppasTag('un texte <cut units="sec" from="23" to="54"/> à couper'))
        cuts = TierNormalizer().parse_cut_label(label)
        self.assertEqual(3, len(cuts))
        self.assertEqual("un texte", cuts[0][0].get_best().get_typed_content())
        self.assertEqual("dummy", cuts[1][0].get_best().get_typed_content())
        self.assertEqual("à couper", cuts[2][0].get_best().get_typed_content())

# ---------------------------------------------------------------------------


class TestParseCut(unittest.TestCase):

    def test_parser(self):
        testParser = ParseCut()

        testParser.feed('<cut unit="sec" from="3" to="7" comment="toto"/>')
        self.assertEqual(3., testParser.cut_from)
        self.assertEqual(7., testParser.cut_to)

        testParser.feed('<cut unit="sec" from="3" to="7"/>')
        self.assertEqual(3., testParser.cut_from)
        self.assertEqual(7., testParser.cut_to)

        testParser.feed('<cut unit="ms" from="32" to="701"/>')
        self.assertEqual(0.032, testParser.cut_from)
        self.assertEqual(0.701, testParser.cut_to)

        testParser.feed('<cut from="0.032" to="0.701"/>')
        self.assertEqual(0.032, testParser.cut_from)
        self.assertEqual(0.701, testParser.cut_to)

        testParser.feed('<cut from="00:0.032" to="00:0.701"/>')
        self.assertEqual(0.032, testParser.cut_from)
        self.assertEqual(0.701, testParser.cut_to)

        testParser.feed('<cut from="01:0.032" to="01:0.701"/>')
        self.assertEqual(60.032, testParser.cut_from)
        self.assertEqual(60.701, testParser.cut_to)

        testParser.feed('<cut from="1:0.032" to="1:0.701"/>')
        self.assertEqual(60.032, testParser.cut_from)
        self.assertEqual(60.701, testParser.cut_to)

        testParser.feed('<cut from="00:01:0.032" to="00:01:0.701"/>')
        self.assertEqual(60.032, testParser.cut_from)
        self.assertEqual(60.701, testParser.cut_to)

        testParser.feed('<cut from="01:01:0.032" to="01:01:0.701"/>')
        self.assertEqual(3660.032, testParser.cut_from)
        self.assertEqual(3660.701, testParser.cut_to)

# ---------------------------------------------------------------------------


class TestTextNorm(unittest.TestCase):
    """Test the SPPAS integration of the TextNormalizer."""

    def test_samples(self):
        """... Compare the current result is the same as the existing one."""
        # Test the automatic annotation with its default parameters only.

        for samples_folder in os.listdir(paths.samples):
            if samples_folder.startswith("samples-") is False:
                continue

            # the place where are the existing results samples.
            expected_result_dir = os.path.join(paths.samples,
                                               "annotation-results",
                                               samples_folder)
            if os.path.exists(expected_result_dir) is False:
                continue

            # Create a TextNormalizer for the given set of samples
            lang = samples_folder[-3:]
            vocab = os.path.join(paths.resources, "vocab", lang+".vocab")
            tn = sppasTextNorm()
            tn.load_resources(vocab, lang=lang)
            tn.set_faked(True)
            tn.set_std(True)
            tn.set_custom(True)

            # Apply TextNormalization on each sample
            for filename in os.listdir(os.path.join(paths.samples, samples_folder)):
                if filename.endswith(".TextGrid") is False:
                    continue

                # Get the expected result
                expected_result_filename = os.path.join(expected_result_dir,
                                                        filename[:-9] + "-token.xra")
                if os.path.exists(expected_result_filename) is False:
                    continue

                try:
                    parser = sppasTrsRW(expected_result_filename)
                    expected_result = parser.read()
                except AioEncodingError:
                    continue

                # Estimate the result and check if it's like expected.
                input_file = os.path.join(paths.samples, samples_folder, filename)
                result = tn.run([input_file])

                expected_tier_tokens = expected_result.find('Tokens')
                if expected_tier_tokens is not None:
                    self.compare_tiers(expected_tier_tokens, result.find('Tokens'))

                expected_tier_tokens = expected_result.find('TokensStd')
                if expected_tier_tokens is not None:
                    self.compare_tiers(expected_tier_tokens, result.find('TokensStd'))

                expected_tier_tokens = expected_result.find('TokensCustom')
                if expected_tier_tokens is not None:
                    self.compare_tiers(expected_tier_tokens, result.find('TokensCustom'))

    # -----------------------------------------------------------------------

    def compare_tiers(self, expected, result):
        self.assertEqual(len(expected), len(result))
        # compare annotations
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

# ---------------------------------------------------------------------------


class TestTextNormOptions(unittest.TestCase):
    """Test the options of the TextNorm automatic annotation."""

    def setUp(self):
        if os.path.exists(TEMP) is False:
            os.mkdir(TEMP)

    def tearDown(self):
        shutil.rmtree(TEMP)

    # -----------------------------------------------------------------------

    @staticmethod
    def create_input_file():
        """Write a file with a 'transcription' and a 'translation' tiers.

        :return: (str) Name of the created file.

        """
        trs = sppasTranscription()
        tier_transcription = trs.create_tier(name="transcription")
        tier_transcription.append(sppasAnnotation(
            sppasLocation(sppasInterval(sppasPoint(1.), sppasPoint(3.))),
            sppasLabel(sppasTag("bonjour"))))
        tier_translation = trs.create_tier(name="translation")
        tier_translation.append(sppasAnnotation(
            sppasLocation(sppasInterval(sppasPoint(1.), sppasPoint(3.))),
            sppasLabel(sppasTag("hello"))))

        input_file = os.path.join(TEMP, "sample.xra")
        parser = sppasTrsRW(input_file)
        parser.write(trs)
        return input_file

    # -----------------------------------------------------------------------

    def test_set_tiername(self):
        """Test of fixing the tiername option."""

        tn = sppasTextNorm()
        tn.set_tiername("toto")
        self.assertEqual(tn._options['tiername'], "toto")

        tn.fix_options([sppasOption("tiername", "str", "translation")])
        self.assertEqual(tn._options['tiername'], "translation")

    # -----------------------------------------------------------------------

    def test_get_inputs_default(self):
        """Test of finding the input tier without the tiername option."""

        input_file = TestTextNormOptions.create_input_file()

        tn = sppasTextNorm()
        tier = tn.get_inputs([input_file])
        self.assertEqual(tier.get_name(), "transcription")

    # -----------------------------------------------------------------------

    def test_get_inputs_tiername(self):
        """Test of finding the input tier with the tiername option."""

        input_file = TestTextNormOptions.create_input_file()

        tn = sppasTextNorm()
        tn.set_tiername("translation")
        tier = tn.get_inputs([input_file])
        self.assertEqual(tier.get_name(), "translation")
