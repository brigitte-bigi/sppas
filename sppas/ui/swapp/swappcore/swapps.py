"""
:filename: sppas.ui.swapp.swappcore.swapps.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Import the available SPPAS Web-based Applications.

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

from .swappinfo import swappWebApplicationInfo
from .wpageinfo import swappWebPageInfo

# Import all locally developed applications
from ..app_setup import SetupWebData
from ..app_dashboard import DashboardWebData
from ..app_wkps import WkpsWebData
from ..app_test.app_test import TestsWebData
# Install all installed application -- the spin-offs ones
from ..spinoff import *
# Import all locally developed generic pages, and their single provider
from ..pages import swappPagesData
from ..pages import AboutResponseRecipe
from ..pages import CiteResponseRecipe
from ..pages import ConfigurationResponseRecipe
from ..pages import FeedbackResponseRecipe
from ..pages import TraceResponseRecipe

# Determine if we're running in debug mode (log level lower than DEBUG)
DEBUG_MODE = logging.getLogger().getEffectiveLevel() <= logging.DEBUG

# List of all known web applications (stable and in development).
# The 'Dashboard' one is the default in the main_app.
WEB_APPLICATIONS = [
    swappWebApplicationInfo('Dashboard', DashboardWebData, True),
    swappWebApplicationInfo('Setup', SetupWebData, True),
    swappWebApplicationInfo('Test', TestsWebData, DEBUG_MODE),
    swappWebApplicationInfo('Wkps', WkpsWebData, DEBUG_MODE),
]

# Add all discovered spin-off applications
for cls in SPINOFF_SWAPPS:
    try:
        inst = cls()        # if instantiation fails, skip the app
        app_id = inst.id()
        WEB_APPLICATIONS.append(swappWebApplicationInfo(app_id, cls, True))
    except Exception as e:
        logging.debug(f"SWAPP: skip {cls} (instantiation failed): {e}")

# List of all known generic pages (fixed and discovered ones).
# A page is not an app: it is dispatched after the apps and it never gets
# a card in the Dashboard. Like an app, each page is declared with True
# or False: True to get a link button in the "Find out more" section of
# the Dashboard, False to be served without a link button.
WEB_PAGES = [
    swappWebPageInfo(AboutResponseRecipe, True),
    swappWebPageInfo(CiteResponseRecipe, True),
    swappWebPageInfo(ConfigurationResponseRecipe, True),
    swappWebPageInfo(FeedbackResponseRecipe, True),
    swappWebPageInfo(TraceResponseRecipe, False),
]

# Add all discovered spin-off pages
for page_info in SPINOFF_PAGES:
    if isinstance(page_info, swappWebPageInfo) is True:
        WEB_PAGES.append(page_info)
    else:
        logging.debug(f"SWAPP: skip page {page_info}: not a swappWebPageInfo.")
