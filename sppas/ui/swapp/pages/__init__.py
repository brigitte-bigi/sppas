# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.pages.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The init file of the generic pages package

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

from .about_maker import swappAboutResponseRecipe
from .cite_maker import swappCiteResponseRecipe
from .configuration_maker import swappConfigurationResponseRecipe
from .feedback_maker import swappFeedbackResponseRecipe
from .trace_maker import swappTraceResponseRecipe
from .help_maker import swappHelpResponseRecipe
from .pages_data import swappPagesData

# -----------------------------------------------------------------------

__all__ = (
    "swappAboutResponseRecipe",
    "swappCiteResponseRecipe",
    "swappConfigurationResponseRecipe",
    "swappFeedbackResponseRecipe",
    "swappTraceResponseRecipe",
    "swappHelpResponseRecipe",
    "swappPagesData"
)
