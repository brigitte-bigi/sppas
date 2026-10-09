# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_convert.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the models of Convert.

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

    TE1 to TE27 of the dossier "Convert - an app of SPPAS": the four
    sub-models and the façade. Six need nothing but the API, twelve need it,
    six need a disk, four need the provision of files. The controller, the view
    and its fragments are owed.

"""

from __future__ import annotations
import unittest
import os
import shutil
import tempfile
from unittest.mock import patch

from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasPoint
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata.aio.readwrite import FileFormatProperty
from sppas.src.wkps import sppasWorkspace
from sppas.src.wkps import States

from whakerpy.htmlmaker import HTMLTree

from sppas.ui.swapp.app_convert.convert_model import swappConvertModel
from sppas.ui.swapp.app_convert.convert_formats import swappModelFormats
from sppas.ui.swapp.app_convert.convert_remediation import swappModelRemediation
from sppas.ui.swapp.app_convert.convert_conversion import swappModelConversion
from sppas.ui.swapp.app_convert.convert_provision import swappModelProvision
from sppas.ui.swapp.services.files import swappFilesManager
from sppas.ui.swapp.services.files import swappWorkspaceFiles
from sppas.ui.swapp.services.files.files_view import MSG_FINISHED

# ---------------------------------------------------------------------------


def a_writable_format(supporting: bool, prop: str) -> str:
    """Give the extension of a writable format, by what it holds.

    Nothing is hard-coded: the format is picked from what the API answers, so
    that a test says what it means and not which software was installed.

    :param supporting: (bool) The property is supported, or it is not.
    :param prop: (str) Name of the support method, e.g. "multi_tiers_support".
    :return: (str) An extension, dot included.

    """
    for extension in sppasTrsRW.extensions():
        fmt = FileFormatProperty(extension)
        if fmt.get_writer() is False:
            continue
        instance = sppasTrsRW.TRANSCRIPTION_TYPES[extension.replace(".", "")]()
        if getattr(instance, prop)() is supporting:
            return fmt.get_extension()
    raise unittest.SkipTest("no writable format with %s = %s" % (prop, supporting))


def one_tier(name: str = "tier", points: bool = False) -> sppasTranscription:
    """Give a transcription holding one tier and one annotation."""
    trs = sppasTranscription("test")
    tier = trs.create_tier(name)
    if points is True:
        location = sppasLocation(sppasPoint(1.))
    else:
        location = sppasLocation(sppasInterval(sppasPoint(1.), sppasPoint(2.)))
    tier.create_annotation(location, sppasLabel(sppasTag("a")))
    return trs


def a_batch(paths: list) -> sppasWorkspace:
    """Give a batch: a workspace in which the given files are known and checked.

    :param paths: (list of str) Names of the files, with their path
    :return: (sppasWorkspace)

    """
    wkp = sppasWorkspace()
    for path in paths:
        wkp.add_file(path)
        wkp.set_object_state(States().CHECKED, wkp.get_object(path))
    return wkp


def names_in(wkp: sppasWorkspace) -> list:
    """Give the names of the files of a workspace, in the order it holds them.

    :param wkp: (sppasWorkspace) Workspace to be read
    :return: (list of str) Names of the files, with their path

    """
    names = list()
    for path in wkp.get_paths():
        for root in path:
            for one in root:
                names.append(one.get_id())
    return names


def several_tiers(how_many: int = 3) -> sppasTranscription:
    """Give a transcription holding several tiers."""
    trs = one_tier("first")
    for i in range(how_many - 1):
        tier = trs.create_tier("tier%d" % i)
        tier.create_annotation(
            sppasLocation(sppasInterval(sppasPoint(1.), sppasPoint(2.))),
            sppasLabel(sppasTag("a")))
    return trs

# ---------------------------------------------------------------------------


class TestModelRemediation(unittest.TestCase):
    """TE1 to TE6. A content in, a content out: nothing is installed."""

    def setUp(self):
        self.remediation = swappModelRemediation()
        self.holds_all = {"multi_tiers": True, "point": True, "interval": True,
                          "alt_tag": True, "tag_types": True,
                          "tag_geometry": True, "empty_tier": True,
                          "metadata": True, "ctrl_vocab": True, "media": True}

    # -----------------------------------------------------------------------

    def holds_all_but(self, *properties):
        """Give the properties of a destination holding everything but these."""
        properties_of = dict(self.holds_all)
        for one in properties:
            properties_of[one] = False
        return properties_of

    # -----------------------------------------------------------------------

    def test_te1_a_content_the_destination_holds(self):
        """TE1. It comes back as it was, and nothing was transformed."""
        trs = several_tiers(3)

        given, refused = self.remediation.remediate(trs, self.holds_all, dict())

        self.assertIsNone(refused)
        self.assertEqual(3, len(given))
        self.assertEqual(list(), self.remediation.what_was_transformed())

    # -----------------------------------------------------------------------

    def test_te2_a_transformation_is_made_and_named(self):
        """TE2. The content is transformed, and what transformed it is named:
        that is what a remark is made of. T06, D12

        """
        trs = several_tiers(3)
        properties = self.holds_all_but("multi_tiers")

        given, refused = self.remediation.remediate(
            trs, properties, {"multi_tiers": "one file per tier"})

        self.assertIsNone(refused)
        transformed = self.remediation.what_was_transformed()
        self.assertEqual(1, len(transformed))
        self.assertIn("multi_tiers", transformed[0])

    # -----------------------------------------------------------------------

    def test_te3_the_content_is_verified_again(self):
        """TE3. Splitting a file of several tiers can leave a tier which is
        empty, and the destination may refuse that: the second property is seen
        only because the content was verified again. C14

        """
        trs = several_tiers(2)
        trs.create_tier("an empty one")
        properties = self.holds_all_but("multi_tiers", "empty_tier")

        given, refused = self.remediation.remediate(
            trs, properties, {"multi_tiers": "one file per tier"})

        transformed = self.remediation.what_was_transformed()
        self.assertIn("multi_tiers", " ".join(transformed))
        self.assertIn("empty_tier", " ".join(transformed))

    # -----------------------------------------------------------------------

    def test_te4_a_remediation_is_applied_at_most_once(self):
        """TE4. The chain ends, and this is what ends it. Nothing of the
        conceptual model asks for it: the operational level found it. C15

        """
        trs = several_tiers(3)
        properties = self.holds_all_but("multi_tiers", "empty_tier",
                                        "no_tiers")

        given, refused = self.remediation.remediate(
            trs, properties, {"multi_tiers": "one file per tier"})

        transformed = self.remediation.what_was_transformed()
        self.assertEqual(len(transformed), len(set(transformed)))

    # -----------------------------------------------------------------------

    def test_te5_a_chain_which_ends_in_a_refusal(self):
        """TE5. What it held exceeds the destination after every remediation
        its answers allow, and the cause is the one which ended the chain. T06

        """
        trs = one_tier(points=True)
        properties = self.holds_all_but("point")

        given, refused = self.remediation.remediate(
            trs, properties, {"point": "skip the tier"})

        self.assertIsNotNone(refused)
        self.assertIn("point", refused)

    # -----------------------------------------------------------------------

    def test_te6_it_touches_no_file(self):
        """TE6. Whatever it is given, nothing appears on a disk. It is what
        makes the business logic of this application testable with nothing.

        """
        root = tempfile.mkdtemp(prefix="test_convert_")
        try:
            before = os.listdir(root)
            trs = several_tiers(3)
            self.remediation.remediate(
                trs, self.holds_all_but("multi_tiers", "point"),
                {"multi_tiers": "one file per tier", "point": "skip the tier"})
            self.assertEqual(before, os.listdir(root))
        finally:
            shutil.rmtree(root, ignore_errors=True)

# ---------------------------------------------------------------------------


class TestModelFormats(unittest.TestCase):
    """TE7 to TE13. The API, and no file of the user."""

    def setUp(self):
        self.formats = swappModelFormats()

    # -----------------------------------------------------------------------

    def test_te7_the_formats_which_can_be_written(self):
        """TE7. What the API says can be written, and nothing else. C2"""
        offered = self.formats.writable_formats()
        self.assertTrue(len(offered) > 0)

        for fmt in offered:
            self.assertTrue(FileFormatProperty(fmt.extension).get_writer())

        readable_only = [FileFormatProperty(e).get_extension()
                         for e in sppasTrsRW.extensions()
                         if FileFormatProperty(e).get_writer() is False]
        for extension in readable_only:
            self.assertNotIn(extension, [f.extension for f in offered])

    # -----------------------------------------------------------------------

    def test_te8_the_properties_of_a_format(self):
        """TE8. What the API answers, relayed and not decided here. D2"""
        extension = a_writable_format(True, "multi_tiers_support")
        properties = self.formats.properties_of(extension)

        instance = sppasTrsRW.TRANSCRIPTION_TYPES[extension.replace(".", "")]()
        self.assertEqual(instance.multi_tiers_support(),
                         properties["multi_tiers"])
        self.assertEqual(instance.metadata_support(), properties["metadata"])

    # -----------------------------------------------------------------------

    def test_te9_an_option_is_a_row_of_the_correspondence(self):
        """TE9. C4 made checkable: a row added to the file which holds the
        correspondence becomes a question asked, and no code is touched. The
        day this has to be rewritten, the correspondence has become code.

        """
        extension = a_writable_format(False, "radius_support")

        before = [o.option for o in self.formats.options_of(extension)]
        self.assertNotIn("radius", before)

        self.formats.correspondence.add(
            "radius", question="the vagueness of the points",
            answers=("keep it", "drop it"), default="keep it", alters=True)

        after = [o.option for o in self.formats.options_of(extension)]
        self.assertIn("radius", after)

    # -----------------------------------------------------------------------

    def test_te10_the_answers_are_restricted_by_the_destination(self):
        """TE10. Answering yes where the destination allows neither comments
        nor a tier has the effect of no: the option is not offered. C5

        """
        extension = a_writable_format(False, "metadata_support")
        instance = sppasTrsRW.TRANSCRIPTION_TYPES[extension.replace(".", "")]()

        options = {o.option: o for o in self.formats.options_of(extension)}

        if instance.comments_support() is False:
            self.assertNotIn("preservation", options)
        else:
            self.assertIn("preservation", options)
            self.assertEqual({"yes", "no"}, set(options["preservation"].answers))

    # -----------------------------------------------------------------------

    def test_te11_a_property_no_option_covers_is_a_structural_loss(self):
        """TE11. And it is the same whatever the files are: it depends on the
        destination alone. C6

        """
        extension = a_writable_format(False, "hierarchy_support")

        lost = self.formats.structural_loss_of(extension)
        self.assertIn("hierarchy", lost)

        covered = [o.option for o in self.formats.options_of(extension)]
        for one in lost:
            self.assertNotIn(one, covered)

        self.assertEqual(lost, self.formats.structural_loss_of(extension))

    # -----------------------------------------------------------------------

    def test_te12_the_preservation_option_appears_once(self):
        """TE12. It covers three properties and is one question, not three. R2"""
        extension = a_writable_format(False, "metadata_support")
        options = [o.option for o in self.formats.options_of(extension)]

        self.assertEqual(1, options.count("preservation"))
        for covered in ("metadata", "ctrl_vocab", "media"):
            self.assertNotIn(covered, options)

    # -----------------------------------------------------------------------

    def test_te13_no_file_of_the_user_is_read(self):
        """TE13. Every answer is given before anything is opened. C7"""
        extension = a_writable_format(False, "multi_tiers_support")

        with patch("builtins.open") as opened:
            self.formats.writable_formats()
            self.formats.properties_of(extension)
            self.formats.options_of(extension)
            self.formats.structural_loss_of(extension)
            for call in opened.call_args_list:
                self.assertNotIn(".wav", str(call))
                self.assertNotIn(".TextGrid", str(call))

# ---------------------------------------------------------------------------


class TestModelConversion(unittest.TestCase):
    """TE14 to TE21. With a disk."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test_convert_")
        self.conversion = swappModelConversion()
        self.destination = a_writable_format(True, "multi_tiers_support")
        self.paths = list()
        for name in ("a", "b", "c"):
            path = os.path.join(self.root, name + ".xra")
            sppasTrsRW(path).write(one_tier())
            self.paths.append(path)
        self.batch = a_batch(self.paths)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te14_one_result_per_file_in_the_order_of_the_batch(self):
        """TE14. One, and in that order. T06"""
        expected = names_in(self.batch)
        results = self.conversion.convert(self.batch, self.destination,
                                          dict(), dict())

        converted = list()
        for result in results:
            converted.append(result.file)
        self.assertEqual(expected, converted)

    # -----------------------------------------------------------------------

    def test_te15_the_failure_of_one_never_interrupts_the_others(self):
        """TE15. The files after it have their results. C13"""
        broken = os.path.join(self.root, "broken.xra")
        with open(broken, "w") as fp:
            fp.write("this is not a transcription")
        batch = a_batch([self.paths[0], broken, self.paths[1]])

        results = self.conversion.convert(batch, self.destination,
                                          dict(), dict())

        self.assertEqual(3, len(results))
        statuses = dict()
        for result in results:
            statuses[result.file] = result.status
        self.assertEqual("refused", statuses[broken])
        self.assertIn(statuses[self.paths[0]], ("written", "written with remarks"))
        self.assertIn(statuses[self.paths[1]], ("written", "written with remarks"))

    # -----------------------------------------------------------------------

    def test_te16_no_file_of_the_batch_removed_or_rewritten(self):
        """TE16. What was added to the workspace handed is what was produced,
        and nothing else. C11

        """
        before = dict()
        for path in self.paths:
            before[path] = os.path.getmtime(path)

        self.conversion.convert(self.batch, self.destination, dict(), dict())

        for path in before:
            self.assertTrue(os.path.exists(path))
            self.assertEqual(before[path], os.path.getmtime(path))

        added = list()
        for name in names_in(self.batch):
            if name not in self.paths:
                added.append(name)
        produced = list()
        for path in self.paths:
            produced.append(os.path.splitext(path)[0] + self.destination)
        self.assertEqual(sorted(produced), sorted(added))

    # -----------------------------------------------------------------------

    def test_te17_a_file_whose_output_exists(self):
        """TE17. Skipped, unless override allows replacing it. C17"""
        output = os.path.splitext(self.paths[0])[0] + self.destination
        with open(output, "w") as fp:
            fp.write("what was there before")

        results = self.conversion.convert(a_batch([self.paths[0]]), self.destination,
                                          dict(), {"override": False})
        self.assertEqual("skipped", results[0].status)
        with open(output) as fp:
            self.assertEqual("what was there before", fp.read())

        results = self.conversion.convert(a_batch([self.paths[0]]), self.destination,
                                          dict(), {"override": True})
        self.assertIn(results[0].status, ("written", "written with remarks"))

    # -----------------------------------------------------------------------

    def test_te18_a_typed_cause_is_attempted_once_more_and_no_third_time(self):
        """TE18. One second pass only. C16"""
        destination = a_writable_format(False, "multi_tiers_support")
        path = os.path.join(self.root, "several.xra")
        sppasTrsRW(path).write(several_tiers(3))

        with patch.object(sppasTrsRW, "write",
                          side_effect=sppasTrsRW.write, autospec=True) as wrote:
            self.conversion.convert(a_batch([path]), destination,
                                    {"multi_tiers": "one file per tier"}, dict())
            self.assertLessEqual(wrote.call_count, 2)

    # -----------------------------------------------------------------------

    def test_te19_a_refused_file_carries_a_cause_in_her_words(self):
        """TE19. The cause names what was in her file, not what is in the
        format. C18

        """
        destination = a_writable_format(False, "point_support")
        path = os.path.join(self.root, "points.xra")
        sppasTrsRW(path).write(one_tier(points=True))

        results = self.conversion.convert(a_batch([path]), destination,
                                          {"point": "skip the tier"}, dict())

        self.assertEqual("refused", results[0].status)
        self.assertTrue(len(results[0].cause) > 0)
        self.assertNotIn("Error", results[0].cause)
        self.assertNotIn("Aio", results[0].cause)

    # -----------------------------------------------------------------------

    def test_te20_what_a_failed_write_left_is_not_removed(self):
        """TE20. It asserts that something is left behind, and it is written
        that way on purpose: a renouncement which is not tested becomes a bug
        somebody fixes. C23

        """
        output = os.path.splitext(self.paths[0])[0] + self.destination
        with open(output, "w") as fp:
            fp.write("half of something")

        with patch.object(sppasTrsRW, "write", side_effect=IOError("no room")):
            self.conversion.convert(a_batch([self.paths[0]]), self.destination,
                                    dict(), {"override": True})

        self.assertTrue(os.path.exists(output))
        with open(output) as fp:
            self.assertEqual("half of something", fp.read())

    # -----------------------------------------------------------------------

    def test_te21_one_file_may_produce_several(self):
        """TE21. And it has one result all the same. C19"""
        destination = a_writable_format(False, "multi_tiers_support")
        path = os.path.join(self.root, "several.xra")
        sppasTrsRW(path).write(several_tiers(3))

        results = self.conversion.convert(
            a_batch([path]), destination, {"multi_tiers": "one file per tier"}, dict())

        self.assertEqual(1, len(results))
        self.assertIn(results[0].status, ("written", "written with remarks"))
        produced = list()
        for name in os.listdir(self.root):
            if name.endswith(destination) is True:
                produced.append(name)
        self.assertEqual(3, len(produced))

# ---------------------------------------------------------------------------


class TestModelProvision(unittest.TestCase):
    """TE22, TE23, TE26 and TE27. Against the provision of files."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test_convert_")
        self.parent = HTMLTree("test_convert").body_main.identifier
        self.person = swappWorkspaceFiles()
        self.manager = swappFilesManager(self.parent, self.person)
        self.files = list()
        for name in ("a.xra", "b.xra"):
            path = os.path.join(self.root, name)
            sppasTrsRW(path).write(one_tier())
            self.manager.consumes({"designate": path})
            self.files.append(path)
        self.provision = swappModelProvision(self.manager)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    @staticmethod
    def names_of(workspace) -> list:
        """Give the names of every file of a workspace, sorted.

        :param workspace: (sppasWorkspace) Workspace to be read
        :return: (list of str) Names of the files, with their path

        """
        names = list()
        for path in workspace.get_paths():
            for root in path:
                for one in root:
                    names.append(one.get_id())

        return sorted(names)

    # -----------------------------------------------------------------------

    def test_te22_the_batch_is_the_workspace_the_provision_hands(self):
        """TE22. Empty when nothing is checked, and the workspace of the
        person has not moved. C11

        """
        batch = self.provision.batch()
        self.assertEqual(sorted(self.files), TestModelProvision.names_of(batch))

        nothing = swappModelProvision(swappFilesManager(self.parent))
        self.assertEqual(list(), TestModelProvision.names_of(nothing.batch()))

        batch.remove_file(self.files[0])
        self.assertEqual(sorted(self.files),
                         TestModelProvision.names_of(self.person.workspace()))

    # -----------------------------------------------------------------------

    def test_te23_what_was_produced_is_given_back(self):
        """TE23. In the workspace it handed: the provision of files knows it
        afterwards, and hands it as a file to be treated. C22

        """
        batch = self.provision.batch()
        produced = os.path.join(self.root, "a.TextGrid")
        sppasTrsRW(produced).write(one_tier())
        batch.add_file(produced)

        self.provision.produced(batch)

        self.assertIn(produced, TestModelProvision.names_of(self.manager.files_for_app()))

    # -----------------------------------------------------------------------

    def test_te26_the_batch_is_locked_while_it_is_converted(self):
        """TE26. And none of its files is still locked once the batch has
        been treated. T06

        """
        self.provision.lock(self.files)
        self.assertEqual(2, len(self.person.locked_files()))

        self.provision.release(self.files)
        self.assertEqual(0, len(self.person.locked_files()))

        self.provision.lock(self.files)
        self.provision.finished()
        self.assertEqual(0, len(self.person.locked_files()))

    # -----------------------------------------------------------------------

    def test_te27_that_the_batch_has_been_treated_is_said(self):
        """TE27. Whatever the results: nothing was produced here. T06"""
        self.provision.finished()
        self.manager.populate_view()

        self.assertIn(MSG_FINISHED, self.manager.container().serialize())

# ---------------------------------------------------------------------------


class TestConvertModel(unittest.TestCase):
    """TE24 and TE25. The façade."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test_convert_")
        parent = HTMLTree("test_convert").body_main.identifier
        self.model = swappConvertModel(swappFilesManager(parent))
        self.destination = a_writable_format(True, "multi_tiers_support")
        self.path = os.path.join(self.root, "a.xra")
        sppasTrsRW(self.path).write(one_tier())

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # -----------------------------------------------------------------------

    def test_te24_it_converts_only_when_everything_is_there(self):
        """TE24. A destination, a batch which is not empty, and an answer
        standing for every option. C12

        """
        with self.assertRaises(ValueError):
            self.model.convert(sppasWorkspace(), self.destination, dict(), dict())

        with self.assertRaises(ValueError):
            self.model.convert(a_batch([self.path]), "", dict(), dict())

        results = self.model.convert(a_batch([self.path]), self.destination,
                                     dict(), dict())
        self.assertEqual(1, len(results))

    # -----------------------------------------------------------------------

    def test_te25_the_options_are_given_before_anything_is_read(self):
        """TE25. The same answer whatever the batch holds: the options and the
        structural loss depend on the destination alone. C6, C7

        """
        options = self.model.options_of(self.destination)
        lost = self.model.structural_loss_of(self.destination)

        other = os.path.join(self.root, "other.xra")
        sppasTrsRW(other).write(several_tiers(4))

        self.assertEqual(options, self.model.options_of(self.destination))
        self.assertEqual(lost, self.model.structural_loss_of(self.destination))

# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
