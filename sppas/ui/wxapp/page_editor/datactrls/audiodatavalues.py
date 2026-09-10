# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.windows.datactrls.audiodatavalues.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Data class for audio.

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

import logging
from audioopy import AudioConverter

from sppas.core.coreutils import b

# ---------------------------------------------------------------------------


class AudioDataValues(object):
    """Data structure to store audio data values.

    """

    def __init__(self):
        # About the audio content itself.
        self._sampwidth = 0
        self._nchannels = 0
        self._framerate = 0
        self._duration = 0.
        self._frames = b("")

        # About what we need to draw if we have a period of time
        self.__fperiod = (0, 0)
        self.values = dict()
        self._oversampled = False

    # -----------------------------------------------------------------------

    def set_audio_data(self, nchannels=None, sampwidth=None, framerate=None, duration=None, frames=None):
        """Set all or any of the data we need about the audio."""
        if nchannels is not None:
            self._nchannels = int(nchannels)
            logging.debug(" -- given nchannels: {}".format(self._nchannels))
        if sampwidth is not None:
            self._sampwidth = int(sampwidth)
            logging.debug(" -- given sampwidth: {}".format(self._sampwidth))
        if framerate is not None:
            self._framerate = int(framerate)
            logging.debug(" -- given framerate: {}".format(self._framerate))
        if frames is not None:
            self._frames = frames
            # The values which were extracted are the ones of other frames:
            # the period has to be given again to extract the new ones.
            self.__fperiod = (0, 0)

        if duration is not None:
            self._duration = float(duration)
        else:
            logging.debug(" -- duration was not given, will eval duration --")
            self.eval_duration()

    def get_nchannels(self):
        return self._nchannels

    def get_sampwidth(self):
        return self._sampwidth

    def get_framerate(self):
        return self._framerate

    def get_duration(self):
        return self._duration

    def get_nframes(self):
        return len(self._frames)

    def get_oversampled(self):
        return self._oversampled

    # -----------------------------------------------------------------------

    def get_start_period(self):
        return float(self.__fperiod[0]) / float(self._framerate * self._nchannels * self._sampwidth)

    def get_end_period(self):
        return float(self.__fperiod[1]) / float(self._framerate * self._nchannels * self._sampwidth)

    # -----------------------------------------------------------------------

    def eval_duration(self):
        """Estimate the duration of the audio from the other information."""
        self._duration = None
        if self._framerate is not None and \
                self._nchannels is not None and \
                self._sampwidth is not None:
            self._duration = float(self.get_nframes()) / \
                             (float(self._framerate * self._nchannels * self._sampwidth))

    # -----------------------------------------------------------------------

    def set_period(self, start_time, end_time, nb_steps=7680):
        """Set a period of time and a sample rate to extract sample values.

        :param nb_steps: (int) Number of expected sample values (7680 = 2*4K width)

        TODO: extract only the missing values when the new period is overlapping
        the current one, instead of extracting all of them again. The cost is
        the frames which are read -- it is proportional to the duration of the
        period, not to nb_steps -- so scrolling of 20% should cost 20%.
        To be done before: the sampling grid has to be anchored on absolute
        positions in the frames. It is currently spread over the period, so the
        values of two overlapping periods are not the same samples and they
        can't be joined.

        """
        # Convert the time (in seconds) into a position in the frames
        start_pos = self._time_to_pos(start_time)
        end_pos = self._time_to_pos(end_time)
        if (start_pos, end_pos) == self.__fperiod:
            # The values of this period were already extracted. Extracting
            # them again is costly and it wouldn't change anything.
            return

        self.__fperiod = (start_pos, end_pos)

        # Evaluate all values during this period, with a given nb of steps
        self._extract_values(nb_steps)

    # -----------------------------------------------------------------------

    def _extract_values(self, nb_steps):
        """Extract values from the frames.

        :param nb_steps: (int) sample rate, i.e. nb of sample values to store

        """
        all_frames = self._period_frames()
        if len(all_frames) == 0 or self._duration is None:
            # there's not enough information about the audio data
            return

        # the number of "values" we have in the period
        nb_in_period = len(all_frames) // (self._sampwidth * self._nchannels)

        # the real number of steps we'll have with sample values
        real_nb_steps = nb_steps
        if self.__fperiod[1] > len(self._frames):
            # the period of time is ending higher than the audio duration
            # eval how many values should be extracted vs None
            dur_period = self._pos_to_time(self.__fperiod[1]) - self._pos_to_time(self.__fperiod[0])
            dur_audio = self._duration - self._pos_to_time(self.__fperiod[0])
            real_nb_steps = int(nb_steps * dur_audio / dur_period)

        if nb_in_period > real_nb_steps:
            # the number of frames in each step must be a constant integer
            # i.e. real_nb_steps = X * nb_in_period
            chi = nb_in_period // real_nb_steps
            real_nb_steps = nb_in_period // chi

        # prepare memory -- faster then appending at each step
        # The 4 lists of a channel are: len, min, max and zero crossing. Only
        # the min and the max are evaluated. The number of samples is not: the
        # lists are already at the expected length, which is the only thing
        # which is read of the first one. The zero crossing is not either:
        # nothing is reading it, and evaluating it was 39% of the time spent
        # in this method. Both are to be evaluated on demand if a view needs
        # them one day.
        self.values = dict()
        for c in range(self._nchannels):
            self.values[c] = [list()]*4
            self.values[c][0] = [None] * real_nb_steps  # len
            self.values[c][1] = [None] * real_nb_steps  # min
            self.values[c][2] = [None] * real_nb_steps  # max
            self.values[c][3] = [None] * real_nb_steps  # zero crossing

        # The converter is created once: creating one at each step was costly
        converter = AudioConverter()

        if nb_in_period < real_nb_steps:
            # there are more steps than values. Set each value to its step.
            self._oversampled = True
            fstep = self._sampwidth * self._nchannels
            for f in range(0, len(all_frames), fstep):
                # get the sample value of each channel
                samples = converter.unpack_data(all_frames[f:f+fstep], self._sampwidth, self._nchannels)
                # eval the xcur of this frame
                i = round((float(f) / float(self._sampwidth*self._nchannels)) * float(real_nb_steps) / float(nb_in_period))
                for c in range(self._nchannels):
                    self.values[c][1][i] = min(samples[c])
                    self.values[c][2][i] = max(samples[c])

        elif nb_in_period > real_nb_steps:
            # there are more values than steps. Set min/max values to each step.
            self._oversampled = False
            nb_by_step = nb_in_period // real_nb_steps
            for i in range(real_nb_steps):
                cur_pos = i * nb_by_step * self._sampwidth * self._nchannels
                next_pos = (i+1) * nb_by_step * self._sampwidth * self._nchannels
                frames = all_frames[cur_pos:next_pos]

                # convert frames into samples
                # -- it's much more faster than getting min/max from the frames
                samples = converter.unpack_data(frames, self._sampwidth, self._nchannels)
                for c in range(self._nchannels):
                    self.values[c][1][i] = min(samples[c])
                    self.values[c][2][i] = max(samples[c])

        else:
            # one frame = one step
            self._oversampled = False
            for i in range(real_nb_steps):
                cur_pos = i * self._sampwidth * self._nchannels
                next_pos = (i+1) * self._sampwidth * self._nchannels
                frames = all_frames[cur_pos:next_pos]

                # convert frames into samples
                samples = converter.unpack_data(frames, self._sampwidth, self._nchannels)
                for c in range(self._nchannels):
                    self.values[c][1][i] = min(samples[c])
                    self.values[c][2][i] = max(samples[c])

    # -----------------------------------------------------------------------

    @staticmethod
    def _zero_crossing(samples):
        """Return the number of zero-crossing in the given samples.

        A zero-crossing occurs if successive samples have different algebraic
        signs.

        """
        if len(samples) < 2:
            return 0
        nz = 0
        i = 1
        negative = samples[0] < 0
        nb_samples = len(samples)
        while i < nb_samples:
            if negative:
                while samples[i] < 0:
                    i += 1
                    if i == nb_samples:
                        return nz
            else:
                while samples[i] >= 0:
                    i += 1
                    if i == nb_samples:
                        return nz

            nz += 1
            negative = not negative

    # -----------------------------------------------------------------------

    def _time_to_pos(self, time_value):
        return int(time_value * float(self._framerate)) * \
               self._sampwidth * \
               self._nchannels

    def _pos_to_time(self, pos_value):
        return float(pos_value) / float(self._framerate * self._sampwidth * self._nchannels)

    # -----------------------------------------------------------------------

    def _period_frames(self):
        """Return the frame of the currently defined period."""
        if self.__fperiod[1] - self.__fperiod[0] > 0:
            end = self.__fperiod[1]
            return self._frames[self.__fperiod[0]:end]
        return b('')
