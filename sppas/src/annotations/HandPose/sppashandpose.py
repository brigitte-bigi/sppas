# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.HandPose.sppashandpose.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS integration of the automatic annotation Hand&Pose.

.. _This file is part of SPPAS: https://sppas.org/
..
    ---------------------------------------------------------------------

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

    ---------------------------------------------------------------------

"""

import logging
import os

from sppas.core.config import annots
from sppas.src.imgdata import sppasImage
from sppas.src.imgdata import image_extensions
from sppas.src.videodata import video_extensions

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoInputError
from ..baseannot import sppasBaseAnnotation
from ..autils import sppasFiles

from .imgsightswriter import sppasHandsSightsImageWriter
from .mphanddetect import MediaPipeHandPoseDetector
from .videosightswriter import sppasSightsVideoWriter
from .videohandpose import VideoHandPoseDetector
from .videohandpose import HandPoseMode

# ---------------------------------------------------------------------------


class sppasHandPose(sppasBaseAnnotation):
    """SPPAS integration of the automatic Mediapipe Hand & Body Pose annotations.

    Requires an image/video.

    """

    def __init__(self, log=None):
        """Create a new sppasHandPose instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasHandPose, self).__init__("handpose.json", log)

        # Hand and pose detection in an image
        self.__hdi = MediaPipeHandPoseDetector()
        self.__img_writer = sppasHandsSightsImageWriter()

        # Hand and pose detection in a video
        self.__hdv = VideoHandPoseDetector(self.__hdi)
        self.__video_writer = sppasSightsVideoWriter(self.__img_writer)

    # -----------------------------------------------------------------------

    def load_resources(self, *args, **kwargs):
        """Fix the model files.

        :param args: (str) Filenames of the hand and the pose landmarker models.

        """
        self.__hdi.load_model(*args)

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if key == "hand":
                self.enable_hand(opt.get_value())

            elif key == "pose":
                self.enable_pose(opt.get_value())

            elif key == "csv":
                self.set_out_csv(opt.get_value())

            elif key == "tag":
                self.set_img_tag(opt.get_value())

            elif key == "folder":
                self.set_out_folder(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------
    # Getters and Setters
    # -----------------------------------------------------------------------

    def enable_hand(self, value=True):
        """The result includes hand detection.

        If set to False, pose detection is automatically enabled.
        If set to True, pose detection remains the same.

        :param value: (bool) Enable hand detection

        """
        v = bool(value)
        self._options["hand"] = v
        if v is False:
            self._options["pose"] = True

    # ----------------------------------------------------------------------

    def enable_pose(self, value=True):
        """The result includes pose detection.

        If set to False, hand detection is automatically enabled.
        If set to True, hand detection remains the same.

        :param value: (bool) Enable pose detection

        """
        v = bool(value)
        self._options["pose"] = v
        if v is False:
            self._options["hand"] = True

    # ----------------------------------------------------------------------

    def set_out_csv(self, out_csv=False):
        """The result includes a CSV file.

        :param out_csv: (bool) Create a CSV file with the coordinates

        """
        out_csv = bool(out_csv)
        self.__video_writer.set_options(csv=out_csv)
        self._options["csv"] = out_csv

        self.__video_writer.set_options(xra=not out_csv)
        self._options["xra"] = not out_csv

    # ----------------------------------------------------------------------

    def set_img_tag(self, value=True):
        """Draw the landmark points to the image.

        :param value: (bool) Tag the images

        """
        value = bool(value)
        self.__img_writer.set_options(tag=value)
        self.__video_writer.set_options(tag=value)
        self._options["tag"] = value

    # -----------------------------------------------------------------------

    def set_out_folder(self, out_folder=False):
        """The result includes a folder with image files -- if video input.

        :param out_folder: (bool) Create a folder with image files when detecting

        """
        out_folder = bool(out_folder)
        self.__video_writer.set_options(folder=out_folder)
        self._options["folder"] = out_folder

    # ----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def image_hand_sights(self, image_file, output=None):
        """Get the image, detect hands and write results.

        :param image_file: (str) Image filename
        :param output: (str) The output name for the image

        :return: (list of list) the sights of all detected hands or created filenames

        """
        # Get the image from the input
        image = sppasImage(filename=image_file)
        all_hands = list()

        # Search for the hands only or pose + hands
        if self._options["hand"] is True:
            if self._options["pose"] is False:
                success = self.__hdi.detect_hands(image)
            else:
                success = self.__hdi.detect(image)

            if success is True:
                if self.logfile:
                    self.logfile.print_message("{:d} hands found".format(len(self.__hdi), indent=2, status=annots.info))
                # Get the output list of sights
                for hand_idx in range(len(self.__hdi)):
                    sights = self.__hdi.get_hand_sights(hand_idx)
                    all_hands.append(sights)
            else:
                if self.logfile:
                    self.logfile.print_message("No hand found", indent=2, status=annots.info)

        # Search for the pose only
        if self._options["hand"] is False and self._options["pose"] is True:
            success = self.__hdi.detect_poses(image)
            if success is True:
                # Get the output list of sights
                sights = self.__hdi.get_pose_sights()
                all_hands.append(sights)
            else:
                if self.logfile:
                    self.logfile.print_message("No hand found", indent=2, status=annots.info)

        # Save result as a list of sights (csv) and/or a tagged image
        if output is not None and len(all_hands) > 0:
            output_file = self.fix_out_file_ext(output, out_format="IMAGE")
            new_files = self.__img_writer.write(image, all_hands, output_file, pattern="")
            return new_files

        return all_hands

    # -----------------------------------------------------------------------

    def video_hand_sights(self, video_file, output=None):
        """Get the video, detect hands and write results.

        :param video_file: (str) Video filename
        :param output: (str) The output name for the video
        :return: (list of list) the sights of all detected hands or created filenames

        """
        result_files = list()
        # Search for the hands only or pose + hands. Result is hand's sights.
        if self._options["hand"] is True:
            if self._options["pose"] is False:
                self.__hdv.set_mode(HandPoseMode().HAND)
            else:
                self.__hdv.set_mode(HandPoseMode().BOTH)
            result_files = self.__hdv.video_hand_sights(video_file, self.__video_writer, output)

        # Search for the pose only
        if self._options["hand"] is False and self._options["pose"] is True:
            self.__hdv.set_mode(HandPoseMode().POSE)
            result_files = self.__hdv.video_hand_sights(video_file, self.__video_writer, output)

        return result_files

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the media.

        :param input_files: (list)
        :raise: NoInputError
        :return: (str) Names of the expected file

        """
        ext = self.get_input_extensions()
        media_ext = ext[0]
        media = None
        for filename in input_files:
            _, fe = os.path.splitext(filename)
            if media is None and fe in media_ext:
                # The video or the image is found.
                media = filename

        if media is None:
            logging.error("Neither a video nor an image was found.")
            raise NoInputError

        return media

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        :param input_files: (list of str) Input file is an image or a video
        :param output: (str) the output file name
        :return: (list of points or filenames) detected sights of hands or created filenames

        """
        media_file = self.get_inputs(input_files)

        # Input is either a video or an image
        _, ext = os.path.splitext(media_file)
        self.__video_writer.set_image_extension(self._out_extensions["IMAGE"])
        self.__video_writer.set_video_extension(self._out_extensions["VIDEO"])

        result_files = list()
        if ext in video_extensions:
            try:
                result_files = self.video_hand_sights(media_file, output)
                self.__video_writer.close()
            except:
                import traceback
                print(traceback.format_exc())
                raise

        if ext in image_extensions:
            try:
                result_files = self.image_hand_sights(media_file, output)
            except:
                import traceback
                print(traceback.format_exc())
                raise

        return result_files

    # -----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-hands")

    # -----------------------------------------------------------------------

    def get_input_patterns(self):
        """Pattern this annotation expects for its input filename."""
        return [
            self._options.get("inputpattern1", "")
            ]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename.

        Priority is given to video files, then image files.

        """
        out_ext = list(sppasFiles.get_informat_extensions("VIDEO"))
        for img_ext in sppasFiles.get_informat_extensions("IMAGE"):
            out_ext.append(img_ext)
        return [out_ext]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_filetypes() -> list:
        """Types of file the annotation expects for its inputs, one list per input.

        The types are those of sppasFiles, and the inputs are in the order of
        get_input_extensions().

        :return: (list of list of str)

        """
        return [["VIDEO", "IMAGE"]]
