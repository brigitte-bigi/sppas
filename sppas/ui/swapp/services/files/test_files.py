# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.services.files.test_files.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the provision of files, and of giving them back.

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

    TE1 to TE22 of the dossier "Providing files, and giving them back".
    TE1 to TE15 need nothing at all. TE16 and TE17 need the deposit API,
    TE18 and TE19 a disk, TE20 to TE22 the domain of the workspaces.

"""

from __future__ import annotations
import unittest
import os
import shutil
import tempfile

from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from ..deposit.deposit_settings import DepositSettings
from ..deposit.deposit_space import DepositSpace

from .files_acceptance import DepositAcceptance
from .files_feeding import Deposit
from .files_place import FilePlace
from .files_workspace import WorkspaceFiles
from .files_handing import AppExchange
from .files_delivery import ResultDelivery
from .files_record import FilesRecord
from .files_view import DepositView
from .files_view import DeliveryView

# ---------------------------------------------------------------------------


def text_of(view):
    """Give what a view built, as it will be sent.

    The one line to change the day a view gives back its tree otherwise.

    """
    return view.serialize()

# ---------------------------------------------------------------------------


class TestDepositAcceptance(unittest.TestCase):
    """TE1 to TE7. It reads nothing: no place, no API, no workspace."""

    def setUp(self):
        self.acceptance = DepositAcceptance()

    # -----------------------------------------------------------------------

    def test_te1_what_is_accepted_is_said_before_anything_is_given(self):
        """TE1. It depends on no file and on no deposit: the same answer is
        given before anything has been fed and after. B7, B8

        """
        said = self.acceptance.what_is_accepted()
        self.assertTrue(len(said) > 0)

        deposit = Deposit()
        deposit.feed("a.wav", 1024)
        self.assertEqual(said, self.acceptance.what_is_accepted())

    # -----------------------------------------------------------------------

    def test_te2_a_name_already_taken(self):
        """TE2. The first of the name stays and the second is refused, and the
        reason is given with the refusal. C12

        """
        deposit = Deposit()
        deposit.feed("a.wav", 1024)

        accepted, reason = self.acceptance.accepts("a.wav", deposit)
        self.assertFalse(accepted)
        self.assertTrue(len(reason) > 0)

        accepted, reason = self.acceptance.accepts("b.wav", deposit)
        self.assertTrue(accepted)
        self.assertEqual("", reason)

    # -----------------------------------------------------------------------

    def test_te3_an_extension_sppas_does_not_read(self):
        """TE3. What SPPAS reads is this domain's to say, and it says it on a
        name. C10

        """
        deposit = Deposit()
        for name in ("a.exe", "a.zip", "a.unknown", "a"):
            accepted, reason = self.acceptance.accepts(name, deposit)
            self.assertFalse(accepted)
            self.assertTrue(len(reason) > 0)

        for name in ("a.wav", "a.TextGrid"):
            accepted, reason = self.acceptance.accepts(name, deposit)
            self.assertTrue(accepted)

    # -----------------------------------------------------------------------

    def test_te4_a_size(self):
        """TE4. Beyond what the machine accepts is refused; one under it
        passes. The bound is the deposit API's, and is relayed. C4

        """
        bound = self.acceptance.what_is_accepted()["size"]
        self.assertTrue(self.acceptance.accepts_size(bound - 1))
        self.assertTrue(self.acceptance.accepts_size(bound))
        self.assertFalse(self.acceptance.accepts_size(bound + 1))

    # -----------------------------------------------------------------------

    def test_te5_a_volume(self):
        """TE5. Beyond the volume of one deposit is refused; one under it
        passes. C4

        """
        bound = self.acceptance.what_is_accepted()["volume"]
        self.assertTrue(self.acceptance.accepts_volume(bound - 1))
        self.assertTrue(self.acceptance.accepts_volume(bound))
        self.assertFalse(self.acceptance.accepts_volume(bound + 1))

    # -----------------------------------------------------------------------

    def test_te6_a_count_of_deposits(self):
        """TE6. Refused beyond the number of deposits, and the refusal says
        when to come back. Neither the bound nor the hour is invented here. C4

        """
        accepted, when = self.acceptance.accepts_one_more_deposit()
        if accepted is False:
            self.assertTrue(when > 0.)
        else:
            self.assertEqual(0., when)

    # -----------------------------------------------------------------------

    def test_te7_a_content_which_says_an_executable(self):
        """TE7. Read on the bytes and not on the name: the only check of this
        class which needs a content. T01

        """
        self.assertFalse(self.acceptance.accepts_content(b"MZ\x90\x00"))
        self.assertFalse(self.acceptance.accepts_content(b"\x7fELF\x02\x01"))
        self.assertFalse(self.acceptance.accepts_content(b"#!/bin/sh\necho"))
        self.assertTrue(self.acceptance.accepts_content(b"RIFF\x00\x00\x00\x00WAVE"))

# ---------------------------------------------------------------------------


class TestDeposit(unittest.TestCase):
    """TE8 to TE11. What is fed, before anything has travelled."""

    def setUp(self):
        self.deposit = Deposit()

    # -----------------------------------------------------------------------

    def test_te8_a_file_fed_in_raises_the_volume(self):
        """TE8. By its size, and by nothing else. T08"""
        self.assertEqual(0, self.deposit.volume())

        self.deposit.feed("a.wav", 1024)
        self.assertEqual(1024, self.deposit.volume())

        self.deposit.feed("b.wav", 512)
        self.assertEqual(1536, self.deposit.volume())

    # -----------------------------------------------------------------------

    def test_te9_a_file_taken_back_lowers_it(self):
        """TE9. And taking back what was never fed does nothing wrong. T09"""
        self.deposit.feed("a.wav", 1024)
        self.deposit.feed("b.wav", 512)

        self.deposit.take_back("a.wav")
        self.assertEqual(512, self.deposit.volume())

        self.deposit.take_back("never_fed.wav")
        self.assertEqual(512, self.deposit.volume())

        self.deposit.take_back("b.wav")
        self.assertEqual(0, self.deposit.volume())

    # -----------------------------------------------------------------------

    def test_te10_what_is_to_be_given_keeps_its_order(self):
        """TE10. The order it was fed in, and not another. T08"""
        for name in ("c.wav", "a.wav", "b.TextGrid"):
            self.deposit.feed(name, 10)

        self.assertEqual(["c.wav", "a.wav", "b.TextGrid"],
                         [f.name for f in self.deposit.files])

    # -----------------------------------------------------------------------

    def test_te11_nothing_of_a_content_travels_while_she_feeds(self):
        """TE11. What is held is a name and a size. A test which found a
        content here would have found RO8 broken.

        """
        self.deposit.feed("a.wav", 1024)

        for placed in self.deposit.files:
            self.assertEqual("", placed.content)

# ---------------------------------------------------------------------------


class TestViews(unittest.TestCase):
    """TE12 and TE13. A view is given a state and builds a tree."""

    def test_te12_a_view_shows_what_the_state_says(self):
        """TE12. What that state said, and nothing more: no refusal it
        invented, no total it counted. D1

        """
        record = FilesRecord()
        record.fed = [("a.wav", 1024), ("b.TextGrid", 512)]

        view = DepositView()
        view.populate_tree_content(record)
        shown = text_of(view)

        self.assertIn("a.wav", shown)
        self.assertIn("b.TextGrid", shown)
        self.assertNotIn("refus", shown.lower())

    # -----------------------------------------------------------------------

    def test_te13_a_state_which_says_nothing(self):
        """TE13. Gives a tree which says nothing. A view which counted a total
        or invented a refusal is caught here. D1

        """
        record = FilesRecord()

        for view in (DepositView(), DeliveryView()):
            view.populate_tree_content(record)
            shown = text_of(view)
            self.assertNotIn("a.wav", shown)
            self.assertNotIn("refus", shown.lower())

# ---------------------------------------------------------------------------


class TestAppExchange(unittest.TestCase):
    """TE14 and TE15. The door, and it is tested."""

    def setUp(self):
        self.wkp = sppasWorkspace()
        self.root = tempfile.mkdtemp(prefix="test_files_")
        self.names = list()
        for name in ("a.wav", "b.wav", "c.wav"):
            path = os.path.join(self.root, name)
            with open(path, "w") as fp:
                fp.write("")
            self.wkp.add_file(path)
            self.names.append(path)

        # Two of the three are to be treated.
        self.wkp.set_object_state(States().CHECKED, self.wkp.get_object(self.names[0]))
        self.wkp.set_object_state(States().CHECKED, self.wkp.get_object(self.names[1]))

        self.workspace = WorkspaceFiles(self.wkp)
        self.exchange = AppExchange(self.workspace)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te14_what_is_handed_holds_the_checked_files_and_them_only(self):
        """TE14. The one it is given is made for it. B1, RO9"""
        handed = self.exchange.for_app()

        given = sorted(f.get_id() for f in handed.get_all_files())
        self.assertEqual(sorted(self.names[:2]), given)

    # -----------------------------------------------------------------------

    def test_te15_the_workspace_of_the_person_does_not_move(self):
        """TE15. Everything in what was handed is changed, emptied and added
        to, and the workspace of the person has not moved. It is what every
        other promise of this domain rests on. RO9

        """
        before = sorted(f.get_id() for f in self.wkp.get_all_files())
        states_before = [self.wkp.get_object(n).get_state() for n in self.names]

        handed = self.exchange.for_app()
        self.assertIsNot(self.wkp, handed)

        for one in list(handed.get_all_files()):
            handed.set_object_state(States().UNUSED, one)
        other = os.path.join(self.root, "made_by_the_app.wav")
        with open(other, "w") as fp:
            fp.write("")
        handed.add_file(other)
        handed.remove_file(self.names[0])

        after = sorted(f.get_id() for f in self.wkp.get_all_files())
        self.assertEqual(before, after)
        self.assertEqual(states_before,
                         [self.wkp.get_object(n).get_state() for n in self.names])

# ---------------------------------------------------------------------------


class TestFilePlace(unittest.TestCase):
    """TE16 and TE17. The only class which calls the deposit API."""

    def setUp(self):
        self.settings = DepositSettings()
        self.settings.space = tempfile.mkdtemp(prefix="test_files_")
        self.api = DepositSpace(self.settings)
        self.place = FilePlace(self.api)

    def tearDown(self):
        shutil.rmtree(self.settings.space, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te16_a_place_a_copy_and_an_address(self):
        """TE16. A place asked for and obtained, a copy put there under the
        name it was given, an address which leads to it. T01, T05

        """
        given = self.place.ask_for_a_place()
        self.assertTrue(len(given) > 0)

        self.assertTrue(self.place.put(given, "a.wav", b"12345"))

        address = self.place.address_of(given, "a.wav")
        self.assertTrue(len(address) > 0)
        self.assertEqual(b"12345", self.api.serve(address))

    # -----------------------------------------------------------------------

    def test_te17_a_refusal_is_relayed_as_it_was_given(self):
        """TE17. With its hour, and nothing of it invented here. The bounds are
        the API's, and this class says what that API said. F13, D2

        """
        said = self.place.what_is_accepted()
        self.assertEqual(self.api.what_is_accepted(),
                         (said["size"], said["volume"], said["deposits"]))

        while True:
            given = self.place.ask_for_a_place()
            if len(given) == 0:
                break

        refused, when = self.place.when_there_will_be_room()
        self.assertTrue(refused)
        self.assertGreater(when, 0.)

# ---------------------------------------------------------------------------


class TestResultDelivery(unittest.TestCase):
    """TE18 and TE19. What an address reaches, and what it does not."""

    def setUp(self):
        self.settings = DepositSettings()
        self.settings.space = tempfile.mkdtemp(prefix="test_files_")
        self.api = DepositSpace(self.settings)
        self.place = FilePlace(self.api)
        self.delivery = ResultDelivery(self.place)

        self.given = self.place.ask_for_a_place()
        self.place.put(self.given, "a-phon.TextGrid", b"produced")

    def tearDown(self):
        shutil.rmtree(self.settings.space, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te18_an_address_reaches_its_file(self):
        """TE18. Its file, and nothing else of the machine. B13"""
        address = self.delivery.address_of(self.given, "a-phon.TextGrid")
        self.assertEqual(b"produced", self.delivery.serve(address))

    # -----------------------------------------------------------------------

    def test_te19_nothing_at_all(self):
        """TE19. When the file is out of date, and when the address names none.
        The two give one answer. B13

        """
        for address in (
                self.delivery.address_of(self.given, "never_produced.TextGrid"),
                self.delivery.address_of("no_such_place", "a-phon.TextGrid"),
                self.delivery.address_of(self.given, "../../etc/passwd"),
                ""):
            self.assertEqual(b"", self.delivery.serve(address))

# ---------------------------------------------------------------------------


class TestWorkspaceFiles(unittest.TestCase):
    """TE20 to TE22. The only class which speaks to the domain of the
    workspaces, and the only tests which need it.

    """

    def setUp(self):
        self.wkp = sppasWorkspace()
        self.root = tempfile.mkdtemp(prefix="test_files_")
        self.names = list()
        for name in ("a.wav", "b.wav"):
            path = os.path.join(self.root, name)
            with open(path, "w") as fp:
                fp.write("")
            self.names.append(path)

        self.workspace = WorkspaceFiles(self.wkp)
        self.workspace.make_known(self.names)
        self.workspace.check(self.names)
        self.exchange = AppExchange(self.workspace)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te20_locking_a_file_takes_it_out_of_what_is_handed(self):
        """TE20. Handed twice around a lock: the second does not hold it. A
        locked file is no longer checked. T10

        """
        first = self.exchange.for_app()
        self.assertEqual(2, len(list(first.get_all_files())))

        self.workspace.lock([self.names[0]])

        second = self.exchange.for_app()
        given = [f.get_id() for f in second.get_all_files()]
        self.assertEqual([self.names[1]], given)

    # -----------------------------------------------------------------------

    def test_te21_releasing_puts_it_back(self):
        """TE21. Among what is handed, and in the state it had. T11, T12"""
        self.workspace.lock([self.names[0]])
        self.workspace.release([self.names[0]])

        handed = self.exchange.for_app()
        given = sorted(f.get_id() for f in handed.get_all_files())
        self.assertEqual(sorted(self.names), given)

    # -----------------------------------------------------------------------

    def test_te22_writing_what_was_produced_unchecks_nothing(self):
        """TE22. What was checked before is checked after: a produced file is
        added and checked, and it takes nothing away. T04

        """
        made = os.path.join(self.root, "a-phon.TextGrid")
        with open(made, "w") as fp:
            fp.write("")

        self.workspace.write_produced([made])

        self.assertEqual(States().CHECKED,
                         self.wkp.get_object(self.names[0]).get_state())
        self.assertEqual(States().CHECKED,
                         self.wkp.get_object(self.names[1]).get_state())
        self.assertEqual(States().CHECKED,
                         self.wkp.get_object(made).get_state())

# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
