#!/usr/bin/env python
"""
:filename: sppas.makedoc.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Create the documentation of SPPAS with ClammingPy

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

import sys
import os
import logging

PROGRAM = os.path.abspath(__file__)
SPPAS = os.path.dirname(PROGRAM)
sys.path.append(SPPAS)

import sppas

try:
    import clamming
except ImportError:
    print("This program requires `Clamming` documentation generator.")
    print("It can be installed with: pip install ClammingPy.")
    print("See <https://pypi.org/project/Clamming/> for details.")
    sys.exit(-1)


# ---------------------------------------------------------------------------
logging.getLogger().setLevel(1)

# -------------------------------------------------
# List of modules to be documented: automatically create the documentation 
# of all known classes of the following 'sppas' packages.
# -------------------------------------------------
packages = list()
packages.append(sppas.core.config)
packages.append(sppas.core.coreutils)
packages.append(sppas.core.preinstall)
packages.append(sppas.src.utils)
packages.append(sppas.src.structs)
packages.append(sppas.src.anndata)
packages.append(sppas.src.imgdata)
packages.append(sppas.src.videodata)
packages.append(sppas.src.wkps)
packages.append(sppas.src.resources)
packages.append(sppas.src.analysis)
packages.append(sppas.src.annotations)

# ----------------------------
# Options for exportation
# ----------------------------
opts_export = clamming.ExportOptions()
opts_export.software = 'sppas ' + sppas.config.sg.__version__
opts_export.url = 'https://sppas.org/'
opts_export.copyright = sppas.config.sg.__copyright__
opts_export.title = 'sppas doc'
opts_export.theme = 'light'
opts_export.favicon = 'icons/sppas.ico'   # relative path to statics
opts_export.icon = 'logos/sppas-logo-v5.png'   # relative path to statics
opts_export.readme = True
# New in ClammingPy 3.1
# ... the table of contents is either a collapsible aside or a fixed panel
opts_export.aside_toc = True
# ... the theme is a file of the statics folder. It defines the colors of the
# pages, and the reader can switch it for the high-contrast one of Whakerexa.
opts_export.css_theme = 'clamming_theme.css'

# For a local use:
opts_export.wexa_statics = "/".join(("..", "sppas", "ui", 'swapp', 'whakerexa', 'wexa_statics'))
opts_export.statics = "/".join(("..", "sppas", 'ui', 'swapp', 'statics'))

# -------------------------------------------------
# Generate documentation
# -------------------------------------------------
clams_modules = clamming.ClamsModules(packages)

# Export documentation into HTML files.
# One .html file = one documented class.
clams_modules.html_export_packages("docs", opts_export, "README.md")

# Export documentation into a Markdown file.
# One .md file = one documented module.
# clamming.ClamsPack.markdown_export_packages(packages, os.path.join("docs", "api"), html_export)
