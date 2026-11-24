# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceIdentity.sppasfaceid.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  SPPAS integration of FaceIdentity automatic annotation

.. _This file is part of SPPAS: <https://sppas.org/>
..
    -------------------------------------------------------------------------

     ######   ########   ########      ###      ######
    ##    ##  ##     ##  ##     ##    ## ##    ##    ##     the automatic
    ##        ##     ##  ##     ##   ##   ##   ##            annotation
     ######   ########   ########   ##     ##   ######        and
          ##  ##         ##         #########        ##        analysis
    ##    ##  ##         ##         ##     ##  ##    ##         of speech
     ######   ##         ##         ##     ##   ######

    Copyright (C) 2011-2022  Brigitte Bigi, CNRS
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

import os
import logging
import traceback

from ..annotationsexc import AnnotationOptionError
from ..baseannot import sppasBaseAnnotation
from ..autils import sppasFiles
from ..annotationsexc import NoInputError

from .identifycoords import VideoCoordsIdentification
from .kidswriter import sppasKidsVideoWriter

# ---------------------------------------------------------------------------


class sppasFaceIdentifier(sppasBaseAnnotation):
    """SPPAS integration of the automatic video coordinates identification.

    Requires both an image/video and a CSV file with face coordinates.

    """

    def __init__(self, log=None):
        """Create a new sppasFaceIdentifier instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasFaceIdentifier, self).__init__("faceidentity.json", log)

        # The objects to store the input data and the results
        self.__video_writer = sppasKidsVideoWriter()

        # The annotator
        self.__pfv = VideoCoordsIdentification()

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if key == "fdmin":
                self.set_face_min_confidence(opt.get_value())

            elif key == "mincoords":
                self.set_compare_coords_min_threshold(opt.get_value())

            elif key == "minrefcoords":
                self.set_compare_coords_ref_min_threshold(opt.get_value())

            elif key == "mindistcoords":
                self.set_coords_min_dist(opt.get_value())

            elif key == "mindistimgs":
                self.set_images_min_dist(opt.get_value())

            elif key == "nbfrimg":
                self.set_nb_images_recognizer(opt.get_value())

            elif key == "ident":
                self.set_ident_export(opt.get_value())

            elif key == "selfi":
                self.set_ident_export_selfi(opt.get_value())

            elif key == "shift":
                self.set_ident_export_shift(opt.get_value())

            elif key == "csv":
                self.set_out_csv(opt.get_value())

            elif key == "folder":
                self.set_out_folder(opt.get_value())

            elif key == "tag":
                self.set_img_tag(opt.get_value())

            elif key == "crop":
                self.set_img_crop(opt.get_value())

            elif key == "width":
                self.set_img_width(opt.get_value())

            elif key == "height":
                self.set_img_height(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # ----------------------------------------------------------------------
    # Getters and setters
    # -----------------------------------------------------------------------

    def set_face_min_confidence(self, value):
        """Threshold to FD confidence to make a face a kid candidate.

        :param value: (float) threshold for the confidence score of coords

        """
        self.__pfv.set_face_min_confidence(value)
        self._options["fdmin"] = value

    # -----------------------------------------------------------------------

    def set_compare_coords_min_threshold(self, value):
        """Fix the minimum comparison score to select a coord as kid candidate.

        :param value: (float) threshold for the comparison score of coords

        """
        self.__pfv.set_compare_coords_min_threshold(value)
        self._options["mincoords"] = value

    # -----------------------------------------------------------------------

    def set_compare_coords_ref_min_threshold(self, value):
        """Fix the minimum comparison score to add a coord as reference.

        :param value: (float) threshold for the comparison score of coords

        """
        self.__pfv.set_compare_coords_ref_min_threshold(value)
        self._options["minrefcoords"] = value

    # -----------------------------------------------------------------------

    def set_coords_min_dist(self, value):
        """Fix the minimum distance of coords between 2 candidate kids.

        :param value: (float) threshold for the distance of coords

        """
        self.__pfv.set_coords_min_dist(value)
        self._options["mindistcoords"] = value

    # -----------------------------------------------------------------------

    def set_images_min_dist(self, value):
        """Fix the minimum distance of images between 2 candidate kids.

        :param value: (float) threshold for the distance of images

        """
        self.__pfv.set_images_min_dist(value)
        self._options["mindistimgs"] = value

    # -----------------------------------------------------------------------

    def set_nb_images_recognizer(self, value):
        """Number of images to store to train a recognizer of a kid.

        Default value is 20. Value must range (0; 100).

        :param value: (int) Number of image to represent a kid

        """
        self.__pfv.set_nb_images_recognizer(value)
        self._options["nbfrimg"] = value

    # -----------------------------------------------------------------------

    def set_ident_export(self, value):
        """Set the export of a portrait video and csv/xra file for each kid.

        :param value: (bool) True to export video/csv files

        """
        self.__pfv.set_out_ident(value)
        self._options["ident"] = value

    # -----------------------------------------------------------------------

    def set_ident_export_shift(self, value):
        """Exported portrait video and csv/xra file for each kid are shifted.

        :param value: (int) Percentage of shift (Negative: left, Positive: right)

        """
        self.__pfv.set_out_shift(value)
        self._options["shift"] = value

    # -----------------------------------------------------------------------

    def set_ident_export_selfi(self, value):
        """Set the export of a selfi video and csv/xra file for each kid.

        :param value: (bool) True to export video/csv files

        """
        value = bool(value)
        self.__pfv.set_out_selfi(value)
        if value is True:
            self._options["ident"] = True
        self._options["selfi"] = value

    # -----------------------------------------------------------------------

    def set_out_csv(self, out_csv=False):
        """The result includes a CSV file instead of XRA.

        :param out_csv: (bool) Create a CSV file when detecting

        """
        self.__video_writer.set_options(csv=out_csv)
        self._options["csv"] = out_csv

        self.__video_writer.set_options(xra=not out_csv)
        self._options["xra"] = not out_csv

    # -----------------------------------------------------------------------

    def set_out_folder(self, out_folder=False):
        """The result includes a folder with image files.

        :param out_folder: (bool) Create a folder with image files when detecting

        """
        self.__video_writer.set_options(folder=out_folder)
        self._options["folder"] = out_folder

    # -----------------------------------------------------------------------

    def set_img_tag(self, value=True):
        """Surround the faces with a square.

        :param value: (bool) Tag the images

        """
        self.__video_writer.set_options(tag=value)
        self._options["tag"] = value

    # -----------------------------------------------------------------------

    def set_img_crop(self, value=True):
        """Create an image/video for each detected person.

        :param value: (bool) Crop the images

        """
        self.__video_writer.set_options(crop=value)
        self._options["crop"] = value

    # -----------------------------------------------------------------------

    def set_img_width(self, value):
        """Width of the resulting images/video.

        :param value: (int) Number of pixels

        """
        self.__video_writer.set_options(width=value)
        self._options["width"] = value

    # -----------------------------------------------------------------------

    def set_img_height(self, value):
        """Height of the resulting images/video.

        :param value: (int) Number of pixel

        """
        self.__video_writer.set_options(height=value)
        self._options["height"] = value

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the media and the csv filenames.

        :param input_files: (list)
        :raise: NoInputError
        :return: (str, str) Names of the 2 expected files

        """
        ext = self.get_input_extensions()
        media_ext = ext[0]
        annot_ext = ext[1]
        media = None
        annot = None
        for filename in input_files:
            fn, fe = os.path.splitext(filename)
            if media is None and fe in media_ext:
                # The video or the image is found.
                media = filename
            elif annot is None and fe.lower() in annot_ext:
                annot = filename

        if media is None:
            logging.error("No video was found.")
            raise NoInputError

        if annot is None:
            logging.error("The XRA or CSV file with faces was not found.")
            raise NoInputError

        return media, annot

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        :param input_files: (list of str) (video ) Video file, CSV file with coords of faces
        :param output: (str) the output base name for files
        :returns: (list) Either the list of list of detected faces or the list
        of all created files.

        """
        # Get and open the video filename from the input
        video_file, annot_file = self.get_inputs(input_files)
        self.__video_writer.set_video_extension(self._out_extensions["VIDEO"])

        # Assign a person identity to the faces
        if output.endswith(self.get_output_pattern()):
            output = output[:-len(self.get_output_pattern())]

        try:
            result = self.__pfv.video_identity(video_file, annot_file, self.__video_writer, output)
        except:
            import traceback
            logging.critical(traceback.format_exc())
            raise
        self.__video_writer.close()

        return result

    # -----------------------------------------------------------------------

    def get_input_patterns(self):
        """Patterns this annotation expects for its input filenames.

        """
        return [
            self._options.get("inputpattern1", ""),        # video
            self._options.get("inputpattern2", '-face')    # csv/xra
            ]

    # -----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation adds to the output filename."""
        return self._options.get("outputpattern", "-ident")

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename.

        """
        return [
            sppasFiles.get_informat_extensions("VIDEO"),
            [".xra", ".csv"]
            ]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_filetypes() -> list:
        """Types of file the annotation expects for its inputs, one list per input.

        The types are those of sppasFiles, and the inputs are in the order of
        get_input_extensions().

        :return: (list of list of str)

        """
        return [["VIDEO"], ["ANNOT_ANNOT"]]
