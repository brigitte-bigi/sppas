# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceSights.sppasfacesights.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  SPPAS integration of the automatic annotation FaceSights.

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

    ---------------------------------------------------------------------

"""

import logging
import os

from sppas.core.config import cfg
from sppas.core.coreutils import sppasEnableFeatureError
from sppas.core.coreutils import sppasError
from sppas.src.imgdata import sppasImage
from sppas.src.imgdata import image_extensions
from sppas.src.imgdata import sppasCoordsReader
from sppas.src.videodata import video_extensions

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoInputError
from ..baseannot import sppasBaseAnnotation
from ..autils import sppasFiles

from .imgfacemark import ImageFaceLandmark
from .imgsightswriter import sppasFaceSightsImageWriter
from .videofacemark import VideoFaceLandmark
from .kidsightswriter import sppasKidsSightsVideoWriter

# ---------------------------------------------------------------------------

ERR_NO_FACE = "No face detected in the image."

# ---------------------------------------------------------------------------


class sppasFaceSights(sppasBaseAnnotation):
    """SPPAS integration of the automatic face sights annotation.

    Requires both an image/video and an XRA or CSV file with faces or
    face identities.

    """

    def __init__(self, log=None):
        """Create a new sppasFaceSights instance.

        :param log: (sppasLog) Human-readable logs.

        """
        if cfg.feature_installed("facedetect") is False:
            raise sppasEnableFeatureError("facedetect")

        if cfg.feature_installed("facemark") is False:
            raise sppasEnableFeatureError("facemark")

        super(sppasFaceSights, self).__init__("facesights.json", log)
        
        # Face sights detection on an image
        self.__fli = ImageFaceLandmark()
        self.__img_writer = sppasFaceSightsImageWriter()

        # Face sights detection on a video
        self.__flv = VideoFaceLandmark(self.__fli)
        self.__video_writer = sppasKidsSightsVideoWriter(self.__img_writer)

    # -----------------------------------------------------------------------

    def load_resources(self, *args, **kwargs):
        """Fix the model and proto files.

        :param args: models for landmark (Kazemi/LBF/AAM)

        """
        for model in args:
            self.__fli.add_model(model)

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if key == "csv":
                self.set_out_csv(opt.get_value())

            elif key == "tag":
                self.set_img_tag(opt.get_value())

            elif key == "crop":
                self.set_img_crop(opt.get_value())

            elif key == "folder":
                self.set_out_folder(opt.get_value())

            elif key == "width":
                self.set_img_width(opt.get_value())

            elif key == "height":
                self.set_img_height(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------
    # Getters and Setters
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------

    def set_img_crop(self, value=True):
        """Create an image/video for each detected person.

        :param value: (bool) Crop the images

        """
        value = bool(value)
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

    # ----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def image_face_sights(self, image_file, annot_faces=None, output=None):
        """Get the image, get or detect faces, eval sights and write results.

        :param image_file: (str) Image filename
        :param annot_faces: (str) CSV/XRA filename
        :param output: (str) The output name for the image

        :return: (list) the sights of all detected faces or created filenames

        """
        # Get the image from the input
        image = sppasImage(filename=image_file)

        # Get the coordinates of the face(s) into the image
        coords = list()
        if annot_faces is not None:
            try:
                cr = sppasCoordsReader(annot_faces)
                if len(cr.coords) > 0:
                    coords = cr.coords
                else:
                    raise Exception("No coordinates found")
            except Exception as e:
                logging.error(str(e))
                sppasError(ERR_NO_FACE)

        all_sights = list()
        for face_coord in coords:
            # Search for the sights
            success = self.__fli.detect_sights(image, face_coord)
            if success is True:
                # Get the output list of sights
                sights = self.__fli.get_sights()
                all_sights.append(sights)

        # Save result as a list of sights (csv) and/or a tagged image
        if output is not None:
            new_files = list()
            output_file = self.fix_out_file_ext(output, out_format="IMAGE")
            if len(all_sights) > 1:
                # Write one file/face
                for i, sights in enumerate(all_sights):
                    # Fix the image filename
                    fn, fe = os.path.splitext(output_file)
                    pattern = self.get_output_pattern()
                    if len(pattern) > 0 and fn.endswith(pattern):
                        # the output_file is already including the pattern
                        fn = fn[:len(fn) - len(pattern)]
                    out_name = "{:s}_{:d}{:s}{:s}".format(fn, i + 1, pattern, fe)
                    _files = self.__img_writer.write(image, [sights], out_name)
                    new_files.extend(_files)

            else:
                new_files = self.__img_writer.write(image, all_sights, output_file)

            return new_files

        return all_sights

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
            logging.error("Neither a video nor an image was found.")
            raise NoInputError

        if annot is None:
            logging.error("The CSV or XRA file with identities/faces was not found.")
            raise NoInputError

        return media, annot

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        :param input_files: (list of str) Input file is an image or a video
        :param output: (str) the output file name
        :returns: (list of points or filenames) detected sights or created filenames

        """
        media_file, annot_file = self.get_inputs(input_files)

        # Input is either a video or an image
        fn, ext = os.path.splitext(media_file)
        self.__video_writer.set_image_extension(self._out_extensions["IMAGE"])
        self.__video_writer.set_video_extension(self._out_extensions["VIDEO"])

        result_files = list()
        if ext in video_extensions:
            try:
                result_files = self.__flv.video_face_sights(media_file, annot_file, self.__video_writer, output)
                self.__video_writer.close()
            except:
                import traceback
                print(traceback.format_exc())
                raise

        if ext in image_extensions:
            result_files = self.image_face_sights(media_file, annot_file, output)

        return result_files

    # -----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-sights")

    # -----------------------------------------------------------------------

    def get_input_patterns(self):
        """Pattern this annotation expects for its input filename."""
        return [
            self._options.get("inputpattern1", ""),
            self._options.get("inputpattern2", "-ident")
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
        return [out_ext, [".xra", ".csv"]]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_filetypes() -> list:
        """Types of file the annotation expects for its inputs, one list per input.

        The types are those of sppasFiles, and the inputs are in the order of
        get_input_extensions().

        :return: (list of list of str)

        """
        return [["VIDEO", "IMAGE"], ["ANNOT_ANNOT"]]
