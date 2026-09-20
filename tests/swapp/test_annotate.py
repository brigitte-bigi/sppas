# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.test_annotate.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Unittests of the app which runs the automatic annotations.

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

    TE1 to TE20 of the dossier "Annotate - an app of SPPAS". Six of them need
    nothing at all: they check how the chosen annotations are arranged, which
    is the one thing this application works out on its own. Seven read what
    annotations written here declare. The seven others start a run, and what
    runs it is written here as well: no annotation of SPPAS is ever run, and
    the domain which runs them is not what is tested.

"""

from __future__ import annotations
import json
import os
import shutil
import tempfile
import time
import unittest

from sppas.core.config import paths
from sppas.src.annotations.param import annotationParam

from sppas.ui.swapp.app_annotate import annotate_model
from sppas.ui.swapp.app_annotate.annotate_model import swappAnnotateModel

# ---------------------------------------------------------------------------


def make_annotation(where: str, key: str, requires=None, anntype=None,
                    resource: str | None = None, api: str | None = "TestAnn",
                    langs=True) -> str:
    """Write the declaration of an annotation, and give its file name.

    :param where: (str) A folder of its own.
    :param key: (str) Identifier of the annotation.
    :param requires: (list|None) What it declares it requires.
    :param anntype: (list|None) Its types, to declare none.
    :param resource: (str|None) A path under the resources, to declare one.
    :param api: (str|None) The class to instantiate, None to declare none.
    :param langs: (bool) Whether that resource is a language resource.

    """
    conf = {
        "id": key,
        "name": "Annotation " + key,
        "descr": "What " + key + " says of itself.",
        "options": [],
        "resources": []
    }
    if api is not None:
        conf["api"] = api
    if anntype is not None:
        conf["anntype"] = anntype
    if requires is not None:
        conf["required"] = requires
    if resource is not None:
        conf["resources"] = [{"type": "file", "path": resource,
                              "name": "", "ext": ".txt", "lang": langs}]

    filename = os.path.join(where, key + ".json")
    with open(filename, "w") as fp:
        json.dump(conf, fp)
    return filename


def make_language(key: str) -> str:
    """Put a resource of a language where the annotations look for one.

    Give back the path to declare, relative to the resources, and the caller
    removes the folder it made.

    """
    folder = os.path.join(paths.resources, "test_annotate_" + str(os.getpid()))
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, key + ".txt"), "w") as fp:
        fp.write("")
    return os.path.basename(folder)


def remove_languages() -> None:
    """Take back what make_language put there."""
    folder = os.path.join(paths.resources, "test_annotate_" + str(os.getpid()))
    shutil.rmtree(folder, ignore_errors=True)


# ---------------------------------------------------------------------------


class ManagerForTests:
    """What runs the annotations, written here.

    It takes what it is handed, says where it is into what it was given for
    that, takes its time, and writes a report. It runs no annotation.

    """

    def __init__(self, seconds: float = 0., fails: str | None = None):
        self.seconds = seconds
        self.fails = fails
        self.handed = None          # the parameters it was handed
        self.activated = None       # which annotations were activated in them
        self.reached_the_end = False
        self.merged = False

    def set_do_merge(self, do_merge):
        self.merged = bool(do_merge)

    def annotate(self, parameters, progress=None):
        self.handed = parameters
        self.activated = [parameters.get_step_key(i)
                          for i in range(parameters.get_step_numbers())
                          if parameters.get_step_status(i) is True]

        report = parameters.get_report_filename()
        with open(report, "w") as fp:
            for key in self.activated:
                if progress is not None:
                    progress.set_new()
                    progress.set_header(key)
                    progress.set_fraction(0.)
                if self.seconds > 0.:
                    time.sleep(self.seconds)
                if key == self.fails:
                    fp.write(key + ": refused\n")
                else:
                    fp.write(key + ": done\n")
                if progress is not None:
                    progress.set_fraction(1.)
        self.reached_the_end = True


# ---------------------------------------------------------------------------


class TestArranged(unittest.TestCase):
    """TE1 to TE6. Nothing is installed and nothing is read.

    What is checked is how the chosen annotations are arranged so that what
    depends on what can be seen. It changes no run: the order a run happens
    in is the one the domain of the annotations declares.

    """

    def test_te1_what_comes_back_is_what_was_chosen(self):
        """TE1. Not one annotation added, not one removed."""
        chosen = ["alignment", "textnorm", "phonetize"]
        arranged = swappAnnotateModel.arranged(chosen, dict())

        self.assertEqual(sorted(chosen), sorted(arranged))
        self.assertEqual(len(chosen), len(arranged))

    # -----------------------------------------------------------------------

    def test_te2_after_what_it_requires(self):
        """TE2. An annotation is shown after every chosen one it requires. C4"""
        arranged = swappAnnotateModel.arranged(
            ["alignment", "phonetize"],
            {"alignment": ["phonetize"]})

        self.assertLess(arranged.index("phonetize"), arranged.index("alignment"))

    # -----------------------------------------------------------------------

    def test_te3_a_requirement_which_was_not_chosen(self):
        """TE3. The annotation is in the list all the same. C5"""
        arranged = swappAnnotateModel.arranged(
            ["alignment"],
            {"alignment": ["phonetize"]})

        self.assertEqual(["alignment"], arranged)

    # -----------------------------------------------------------------------

    def test_te4_a_chain_of_three(self):
        """TE4. Whatever order it was given in, the reverse included. C4"""
        requirements = {"phonetize": ["textnorm"], "alignment": ["phonetize"]}
        expected = ["textnorm", "phonetize", "alignment"]

        for given in (["textnorm", "phonetize", "alignment"],
                      ["alignment", "phonetize", "textnorm"],
                      ["phonetize", "alignment", "textnorm"]):
            self.assertEqual(expected,
                             swappAnnotateModel.arranged(given, requirements))

    # -----------------------------------------------------------------------

    def test_te5_a_requirement_which_names_nothing(self):
        """TE5. It changes nothing of the arrangement. C4

        The declarations are not all sound: one of them names a requirement
        which no annotation bears. What is arranged must not wait for it.

        """
        chosen = ["textnorm", "alignment"]
        requirements = {"alignment": ["nothing_bears_this_name"]}
        arranged = swappAnnotateModel.arranged(chosen, requirements)

        self.assertEqual(sorted(chosen), sorted(arranged))

    # -----------------------------------------------------------------------

    def test_te6_the_same_set_twice(self):
        """TE6. It is arranged the same way."""
        chosen = ["alignment", "textnorm", "phonetize", "syllabify"]
        requirements = {"phonetize": ["textnorm"],
                        "alignment": ["phonetize"],
                        "syllabify": ["alignment"]}

        once = swappAnnotateModel.arranged(chosen, requirements)
        twice = swappAnnotateModel.arranged(chosen, requirements)
        self.assertEqual(once, twice)


# ---------------------------------------------------------------------------


class TestWhatIsOffered(unittest.TestCase):
    """TE7 to TE13. Annotations written here are read, and no run is started."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test_annotate_")
        self.model = swappAnnotateModel()
        self.model.parameters().annotations = list()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
        remove_languages()

    def offer(self, *filenames):
        """Make the annotations of those declarations the ones offered."""
        self.model.parameters().annotations = \
            [annotationParam(f) for f in filenames]

    # -----------------------------------------------------------------------

    def test_te7_every_annotation_which_is_declared(self):
        """TE7. And no other. B1"""
        self.offer(make_annotation(self.root, "one"),
                   make_annotation(self.root, "two"))

        offered = self.model.parameters()
        self.assertEqual(2, offered.get_step_numbers())
        self.assertEqual(["one", "two"],
                         sorted(offered.get_step_key(i) for i in range(2)))

    # -----------------------------------------------------------------------

    def test_te8_what_is_given_of_an_annotation(self):
        """TE8. What it declares, and nothing this application wrote. C14, B3"""
        self.offer(make_annotation(self.root, "one"))

        step = self.model.parameters().get_step(0)
        self.assertEqual("Annotation one", step.get_name())
        self.assertEqual("What one says of itself.", step.get_descr())
        self.assertEqual([], step.get_reference_identifiers())

    # -----------------------------------------------------------------------

    def test_te9_an_annotation_which_declares_nothing_to_run(self):
        """TE9. It cannot be chosen, and it is given all the same."""
        self.offer(make_annotation(self.root, "one", api=None))

        param = self.model.parameters()
        self.assertEqual(1, param.get_step_numbers())

        param.activate_annotation("one")
        self.assertFalse(param.get_step_status(0))

    # -----------------------------------------------------------------------

    def test_te10_an_annotation_which_declares_no_type(self):
        """TE10. It takes one file on its own. C16"""
        self.offer(make_annotation(self.root, "one"))

        self.assertEqual(["STANDALONE"], self.model.parameters().get_step_types(0))

    # -----------------------------------------------------------------------

    def test_te11_the_languages_of_an_annotation(self):
        """TE11. Those whose resources stand on the machine. C17"""
        if os.access(paths.resources, os.W_OK) is False:
            self.skipTest("The resources cannot be written where they stand.")

        folder = make_language("fra")
        self.offer(make_annotation(self.root, "speaks", resource=folder),
                   make_annotation(self.root, "silent"))

        param = self.model.parameters()
        self.assertEqual(["fra"], param.get_langlist(0))
        self.assertEqual([], param.get_langlist(1))

    # -----------------------------------------------------------------------

    def test_te12_a_language_an_annotation_does_not_speak(self):
        """TE12. It is taken out of what can be chosen. C3"""
        if os.access(paths.resources, os.W_OK) is False:
            self.skipTest("The resources cannot be written where they stand.")

        folder = make_language("fra")
        self.offer(make_annotation(self.root, "speaks", resource=folder))

        param = self.model.parameters()
        param.set_lang("eng")

        param.activate_annotation("speaks")
        self.assertFalse(param.get_step_status(0))

    # -----------------------------------------------------------------------

    def test_te13_what_an_annotation_requires(self):
        """TE13. Read from its declaration. C15, B13

        It fails until the field is read: what an annotation requires is
        declared and never loaded, and this test is what says whether the
        extension of the annex was made.

        """
        self.offer(make_annotation(self.root, "needs", requires=["other"]),
                   make_annotation(self.root, "needs_nothing"))

        self.assertEqual(["other"], self.model.requires("needs"))
        self.assertEqual([], self.model.requires("needs_nothing"))


# ---------------------------------------------------------------------------


class TestWithARun(unittest.TestCase):
    """TE14 to TE20. A run is started, and what runs it is written here.

    No annotation of SPPAS is run. What is checked is what was handed over,
    that nothing waited for it, and what was done with what came back.

    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test_annotate_")
        self.manager = ManagerForTests()
        self.was = annotate_model.sppasAnnotationsManager
        annotate_model.sppasAnnotationsManager = lambda: self.manager

        self.model = swappAnnotateModel()
        self.model.parameters().annotations = [
            annotationParam(make_annotation(self.root, "one")),
            annotationParam(make_annotation(self.root, "two"))]

    def tearDown(self):
        annotate_model.sppasAnnotationsManager = self.was
        shutil.rmtree(self.root, ignore_errors=True)

    def files_to_annotate(self):
        """Give a workspace holding one file, as the provision of files does."""
        name = os.path.join(self.root, "a_file.wav")
        with open(name, "w") as fp:
            fp.write("")
        return name

    def a_run_of_one(self):
        """Start a run of one annotation on one file."""
        self.model.set_workspace(self.files_to_annotate())
        self.model.parameters().activate_annotation("one")
        return self.model.start()

    # -----------------------------------------------------------------------

    def test_te14_what_is_handed_over(self):
        """TE14. Every annotation which was chosen, and no other. C1, C10"""
        self.model.set_workspace(self.files_to_annotate())
        self.model.parameters().activate_annotation("two")
        self.model.start()
        while self.model.is_running() is True:
            time.sleep(0.01)

        self.assertEqual(["two"], self.manager.activated)
        self.assertIs(self.model.parameters(), self.manager.handed)

    # -----------------------------------------------------------------------

    def test_te15_starting_a_run_does_not_wait_for_it(self):
        """TE15. And the run goes on after the answer. RO1"""
        self.manager.seconds = .4
        self.model.set_workspace(self.files_to_annotate())
        self.model.parameters().activate_annotation("one")

        started = time.time()
        self.model.start()
        answered = time.time() - started

        self.assertLess(answered, .2)
        self.assertTrue(self.model.is_running())

        while self.model.is_running() is True:
            time.sleep(0.01)
        self.assertTrue(self.manager.reached_the_end)

    # -----------------------------------------------------------------------

    def test_te16_an_annotation_which_fails_stops_nothing(self):
        """TE16. The run reaches its end and the report holds both. C6, C7"""
        self.manager.fails = "one"
        self.model.set_workspace(self.files_to_annotate())
        self.model.parameters().activate_annotation("one")
        self.model.parameters().activate_annotation("two")
        self.model.start()
        while self.model.is_running() is True:
            time.sleep(0.01)

        self.assertTrue(self.manager.reached_the_end)
        held = self.model.read_report(self.model.the_run().report)
        self.assertIn("one: refused", held)
        self.assertIn("two: done", held)

    # -----------------------------------------------------------------------

    def test_te17_a_second_run_while_one_is_going(self):
        """TE17. It is refused, and the refusal says which one is going. C8"""
        self.manager.seconds = .4
        self.a_run_of_one()

        with self.assertRaises(RuntimeError) as refusal:
            self.model.start()
        self.assertIn(str(self.model.the_run().run), str(refusal.exception))

        while self.model.is_running() is True:
            time.sleep(0.01)

    # -----------------------------------------------------------------------

    def test_te18_an_annotation_set_again_while_the_run_goes(self):
        """TE18. It does not change what that run is running with. C9"""
        self.manager.seconds = .4
        self.a_run_of_one()
        started_with = self.model.the_run().parameters

        self.model.parameters().activate_annotation("two")

        self.assertEqual(["one"],
                         [started_with.get_step_key(i)
                          for i in range(started_with.get_step_numbers())
                          if started_with.get_step_status(i) is True])

        while self.model.is_running() is True:
            time.sleep(0.01)

    # -----------------------------------------------------------------------

    def test_te19_where_a_run_stands(self):
        """TE19. What the domain of the annotations said, and nothing else. B8"""
        self.assertIsNone(self.model.where_it_stands())

        self.manager.seconds = .4
        self.a_run_of_one()
        time.sleep(.2)

        stands = self.model.where_it_stands()
        self.assertEqual("one", stands.get_header())

        while self.model.is_running() is True:
            time.sleep(0.01)

    # -----------------------------------------------------------------------

    def test_te20_what_is_given_back_when_the_run_is_over(self):
        """TE20. The files which were written and the report, once. T08"""
        given_back = list()
        self.model.give_back = lambda files: given_back.append(list(files))

        self.a_run_of_one()
        while self.model.is_running() is True:
            time.sleep(0.01)
        self.model.the_run()

        self.assertEqual(1, len(given_back))
        self.assertIn(self.model.the_run().report, given_back[0])


# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
