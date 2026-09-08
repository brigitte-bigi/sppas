# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.spinoff.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Dynamic loader for external "spin-off" annotations.

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

This module automatically imports all classes declared in each Python file
of the `spinoff/` directory, enabling the SPPAS annotation system to detect
and use new annotations added dynamically (i.e., dropped into the folder).

Each file in `spinoff/` is expected to import (not necessarily define) one or
more annotation classes — usually located in separately developed spin-off
modules placed alongside native annotations.

This approach allows external contributors or modules to register their
annotation processors simply by adding a `.py` file to the `spinoff/` folder
without modifying the rest of the codebase.

The classes (even if imported from another module) are automatically exposed
in the `sppas.src.annotations.spinoff` namespace.

Example usage:

    from sppas.src.annotations.spinoff1 import MySpinOffClass1
    from sppas.src.annotations import MySpinOffClass2

"""

import os
import importlib
import pkgutil
import inspect
import logging


# Absolute path to the current directory (spinoff/)
current_dir = os.path.dirname(__file__)

# Full module path of this package (e.g. sppas.src.annotations.spinoff)
current_package = __name__

# Store the defined spin-off SWAPP_CLASS
SPINOFF_SWAPPS = []

# Store the declared spin-off SWAPP_PAGES -- a list of WebPageInfo objects
SPINOFF_PAGES = []

# Iterate through all modules in this directory (excluding __init__.py and sub-packages)
for _, module_name, is_pkg in pkgutil.iter_modules([current_dir]):
    if is_pkg or module_name == "__init__":
        continue

    full_module_name = f"{current_package}.{module_name}"

    try:
        # Dynamically import the module
        module = importlib.import_module(full_module_name)

        # Iterate through all class objects found in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Add the class to the package namespace (even if it was imported)
            globals()[name] = obj

        app_cls = getattr(module, "SWAPP_CLASS", None)
        if app_cls is not None:
            SPINOFF_SWAPPS.append(app_cls)

        page_infos = getattr(module, "SWAPP_PAGES", None)
        if page_infos is not None:
            SPINOFF_PAGES.extend(page_infos)

    except Exception as e:
        # Silently fail to keep robustness
        logging.warning(f"Spinoff init. Failed to import module {full_module_name}: {e}")
        continue
