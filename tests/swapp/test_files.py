# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_files.py
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
    TE29 and TE30 run with the deposit API absent.

"""

from __future__ import annotations
import unittest
import os
import shutil
import tempfile
from unittest import mock

from whakerpy.htmlmaker import HTMLTree

from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from sppas.ui.swapp.services.deposit.deposit_settings import swappDepositSettings
from sppas.ui.swapp.services.deposit.deposit_space import swappDepositSpace

from sppas.ui.swapp.services.files.files_acceptance import swappDepositAcceptance
from sppas.ui.swapp.services.files.files_feeding import swappDataFiles
from sppas.ui.swapp.services.files.files_place import swappFilePlace
from sppas.ui.swapp.services.files.files_workspace import swappWorkspaceFiles
from sppas.ui.swapp.services.files.files_handing import swappAppExchange
from sppas.ui.swapp.services.files.files_chooser import swappFileChooser
from sppas.ui.swapp.services.files.files_provision import swappFileProvision
from sppas.ui.swapp.services.files.files_delivery import swappResultDelivery
from sppas.ui.swapp.services.files.files_record import swappFilesRecord
from sppas.ui.swapp.services.files.files_view import swappDepositView
from sppas.ui.swapp.services.files.files_view import swappDeliveryView
from sppas.ui.swapp.services.files.files_controller import MSG_FAILED
from sppas.ui.swapp.services.files.files_view import MSG_FINISHED
from sppas.ui.swapp.services.files.files_manager import swappFilesManager

# ---------------------------------------------------------------------------


def files_of(workspace):
    """Give every file of a workspace, whatever its state.

    The three levels are walked because a workspace gives its files by
    state and not as a whole: what is handed has to be seen entirely, the
    promise being that it holds the checked files *and them only*.

    """
    return [fn for fp in workspace.get_paths() for fr in fp for fn in fr]

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
        self.acceptance = swappDepositAcceptance()

    # -----------------------------------------------------------------------

    def test_te1_what_is_accepted_is_said_before_anything_is_given(self):
        """TE1. It depends on no file and on no deposit: the same answer is
        given before anything has been fed and after. B7, B8

        """
        said = self.acceptance.what_is_accepted()
        self.assertTrue(len(said) > 0)

        deposit = swappDataFiles()
        deposit.feed("a.wav", 1024)
        self.assertEqual(said, self.acceptance.what_is_accepted())

    # -----------------------------------------------------------------------

    def test_te2_a_name_already_taken(self):
        """TE2. The first of the name stays and the second is refused, and the
        reason is given with the refusal. C12

        """
        deposit = swappDataFiles()
        deposit.feed("a.wav", 1024)

        accepted, reason = self.acceptance.accepts("a.wav", deposit)
        self.assertFalse(accepted)
        self.assertTrue(len(reason) > 0)

        accepted, reason = self.acceptance.accepts("b.wav", deposit)
        self.assertTrue(accepted)
        self.assertEqual("", reason)

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
        self.deposit = swappDataFiles()

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

    def setUp(self):
        # The identifier an app gives: the node of its page the container is
        # built under. It is read from a tree of its own, and written nowhere
        # here -- append_child() refuses a node which was built under another
        # parent, and a value copied is a value which will differ from itself.
        self.parent = HTMLTree("test_files").body_main.identifier

    # -----------------------------------------------------------------------

    def test_te12_a_view_shows_what_the_state_says(self):
        """TE12. What that state said, and nothing more: no refusal it
        invented, no total it counted. D1

        """
        record = swappFilesRecord()
        record.reachable = False
        record.fed = [("a.wav", 1024), ("b.TextGrid", 512)]

        view = swappDepositView(self.parent)
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
        record = swappFilesRecord()
        record.reachable = False

        for view in (swappDepositView(self.parent), swappDeliveryView(self.parent)):
            view.populate_tree_content(record)
            shown = text_of(view)
            self.assertNotIn("a.wav", shown)
            self.assertNotIn("refus", shown.lower())

    # -----------------------------------------------------------------------

    def test_te23_the_same_state_gives_the_same_tree(self):
        """TE23. No clock is read and no order shifts: a view is called with
        everything it needs and asks for nothing. D1

        """
        record = swappFilesRecord()
        record.reachable = False
        record.fed = [("a.wav", 1024), ("b.TextGrid", 512)]
        record.to_be_shown = {"accepted": "1536 of 100 bytes accepted here."}

        first = swappDepositView(self.parent)
        first.populate_tree_content(record)
        second = swappDepositView(self.parent)
        second.populate_tree_content(record)

        self.assertEqual(text_of(first), text_of(second))

    # -----------------------------------------------------------------------

    def test_te24_a_refusal_is_marked_on_the_file_it_refuses(self):
        """TE24. On that file and on no other, with the reason it came with.
        A file which was refused stays in the list. C12

        """
        record = swappFilesRecord()
        record.reachable = False
        record.fed = [("a.wav", 1024)]
        record.to_be_shown = {"refused": {"b.exe": "SPPAS does not read this kind of file."}}

        view = swappDepositView(self.parent)
        view.populate_tree_content(record)
        shown = text_of(view)

        self.assertIn("a.wav", shown)
        self.assertIn("b.exe", shown)
        self.assertIn("does not read", shown)
        self.assertEqual(1, shown.count("does not read"))
        self.assertEqual(1, shown.count('aria-invalid="true"'))
        self.assertEqual(1, shown.count('aria-invalid="false"'))

    # -----------------------------------------------------------------------

    def test_te25_no_place_no_control_which_sends(self):
        """TE25. Not one which is built and disabled: one which is not there.
        And what she fed stands as it was.

        """
        record = swappFilesRecord()
        record.reachable = False
        record.fed = [("a.wav", 1024)]

        view = swappDepositView(self.parent)
        view.populate_tree_content(record)
        self.assertIn("cta-button", text_of(view))

        record.to_be_shown = {"no_place": "4 min 32 s"}
        refused = swappDepositView(self.parent)
        refused.populate_tree_content(record)
        shown = text_of(refused)

        self.assertNotIn("cta-button", shown)
        self.assertIn("a.wav", shown)

    # -----------------------------------------------------------------------

    def test_te26_a_view_never_writes_what_it_was_not_given(self):
        """TE26. No path, no place, no name of a folder, nothing of the
        machine: what the person may see was chosen before the view was
        called. B6

        """
        record = swappFilesRecord()
        record.to_be_shown = {"produced": {"a": [("a-phon.TextGrid", "/deposit/place_1/a-phon.TextGrid")],
                                           "b": ["Nothing was produced: the file holds no transcription."]},
                              "reachable_until": "Reachable until 14:32.",
                              "finished": True}

        view = swappDeliveryView(self.parent)
        view.populate_tree_content(record)
        shown = text_of(view)

        self.assertIn("a-phon.TextGrid", shown)
        self.assertIn("no transcription", shown)
        self.assertIn("14:32", shown)
        self.assertNotIn(tempfile.gettempdir(), shown)
        self.assertNotIn("a.wav", shown)

    # -----------------------------------------------------------------------

    def test_te27_where_the_files_stand_already(self):
        """TE27. The view is told which case it is in and reads nothing else:
        the files are listed by their path, no bound is shown and no file
        carries a mark of validity. C5, C6

        """
        wkp = sppasWorkspace()
        root = tempfile.mkdtemp(prefix="test_files_")
        path = os.path.join(root, "a.wav")
        with open(path, "w") as fp:
            fp.write("")
        wkp.add_file(path)

        record = swappFilesRecord()
        record.reachable = True
        record.workspace = wkp
        record.to_be_shown = {"accepted": "1536 of 100 bytes accepted here."}

        view = swappDepositView(self.parent)
        view.populate_tree_content(record)
        shown = text_of(view)
        shutil.rmtree(root, ignore_errors=True)

        self.assertIn(path, shown)
        self.assertNotIn("aria-invalid", shown)
        self.assertNotIn("of 100 bytes", shown)
        self.assertNotIn("type=\"file\"", shown)

    # -----------------------------------------------------------------------

    def test_te27bis_nothing_designated_yet(self):
        """TE27. The same case, before she has designated anything: the list
        is empty and the view shows the same control. C6

        """
        record = swappFilesRecord()
        record.reachable = True

        view = swappDepositView(self.parent)
        view.populate_tree_content(record)
        shown = text_of(view)

        self.assertIn("files_browse", shown)
        self.assertNotIn("type=\"file\"", shown)

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

        self.workspace = swappWorkspaceFiles(self.wkp)
        self.exchange = swappAppExchange(self.workspace)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te14_what_is_handed_holds_the_checked_files_and_them_only(self):
        """TE14. The one it is given is made for it. B1, RO9"""
        handed = self.exchange.for_app()

        given = sorted(f.get_id() for f in files_of(handed))
        self.assertEqual(sorted(self.names[:2]), given)

    # -----------------------------------------------------------------------

    def test_te15_the_workspace_of_the_person_does_not_move(self):
        """TE15. Everything in what was handed is changed, emptied and added
        to, and the workspace of the person has not moved. It is what every
        other promise of this domain rests on. RO9

        """
        before = sorted(f.get_id() for f in files_of(self.wkp))
        states_before = [self.wkp.get_object(n).get_state() for n in self.names]

        handed = self.exchange.for_app()
        self.assertIsNot(self.wkp, handed)

        for one in list(files_of(handed)):
            handed.set_object_state(States().UNUSED, one)
        other = os.path.join(self.root, "made_by_the_app.wav")
        with open(other, "w") as fp:
            fp.write("")
        handed.add_file(other)
        handed.remove_file(self.names[0])

        after = sorted(f.get_id() for f in files_of(self.wkp))
        self.assertEqual(before, after)
        self.assertEqual(states_before,
                         [self.wkp.get_object(n).get_state() for n in self.names])

# ---------------------------------------------------------------------------


class TestFileChooser(unittest.TestCase):
    """TE28. The way in of the files which stand already."""

    def setUp(self):
        self.wkp = sppasWorkspace()
        self.root = tempfile.mkdtemp(prefix="test_files_")
        self.names = list()
        for name in ("a.wav", "b.wav"):
            path = os.path.join(self.root, name)
            with open(path, "w") as fp:
                fp.write("")
            self.names.append(path)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    @staticmethod
    def a_chooser(answer):
        """Give a chooser which answers what a dialog would answer."""
        class _Dialog(object):
            def ask_file(self, **kwargs):
                return answer

        return swappFileChooser(_Dialog())

    # -----------------------------------------------------------------------

    def test_te28_what_a_dialog_answers_is_read_and_never_guessed(self):
        """TE28. One name, several of them, nothing, or something which is no
        name: only names are kept, and nothing is raised.

        """
        self.assertEqual([self.names[0]],
                         swappFileChooser.validate_chosen(self.names[0]))
        self.assertEqual(self.names,
                         swappFileChooser.validate_chosen(list(self.names)))
        self.assertEqual(list(), swappFileChooser.validate_chosen(None))
        self.assertEqual(list(), swappFileChooser.validate_chosen(""))
        self.assertEqual(list(), swappFileChooser.validate_chosen(12))

    # -----------------------------------------------------------------------

    def test_te28bis_what_she_chose_is_known_and_checked(self):
        """TE28. The files join the workspace as they stand: nothing is
        copied and nothing is asked of the deposit API. A person who chose
        nothing adds nothing.

        """
        provision = swappFileProvision(swappWorkspaceFiles(self.wkp),
                                       chooser=TestFileChooser.a_chooser(list(self.names)))

        self.assertEqual(self.names, provision.ask_for_files())
        self.assertEqual(sorted(self.names),
                         sorted(f.get_id() for f in files_of(provision.files_for_app())))

        nothing = swappFileProvision(swappWorkspaceFiles(sppasWorkspace()),
                                     chooser=TestFileChooser.a_chooser(""))
        self.assertEqual(list(), nothing.ask_for_files())
        self.assertEqual(list(), files_of(nothing.files_for_app()))

# ---------------------------------------------------------------------------


class TestLocalUse(unittest.TestCase):
    """TE29 and TE30. Where the files stand already, and nothing else."""

    def setUp(self):
        self.parent = HTMLTree("test_files").body_main.identifier
        self.root = tempfile.mkdtemp(prefix="test_files_")
        self.path = os.path.join(self.root, "a.wav")
        with open(self.path, "w") as fp:
            fp.write("")

        # The deposit API is absent: an error is raised as soon as it is built.
        self.absent = mock.patch(
            "sppas.ui.swapp.services.files.files_place.swappDepositSpace",
            side_effect=RuntimeError("The deposit API is absent."))
        self.absent.start()

    def tearDown(self):
        self.absent.stop()
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    @staticmethod
    def answer(manager, events):
        """Offer the events of one request, and give what the container shows.

        :param manager: (swappFilesManager) What an app holds of the service
        :param events: (dict) The events of one request
        :return: (tuple) Whether they were consumed, and the HTML of the container

        """
        consumed = manager.consumes(events)
        manager.populate_view()

        return consumed, manager.container().serialize()

    # -----------------------------------------------------------------------

    def test_te29_no_deposit_api_where_the_files_stand_already(self):
        """TE29. The service is built and answers every task, and nothing of
        the deposit API is built, asked or announced. C15

        """
        manager = swappFilesManager(self.parent, reachable=True)

        requests = ({"designate": self.path},
                    {"take_back": self.path},
                    {"designate": self.path},
                    {"ready": ""},
                    {"finished": ""})
        for events in requests:
            consumed, shown = TestLocalUse.answer(manager, events)
            self.assertTrue(consumed)
            self.assertNotIn(MSG_FAILED, shown)

    # -----------------------------------------------------------------------

    def test_te30_ready(self):
        """TE30. ready sends nothing and asks nothing of the deposit API;
        is_ready() answers true after it, and false after any other task. E7

        """
        manager = swappFilesManager(self.parent, reachable=True)

        manager.consumes({"designate": self.path})
        self.assertFalse(manager.is_ready())

        self.assertTrue(manager.consumes({"ready": ""}))
        self.assertTrue(manager.is_ready())
        handed = list()
        for handed_file in files_of(manager.files_for_app()):
            handed.append(handed_file.get_id())
        self.assertEqual([self.path], handed)

        manager.consumes({"take_back": self.path})
        self.assertFalse(manager.is_ready())

    # -----------------------------------------------------------------------

    def test_te31_start_over(self):
        """TE31. The deposit is shown again, and no file is handed afterwards:
        the files are known to a new workspace, holding none.

        """
        manager = swappFilesManager(self.parent, reachable=True)
        manager.consumes({"designate": self.path})
        manager.consumes({"finished": ""})
        manager.populate_view()
        self.assertIn(MSG_FINISHED, manager.container().serialize())

        manager.start_over()
        manager.populate_view()
        self.assertNotIn(MSG_FINISHED, manager.container().serialize())
        self.assertEqual(list(), files_of(manager.files_for_app()))

# ---------------------------------------------------------------------------


class TestFilePlace(unittest.TestCase):
    """TE16 and TE17. The only class which calls the deposit API."""

    def setUp(self):
        self.settings = swappDepositSettings()
        self.settings.space = tempfile.mkdtemp(prefix="test_files_")
        self.api = swappDepositSpace(self.settings)
        self.place = swappFilePlace(self.api)

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
        self.settings = swappDepositSettings()
        self.settings.space = tempfile.mkdtemp(prefix="test_files_")
        self.api = swappDepositSpace(self.settings)
        self.place = swappFilePlace(self.api)
        self.delivery = swappResultDelivery(self.place)

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

        self.workspace = swappWorkspaceFiles(self.wkp)
        self.workspace.make_known(self.names)
        self.workspace.check(self.names)
        self.exchange = swappAppExchange(self.workspace)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te20_locking_a_file_takes_it_out_of_what_is_handed(self):
        """TE20. Handed twice around a lock: the second does not hold it. A
        locked file is no longer checked. T10

        """
        first = self.exchange.for_app()
        self.assertEqual(2, len(list(files_of(first))))

        self.workspace.lock([self.names[0]])

        second = self.exchange.for_app()
        given = [f.get_id() for f in files_of(second)]
        self.assertEqual([self.names[1]], given)

    # -----------------------------------------------------------------------

    def test_te21_releasing_puts_it_back(self):
        """TE21. Among what is handed, and in the state it had. T11, T12"""
        self.workspace.lock([self.names[0]])
        self.workspace.release([self.names[0]])

        handed = self.exchange.for_app()
        given = sorted(f.get_id() for f in files_of(handed))
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
