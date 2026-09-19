# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_deposit.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the place for files which have to travel.

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

    TE1 to TE22 of the dossier "A place for files which have to travel".
    Nine need nothing at all, ten need a disk, three need two threads.

"""

from __future__ import annotations
import unittest
import os
import shutil
import tempfile
import threading
import time

from sppas.ui.swapp.services.deposit.deposit_settings import sppasDepositSettings
from sppas.ui.swapp.services.deposit.deposit_acceptance import sppasSpaceAcceptance
from sppas.ui.swapp.services.deposit.deposit_place import sppasPlace
from sppas.ui.swapp.services.deposit.deposit_place import sppasSpaceFolder
from sppas.ui.swapp.services.deposit.deposit_address import sppasFileAddress
from sppas.ui.swapp.services.deposit.deposit_space import sppasDepositSpace

# ---------------------------------------------------------------------------

MINUTE = 60.

# ---------------------------------------------------------------------------


class TestSpaceAcceptance(unittest.TestCase):
    """TE1 to TE4. It reads no disk: nothing is installed here."""

    def setUp(self):
        self.settings = sppasDepositSettings()
        self.acceptance = sppasSpaceAcceptance(self.settings)

    # -----------------------------------------------------------------------

    def test_te1_the_values_are_read_from_the_settings(self):
        """TE1. The four values are said as the one file which holds them says
        them. Change that file and the answers change: no value of this domain
        is written anywhere else. C9

        """
        size, volume, places = self.acceptance.what_is_accepted()
        self.assertEqual(self.settings.file_size, size)
        self.assertEqual(self.settings.place_volume, volume)
        self.assertEqual(self.settings.places, places)

        other = sppasDepositSettings()
        other.file_size = self.settings.file_size // 2
        self.assertEqual(other.file_size,
                         sppasSpaceAcceptance(other).what_is_accepted()[0])

    # -----------------------------------------------------------------------

    def test_te2_a_size(self):
        """TE2. Beyond what one file may be is refused; one under it passes. C4"""
        bound = self.settings.file_size
        self.assertTrue(self.acceptance.accepts_size(bound - 1))
        self.assertTrue(self.acceptance.accepts_size(bound))
        self.assertFalse(self.acceptance.accepts_size(bound + 1))
        self.assertTrue(self.acceptance.accepts_size(0))

    # -----------------------------------------------------------------------

    def test_te3_a_volume(self):
        """TE3. Beyond what one place may hold is refused; one under passes. C5"""
        bound = self.settings.place_volume
        self.assertTrue(self.acceptance.accepts_volume(bound - 1))
        self.assertTrue(self.acceptance.accepts_volume(bound))
        self.assertFalse(self.acceptance.accepts_volume(bound + 1))

    # -----------------------------------------------------------------------

    def test_te4_a_number_of_places(self):
        """TE4. At and beyond the number of places is refused; one under
        passes. The number is counted after the forgetting, and this class is
        not what counts it. C6

        """
        bound = self.settings.places
        self.assertTrue(self.acceptance.accepts_one_more_place(bound - 1))
        self.assertFalse(self.acceptance.accepts_one_more_place(bound))
        self.assertFalse(self.acceptance.accepts_one_more_place(bound + 1))

# ---------------------------------------------------------------------------


class TestPlace(unittest.TestCase):
    """TE5 and TE6. No place is ever made here, and no clock is faked."""

    def setUp(self):
        self.settings = sppasDepositSettings()

    # -----------------------------------------------------------------------

    def test_te5_the_moment_is_read_from_the_name(self):
        """TE5. A place of any age is a name written by the test: the moment is
        carried by the name and is read from nothing else. The minute on either
        side of the bound is where the two are separated. C1

        """
        duration = self.settings.duration

        young = sppasPlace(sppasPlace.a_name_for(time.time() - MINUTE), self.settings)
        self.assertTrue(young.is_of_this_hour())
        self.assertAlmostEqual(time.time() - MINUTE, young.moment(), delta=1.)

        edge = sppasPlace(sppasPlace.a_name_for(time.time() - duration + MINUTE), self.settings)
        self.assertTrue(edge.is_of_this_hour())

        old = sppasPlace(sppasPlace.a_name_for(time.time() - duration - MINUTE), self.settings)
        self.assertFalse(old.is_of_this_hour())

    # -----------------------------------------------------------------------

    def test_te6_a_name_this_domain_never_made(self):
        """TE6. It carries no moment, and it is not of this hour. C1"""
        for name in ("", "..", "a_folder", "1234", "/etc"):
            place = sppasPlace(name, self.settings)
            self.assertEqual(0., place.moment())
            self.assertFalse(place.is_of_this_hour())

    # -----------------------------------------------------------------------

    def test_te5bis_two_names_made_at_one_moment_differ(self):
        """TE5. What the name carries besides the moment is drawn: two places
        made in one second are two names.

        """
        moment = time.time()
        self.assertNotEqual(sppasPlace.a_name_for(moment), sppasPlace.a_name_for(moment))

# ---------------------------------------------------------------------------


class TestFileAddress(unittest.TestCase):
    """TE7 to TE9. It touches no disk: nothing is written here either."""

    def setUp(self):
        self.settings = sppasDepositSettings()
        self.address = sppasFileAddress(self.settings)
        self.place = sppasPlace.a_name_for(time.time())

    # -----------------------------------------------------------------------

    def test_te7_an_address_names_a_place_and_a_name(self):
        """TE7. What it is made of is what is read back from it. C10"""
        address = self.address.address_of(self.place, "a.wav")
        self.assertTrue(len(address) > 0)
        self.assertEqual((self.place, "a.wav"),
                         self.address.what_it_names(address))

    # -----------------------------------------------------------------------

    def test_te8_an_address_names_nothing_else_of_the_machine(self):
        """TE8. A name which climbs out of the space, a path of the machine, a
        place which is not one: each of them names nothing, and none of them is
        read as a file to give. C10

        """
        for place, name in (
                (self.place, "../../etc/passwd"),
                (self.place, "/etc/passwd"),
                (self.place, ".."),
                ("..", "a.wav"),
                ("/etc", "passwd"),
                ("", "a.wav"),
                (self.place, "")):
            self.assertEqual(("", ""), self.address.what_it_names(
                self.address.address_of(place, name)))

        for address in ("", "/etc/passwd", "..", self.place,
                        self.place + "/../../etc/passwd"):
            self.assertEqual(("", ""), self.address.what_it_names(address))

    # -----------------------------------------------------------------------

    def test_te9_what_authorises_outlives_a_place(self):
        """TE9. What authorises an address never runs out before the place
        does, whatever moment of the life of that place it was made at. It is
        the only thing of the front of the machine this domain answers for. C3

        """
        self.assertGreaterEqual(self.settings.signature_life,
                                self.settings.duration)

# ---------------------------------------------------------------------------


class TestSpaceFolder(unittest.TestCase):
    """TE10 to TE15. On a space of its own, deleted with the test."""

    def setUp(self):
        self.settings = sppasDepositSettings()
        self.settings.space = tempfile.mkdtemp(prefix="test_deposit_")
        self.folder = sppasSpaceFolder(self.settings)

    def tearDown(self):
        shutil.rmtree(self.settings.space, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te10_what_is_made_stands_in_the_listing(self):
        """TE10. A place stands in the listing of the space; a file stands in
        the listing of its place. The two tables, seen on a disk.

        """
        self.assertEqual(list(), self.folder.places())

        name = self.folder.make_a_place(sppasPlace.a_name_for(time.time()))
        self.assertTrue(len(name) > 0)
        self.assertEqual([name], self.folder.places())
        self.assertEqual(list(), self.folder.files(name))

        self.folder.make_a_file(name, "a.wav", b"12345")
        self.assertEqual(["a.wav"], self.folder.files(name))

    # -----------------------------------------------------------------------

    def test_te11_the_volume_of_a_place(self):
        """TE11. The sum of the sizes it holds; zero when it holds nothing,
        and zero when the place is not there. C5

        """
        self.assertEqual(0, self.folder.volume("no_such_place"))

        name = self.folder.make_a_place(sppasPlace.a_name_for(time.time()))
        self.assertEqual(0, self.folder.volume(name))

        self.folder.make_a_file(name, "a.wav", b"12345")
        self.assertEqual(5, self.folder.volume(name))
        self.folder.make_a_file(name, "b.wav", b"123")
        self.assertEqual(8, self.folder.volume(name))

    # -----------------------------------------------------------------------

    def test_te12_a_file_is_read_back_as_it_was_written(self):
        """TE12. Byte for byte, and under the name it was given. Nothing here
        judges what the bytes say. C7

        """
        name = self.folder.make_a_place(sppasPlace.a_name_for(time.time()))
        content = bytes(range(256)) * 8
        self.folder.make_a_file(name, "a.bin", content)

        self.assertEqual(content, self.folder.read(name, "a.bin"))
        self.assertEqual(b"", self.folder.read(name, "b.bin"))
        self.assertEqual(b"", self.folder.read("no_such_place", "a.bin"))

    # -----------------------------------------------------------------------

    def test_te13_deleting_a_place_deletes_what_it_held(self):
        """TE13. Not one file left, not one folder: the cascade of the logical
        level, seen on a disk. R1, T06

        """
        name = self.folder.make_a_place(sppasPlace.a_name_for(time.time()))
        self.folder.make_a_file(name, "a.wav", b"12345")
        self.folder.make_a_file(name, "b.wav", b"12345")

        self.folder.delete(name)

        self.assertEqual(list(), self.folder.places())
        self.assertEqual(list(), self.folder.files(name))
        self.assertFalse(os.path.exists(os.path.join(self.settings.space, name)))

        # Deleting what is not there does nothing wrong.
        self.folder.delete(name)
        self.folder.delete("no_such_place")

    # -----------------------------------------------------------------------

    def test_te14_a_file_whose_name_is_taken(self):
        """TE14. The making is refused by the name itself, and what stood there
        is what it was: not the bytes of the second, not a mixture. C8

        """
        name = self.folder.make_a_place(sppasPlace.a_name_for(time.time()))
        self.assertTrue(self.folder.make_a_file(name, "a.wav", b"first"))

        self.assertFalse(self.folder.make_a_file(name, "a.wav", b"second-and-longer"))

        self.assertEqual(b"first", self.folder.read(name, "a.wav"))
        self.assertEqual(["a.wav"], self.folder.files(name))

    # -----------------------------------------------------------------------

    def test_te15_a_place_whose_name_is_taken(self):
        """TE15. Nothing is made, and the place which was there is untouched. C8"""
        name = self.folder.make_a_place(sppasPlace.a_name_for(time.time()))
        self.folder.make_a_file(name, "a.wav", b"first")

        self.assertEqual("", self.folder.make_a_place(name))

        self.assertEqual([name], self.folder.places())
        self.assertEqual(["a.wav"], self.folder.files(name))
        self.assertEqual(b"first", self.folder.read(name, "a.wav"))

# ---------------------------------------------------------------------------


class TestDepositSpace(unittest.TestCase):
    """TE16 to TE19. The façade, which is an order of tasks."""

    def setUp(self):
        self.settings = sppasDepositSettings()
        self.settings.space = tempfile.mkdtemp(prefix="test_deposit_")
        self.space = sppasDepositSpace(self.settings)
        self.folder = sppasSpaceFolder(self.settings)

    def tearDown(self):
        shutil.rmtree(self.settings.space, ignore_errors=True)

    # -----------------------------------------------------------------------

    def an_old_place(self):
        """Make on the disk a place which has outlived its duration."""
        name = sppasPlace.a_name_for(time.time() - self.settings.duration - MINUTE)
        return self.folder.make_a_place(name)

    # -----------------------------------------------------------------------

    def test_te16_the_judging_comes_before_the_writing(self):
        """TE16. A file beyond the size is refused and nothing appears in the
        place. A file written and then removed would be the tasks reversed.

        """
        place, when = self.space.ask_for_a_place()
        self.assertTrue(len(place) > 0)
        self.assertEqual(0., when)

        too_big = b"x" * (self.settings.file_size + 1)
        given, reason = self.space.put(place, "a.wav", too_big)

        self.assertFalse(given)
        self.assertTrue(len(reason) > 0)
        self.assertEqual(list(), self.folder.files(place))
        self.assertEqual(0, self.folder.volume(place))

    # -----------------------------------------------------------------------

    def test_te17_a_place_which_is_not_of_this_hour(self):
        """TE17. It takes nothing, gives no address and serves nothing, whether
        or not it has been swept. The reading is what holds C1, not the
        sweeping.

        """
        place = self.an_old_place()

        given, reason = self.space.put(place, "a.wav", b"12345")
        self.assertFalse(given)
        self.assertTrue(len(reason) > 0)

        self.assertEqual("", self.space.address_of(place, "a.wav"))

    # -----------------------------------------------------------------------

    def test_te18_what_is_out_of_date_goes_without_being_asked(self):
        """TE18. A place of thirty-one minutes ago is gone from the listing
        after any operation at all, nobody having asked for it. C2, RO2

        """
        old = self.an_old_place()
        self.assertEqual([old], self.folder.places())

        self.space.what_is_accepted()

        self.assertEqual(list(), self.folder.places())

    # -----------------------------------------------------------------------

    def test_te18bis_a_place_of_this_hour_stays(self):
        """TE18. What the sweep does not reach is what is still of this hour."""
        place, _ = self.space.ask_for_a_place()
        self.space.put(place, "a.wav", b"12345")

        self.space.what_is_accepted()

        self.assertEqual([place], self.folder.places())
        self.assertEqual(["a.wav"], self.folder.files(place))

    # -----------------------------------------------------------------------

    def test_te19_an_address_serves_nothing_else_of_the_machine(self):
        """TE19. The test this design rests on. A door which is not tested is a
        consigne. C10

        """
        place, _ = self.space.ask_for_a_place()
        self.space.put(place, "a.wav", b"12345")
        self.assertEqual(b"12345", self.space.serve(
            self.space.address_of(place, "a.wav")))

        beside = os.path.join(os.path.dirname(self.settings.space), "beside.txt")
        with open(beside, "wb") as fp:
            fp.write(b"not of a place")

        for address in (
                self.space.address_of(place, "../beside.txt"),
                self.space.address_of(place, "/etc/passwd"),
                self.space.address_of("..", "beside.txt"),
                self.space.address_of(self.an_old_place(), "a.wav"),
                "/etc/passwd",
                "../beside.txt",
                ""):
            self.assertEqual(b"", self.space.serve(address))

        os.remove(beside)

# ---------------------------------------------------------------------------


class TestTwoAtOnce(unittest.TestCase):
    """TE20 to TE22. What one request cannot show."""

    def setUp(self):
        self.settings = sppasDepositSettings()
        self.settings.space = tempfile.mkdtemp(prefix="test_deposit_")
        self.space = sppasDepositSpace(self.settings)
        self.folder = sppasSpaceFolder(self.settings)

    def tearDown(self):
        shutil.rmtree(self.settings.space, ignore_errors=True)

    # -----------------------------------------------------------------------

    @staticmethod
    def together(first, second):
        """Run two things at one instant, and give back what each answered."""
        answers = dict()
        start = threading.Barrier(2)

        def run(key, what):
            start.wait()
            answers[key] = what()

        threads = (threading.Thread(target=run, args=("first", first)),
                   threading.Thread(target=run, args=("second", second)))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        return answers["first"], answers["second"]

    # -----------------------------------------------------------------------

    def test_te20_two_files_of_one_name_at_one_instant(self):
        """TE20. One stands and one is refused, and the one which stands is
        whole and is one of the two -- never a mixture. Which of them wins is
        not checked: nothing promises it. C8

        """
        place, _ = self.space.ask_for_a_place()

        for turn in range(20):
            name = "a%d.wav" % turn
            first = b"1" * 4096
            second = b"2" * 8192

            answers = self.together(lambda: self.space.put(place, name, first),
                                    lambda: self.space.put(place, name, second))

            given = [ok for ok, _ in answers]
            self.assertEqual(1, given.count(True))
            self.assertEqual(1, given.count(False))
            self.assertIn(self.folder.read(place, name), (first, second))

    # -----------------------------------------------------------------------

    def test_te21_two_places_when_there_is_room_for_one(self):
        """TE21. Both may be given, and the space may then hold one place over
        its number. The test says that this is what happens: demanding
        exactness here would be a test written against the design. C6

        """
        self.settings.places = 3
        while len(self.folder.places()) < self.settings.places - 1:
            self.folder.make_a_place(sppasPlace.a_name_for(time.time()))

        answers = self.together(self.space.ask_for_a_place,
                                self.space.ask_for_a_place)

        for name, when in answers:
            self.assertTrue(len(name) > 0 or when > 0.)

        self.assertLessEqual(len(self.folder.places()), self.settings.places + 1)

        # The bound is verified again, on what is counted now.
        name, when = self.space.ask_for_a_place()
        self.assertEqual("", name)
        self.assertGreater(when, 0.)

    # -----------------------------------------------------------------------

    def test_te22_served_while_another_request_sweeps(self):
        """TE22. The bytes, whole, or nothing at all -- never half a file. What
        was opened is read to its end. T05

        """
        content = b"x" * 1024 * 512

        for turn in range(20):
            place, _ = self.space.ask_for_a_place()
            self.space.put(place, "a.wav", content)
            address = self.space.address_of(place, "a.wav")

            answers = self.together(lambda: self.space.serve(address),
                                    lambda: self.folder.delete(place))

            self.assertIn(answers[0], (content, b""))

# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
