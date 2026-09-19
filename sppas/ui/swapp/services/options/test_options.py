# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.services.options.test_options.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of what an app lets one set.

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

    TE1 to TE21 of the dossier "What an app lets one set". Sixteen of them
    need nothing installed, four need a view, one needs the provision of
    files. The bounds of an option are the extension E1 of the annex.

"""

from __future__ import annotations
import unittest

from sppas.src.structs.baseoption import sppasOption

from .options_acceptance import ValueAcceptance
from .options_set import OptionSet
from .options_file import FileForOption
from .options_record import OptionsRecord
from .options_view import OptionsView

# ---------------------------------------------------------------------------


def an_option(key: str, kind: str, value, text: str = "", description: str = "",
              bounds: tuple | None = None) -> sppasOption:
    """Give an option as an app declares one.

    :param bounds: (tuple|None) The low and the high bound -- extension E1.

    """
    option = sppasOption(key, kind, value)
    option.set_text(text if len(text) > 0 else key)
    option.set_description(description)
    if bounds is not None:
        option.set_bounds(bounds[0], bounds[1])
    return option


def a_set() -> OptionSet:
    """Give a set of four options, one of each kind which is tested."""
    return OptionSet([
        an_option("keep", "bool", "True", "Keep what cannot be written",
                  "What the destination cannot hold is written as comments."),
        an_option("window", "int", "5", "Window", "In number of frames.",
                  bounds=(1, 10)),
        an_option("threshold", "float", "0.5", "Threshold", "", bounds=(0., 1.)),
        an_option("name", "str", "aaa", "Name of the tier", "")])


def text_of(view) -> str:
    """Give what a view built, as it will be sent.

    The one line to change the day a view gives back its tree otherwise.

    """
    return view.serialize()

# ---------------------------------------------------------------------------


class TestValueAcceptance(unittest.TestCase):
    """TE1 to TE5. Nothing is installed: a kind, bounds, and a value."""

    def setUp(self):
        self.acceptance = ValueAcceptance()

    # -----------------------------------------------------------------------

    def test_te1_a_value_suits_the_kind_or_it_does_not(self):
        """TE1. Accepted when it suits the kind of its option, refused when it
        does not. [201]

        """
        whole = an_option("window", "int", "5")
        self.assertTrue(self.acceptance.accepts(whole, "7"))
        self.assertFalse(self.acceptance.accepts(whole, "seven"))
        self.assertFalse(self.acceptance.accepts(whole, "7.5"))

        yes_or_no = an_option("keep", "bool", "True")
        self.assertTrue(self.acceptance.accepts(yes_or_no, "False"))
        self.assertFalse(self.acceptance.accepts(yes_or_no, "maybe"))

        decimal = an_option("threshold", "float", "0.5")
        self.assertTrue(self.acceptance.accepts(decimal, "0.75"))
        self.assertFalse(self.acceptance.accepts(decimal, "a lot"))

        text = an_option("name", "str", "aaa")
        self.assertTrue(self.acceptance.accepts(text, "anything at all"))

    # -----------------------------------------------------------------------

    def test_te2_the_bounds_of_an_option(self):
        """TE2. Inside is accepted, the bound itself passes, one step beyond is
        refused. The bounds are the extension E1. [201]

        """
        option = an_option("window", "int", "5", bounds=(1, 10))
        for value in ("1", "5", "10"):
            self.assertTrue(self.acceptance.accepts(option, value))
        for value in ("0", "11", "-3"):
            self.assertFalse(self.acceptance.accepts(option, value))

        decimal = an_option("threshold", "float", "0.5", bounds=(0., 1.))
        self.assertTrue(self.acceptance.accepts(decimal, "0."))
        self.assertTrue(self.acceptance.accepts(decimal, "1."))
        self.assertFalse(self.acceptance.accepts(decimal, "1.0001"))

    # -----------------------------------------------------------------------

    def test_te3_an_option_without_bounds(self):
        """TE3. Every value of its kind is accepted. [201]"""
        option = an_option("window", "int", "5")
        for value in ("0", "-3000", "999999"):
            self.assertTrue(self.acceptance.accepts(option, value))

    # -----------------------------------------------------------------------

    def test_te4_what_is_expected_is_said(self):
        """TE4. For an option, whether or not anything was refused. [202]"""
        option = an_option("window", "int", "5", bounds=(1, 10))

        expected = self.acceptance.what_is_expected(option)
        self.assertTrue(len(expected) > 0)
        self.assertEqual(expected, self.acceptance.what_is_expected(option))

        self.assertTrue(len(self.acceptance.what_is_expected(
            an_option("name", "str", "aaa"))) > 0)

    # -----------------------------------------------------------------------

    def test_te5_nothing_is_refused_on_what_a_value_means(self):
        """TE5. Two values which contradict each other are both accepted: what
        they mean belongs to the app. The day this test has to be changed, this
        domain has started to judge. [201]

        """
        low = an_option("minimum", "int", "0", bounds=(0, 100))
        high = an_option("maximum", "int", "100", bounds=(0, 100))

        self.assertTrue(self.acceptance.accepts(low, "90"))
        self.assertTrue(self.acceptance.accepts(high, "10"))

# ---------------------------------------------------------------------------


class TestOptionSet(unittest.TestCase):
    """TE6 to TE16. The set, and nothing installed."""

    def setUp(self):
        self.options = a_set()

    # -----------------------------------------------------------------------

    def test_te6_a_set_rebuilt_from_what_a_page_transmitted(self):
        """TE6. The same options, the same values, the same values on
        arrival. RO1

        """
        self.options.set_value("window", "8")
        rebuilt = OptionSet.rebuild(self.options.serialize())

        self.assertEqual([o.get_key() for o in self.options.for_app()],
                         [o.get_key() for o in rebuilt.for_app()])
        self.assertEqual("8", rebuilt.value_of("window"))
        self.assertEqual("5", rebuilt.value_on_arrival_of("window"))

    # -----------------------------------------------------------------------

    def test_te7_a_record_parsed_twice(self):
        """TE7. It gives the same set. Without this, reloading a page loses
        what was given. RO1

        """
        record = OptionsRecord()
        record.set = self.options
        record.set.set_value("name", "bbb")

        transported = record.serialize()
        once = OptionsRecord.parse(transported)
        twice = OptionsRecord.parse(transported)

        self.assertEqual("bbb", once.set.value_of("name"))
        self.assertEqual(once.set.serialize(), twice.set.serialize())

    # -----------------------------------------------------------------------

    def test_te8_an_empty_transport(self):
        """TE8. It gives an empty set, and nothing is raised. RO1"""
        empty = OptionsRecord.parse(dict())
        self.assertEqual(list(), empty.set.for_app())
        self.assertEqual(list(), empty.set.refusals())

    # -----------------------------------------------------------------------

    def test_te9_setting_a_value_leaves_the_value_on_arrival(self):
        """TE9. The option holds the new value; what it arrived with does not
        move. [104]

        """
        self.assertEqual("5", self.options.value_on_arrival_of("window"))

        self.options.set_value("window", "9")

        self.assertEqual("9", self.options.value_of("window"))
        self.assertEqual("5", self.options.value_on_arrival_of("window"))

    # -----------------------------------------------------------------------

    def test_te10_setting_a_value_changes_nothing_else(self):
        """TE10. Not the kind, not the label, not the description. [101]"""
        before = [(o.get_key(), o.get_type(), o.get_text(), o.get_description())
                  for o in self.options.for_app()]

        self.options.set_value("window", "9")
        self.options.set_value("name", "bbb")

        after = [(o.get_key(), o.get_type(), o.get_text(), o.get_description())
                 for o in self.options.for_app()]
        self.assertEqual(before, after)

    # -----------------------------------------------------------------------

    def test_te11_putting_one_option_back(self):
        """TE11. That option holds what it arrived with; the others are left as
        they were. [301]

        """
        self.options.set_value("window", "9")
        self.options.set_value("name", "bbb")

        self.options.put_back("window")

        self.assertEqual("5", self.options.value_of("window"))
        self.assertEqual("bbb", self.options.value_of("name"))

    # -----------------------------------------------------------------------

    def test_te12_putting_every_option_back(self):
        """TE12. Every option holds what it arrived with. [302]"""
        for key, value in (("window", "9"), ("name", "bbb"), ("keep", "False")):
            self.options.set_value(key, value)

        self.options.put_all_back()

        self.assertEqual("5", self.options.value_of("window"))
        self.assertEqual("aaa", self.options.value_of("name"))
        self.assertEqual("True", self.options.value_of("keep"))

    # -----------------------------------------------------------------------

    def test_te13_putting_an_option_back_drops_its_refusal(self):
        """TE13. A reproach made to a value which is nowhere any more does not
        stand. T04

        """
        self.options.validate({"window": "99"})
        self.assertEqual(1, len(self.options.refusals()))

        self.options.put_back("window")

        self.assertEqual(list(), self.options.refusals())

    # -----------------------------------------------------------------------

    def test_te14_one_bad_value_out_of_twenty(self):
        """TE14. The nineteen others are taken in, and there is one refusal. A
        set is not accepted or refused as a whole. T03

        """
        options = OptionSet([an_option("o%d" % i, "int", "0", bounds=(0, 10))
                             for i in range(20)])
        given = {"o%d" % i: str(i % 10) for i in range(20)}
        given["o7"] = "99"

        options.validate(given)

        refusals = options.refusals()
        self.assertEqual(1, len(refusals))
        self.assertEqual("o7", refusals[0].option)
        for i in range(20):
            if i != 7:
                self.assertEqual(str(i % 10), options.value_of("o%d" % i))

    # -----------------------------------------------------------------------

    def test_te15_a_refused_value_erases_nothing(self):
        """TE15. The option holds what it held before the value was given. T03"""
        self.options.set_value("window", "8")

        self.options.validate({"window": "99"})

        self.assertEqual("8", self.options.value_of("window"))
        self.assertEqual(1, len(self.options.refusals()))

    # -----------------------------------------------------------------------

    def test_te16_what_is_given_back_for_an_app(self):
        """TE16. Every option with the value it holds; no refusal, and no value
        on arrival. [601]

        """
        self.options.set_value("window", "8")
        self.options.validate({"threshold": "not a number"})

        given = self.options.for_app()

        self.assertEqual(4, len(given))
        values = {o.get_key(): o.get_untypedvalue() for o in given}
        self.assertEqual("8", values["window"])
        self.assertEqual("0.5", values["threshold"])
        for option in given:
            self.assertFalse(hasattr(option, "refusal"))
            self.assertFalse(hasattr(option, "value_on_arrival"))

# ---------------------------------------------------------------------------


class TestOptionsView(unittest.TestCase):
    """TE17 to TE20. With a view, and nothing else."""

    def setUp(self):
        self.options = a_set()
        self.record = OptionsRecord()
        self.record.set = self.options
        self.view = OptionsView()

    # -----------------------------------------------------------------------

    def test_te17_one_line_per_option(self):
        """TE17. Carrying the label of that option and the value it holds.
        [021], [031]

        """
        self.view.populate_tree_content(self.record)
        shown = text_of(self.view)

        for option in self.options.for_app():
            self.assertIn(option.get_text(), shown)
            self.assertIn(option.get_untypedvalue(), shown)

    # -----------------------------------------------------------------------

    def test_te18_the_description_is_shown_when_it_is_asked_for(self):
        """TE18. And nowhere otherwise. [022]"""
        told = "What the destination cannot hold is written as comments."

        self.view.populate_tree_content(self.record)
        self.assertNotIn(told, text_of(self.view))

        self.record.to_be_shown = "keep"
        other = OptionsView()
        other.populate_tree_content(self.record)
        self.assertIn(told, text_of(other))

    # -----------------------------------------------------------------------

    def test_te19_no_text_the_options_did_not_carry(self):
        """TE19. A view writes none of its own. [023]"""
        options = OptionSet([an_option("k", "str", "v", "Label of the option",
                                       "Description of the option")])
        record = OptionsRecord()
        record.set = options
        record.to_be_shown = "k"

        self.view.populate_tree_content(record)
        shown = text_of(self.view)

        self.assertIn("Label of the option", shown)
        self.assertIn("Description of the option", shown)
        self.assertNotIn("option k", shown.lower())

    # -----------------------------------------------------------------------

    def test_te20_a_refusal_stands_beside_its_option(self):
        """TE20. And beside no other. [202]"""
        self.options.validate({"window": "99"})

        self.view.populate_tree_content(self.record)
        shown = text_of(self.view)

        expected = ValueAcceptance().what_is_expected(
            [o for o in self.options.for_app() if o.get_key() == "window"][0])
        self.assertIn(expected, shown)
        self.assertEqual(1, shown.count(expected))

# ---------------------------------------------------------------------------


class TestFileForOption(unittest.TestCase):
    """TE21. The only test which needs the provision of files."""

    def setUp(self):
        self.options = a_set()
        self.for_option = FileForOption()

    # -----------------------------------------------------------------------

    def test_te21_a_file_is_asked_for_one_option_and_given_to_that_one(self):
        """TE21. What is checked on this side is the tie: which option a file
        was asked for, and which option gets it. [401]

        """
        asked = self.for_option.ask_for(
            an_option("alphabet", "filename", ""))
        self.assertEqual("alphabet", asked.option)

        options = OptionSet([an_option("alphabet", "filename", ""),
                             an_option("other", "filename", "")])
        self.for_option.take_in(options, "alphabet", "sampa-to-ipa.csv")

        self.assertEqual("sampa-to-ipa.csv", options.value_of("alphabet"))
        self.assertEqual("", options.value_of("other"))

# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
