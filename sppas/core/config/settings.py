"""
:filename: sppas.config.settings.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Store global settings of the application.

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

New in SPPAS 4.11:
  Each setting is instantiated in this file and no longer in the init of the
  package. It ensures it will be instantiated only once in the application.
  The classes are then removed of the init.
New in SPPAS 5.0.0:
  Add the 'bin' folder of SPPAS into Windows PATH environment variable.

"""

from __future__ import annotations
import os
import sys
from importlib.metadata import metadata
import logging
import locale

try:
    from audioopy.aio import extensions as audioopy_extensions
except ImportError:
    # no audio support
    audioopy_extensions = list()

# ---------------------------------------------------------------------------


class sppasBaseSettings:
    """Base class for any kind of mutable or immutable settings saved in a file.

    The sppasBaseSettings class serves as a base class for managing settings
    that can be either mutable or immutable. It provides mechanisms to load
    and save these settings from and to a file, ensuring that the settings are
    consistently managed across different instances.

    The setting members are declared in the class dictionary. It allows to
    store modifiable or un-modifiable members - by declaring a set() method
    or by overriding __setattr__, and to load/save them from/to a file every
    time the instance is created/deleted.

    :Example:
    >>>with sppasBaseSettings() as settings:
    >>>    settings.newKey = 'myNewValue'
    >>>    print(settings.newKey)

    """

    def __init__(self):
        """Create the dictionary and load config file if any.

        """
        # Dictionary that holds the settings.
        self.__dict__ = dict()
        self.load()

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        self.save()

    # -----------------------------------------------------------------------

    def load(self):
        """Load the dictionary of settings from a file. To be overridden."""
        pass

    # -----------------------------------------------------------------------

    def save(self):
        """Save the dictionary of settings in a file. To be overridden."""
        pass

# ---------------------------------------------------------------------------


class sppasPathSettings:
    """Immutable class to manage paths of SPPAS.

    The sppasPathSettings class is designed to manage and provide immutable
    paths for the SPPAS application. It initializes various directory paths
    based on the location of the SPPAS package and ensures that these paths
    cannot be modified or deleted after they are set.

    :Example:
    >>> with sppasPathSettings() as paths:
    >>>     print(paths.sppas)
    >>>     # Outputs the SPPAS directory path

    """

    def __init__(self):
        """Create the sppasPathSettings dictionary.

        """
        # Temporarily mutable
        self._is_frozen = False
        # An external directory to store: trashed files, workspaces, logs.
        ext_dir = sppasPathSettings.fix_ext_dir()
        # Where are we?
        sppas_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base_dir = os.path.dirname(sppas_dir)

        # Define absolute and/or relative paths
        self.__dict__ = dict(
            basedir=base_dir,
            tests=os.path.join(base_dir, "tests"),

            sppas=sppas_dir,
            cli=os.path.join(sppas_dir, "bin"),
            etc=os.path.join(sppas_dir, "etc"),
            po=os.path.join(sppas_dir, "core", "locale"),
            src=os.path.join(sppas_dir, "src"),
            ui=os.path.join(sppas_dir, "ui"),
            plugins=os.path.join(sppas_dir, "plugins"),
            icons=os.path.join(sppas_dir, "ui", "wxapp", "icons"),
            images=os.path.join(sppas_dir, "ui", "wxapp", "images"),

            ext_dir=ext_dir,
            logs=os.path.join(ext_dir, "logs"),
            trash=os.path.join(ext_dir, "trash"),
            wkps=os.path.join(ext_dir, "workspaces"),

            # Files larger than 10 MB trigger a 'Varnish' (503) error on sppas.org,
            # which is hosted by gandi.net.
            # Therefore, annotation resources are temporarily hosted on SourceForge.
            # url_annot_resources="https://sppas.org/resources/"
            url_lang_resources="https://sppas.org/resources/",
            url_spin_resources="https://sppas.org/resources/",
            url_annot_resources="https://sourceforge.net/projects/sppas/files/"
        )

        # Modifiable members with setters
        self.__resources = os.path.join(self.__dict__['ext_dir'], "resources")
        self.__samples = os.path.join(self.__resources, "samples")

        # Add the 'bin' folder of SPPAS into system PATH environment variable
        os.environ['PATH'] = self.__dict__['cli'] + os.pathsep + os.environ['PATH']

        # Freeze the instance
        self._is_frozen = True

    # -----------------------------------------------------------------------
    # Getters/Setters/Properties
    # -----------------------------------------------------------------------

    def get_resources(self) -> str:
        """Return the path to resources."""
        return self.__resources

    def set_resources(self, value: str) -> None:
        """Set the resource path.

        :param value: (str|None) Resources path value.
        :raises: TypeError: Invalid type of the given value.
        :raises: IOError: Resources path does not exist.

        """
        if type(value) is not str:
            raise TypeError("resources must be a string.")
        if os.path.isdir(value) is False:
            raise IOError("resources must be a directory.")

        self.__resources = value
        self.__samples = os.path.join(value, "samples")

    resources = property(get_resources, set_resources)

    # -----------------------------------------------------------------------

    def get_samples(self) -> str:
        """Return the path to samples."""
        return self.__samples

    samples = property(get_samples, None)

    # -----------------------------------------------------------------------

    @staticmethod
    def fix_ext_dir() -> str:
        """Return the external directory to be used for logs/trash/wkps.

        Create if it doesn't exist.

        """
        p = sppasPathSettings.get_ext_dir()
        os.makedirs(p, exist_ok=True)
        return p

    # -----------------------------------------------------------------------

    @staticmethod
    def get_ext_dir() -> str:
        """Return the external directory to be used for logs/trash/wkps.

        """
        p = os.getenv('SPPAS')
        if p is not None and len(p) > 0:
            return os.path.abspath(p)

        home = os.path.expanduser('~')

        if os.name == 'nt':
            base = os.getenv('APPDATA', home)
            return os.path.join(base, 'sppas')

        if sys.platform == 'darwin':
            return os.path.join(home, 'Library', 'Application Support', 'sppas')

        base = os.getenv('XDG_DATA_HOME', os.path.join(home, '.local', 'share'))
        return os.path.join(base, 'sppas')

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    # -----------------------------------------------------------------------

    def __setattr__(self, key, value):
        """Override to prevent any attribute setter."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    # -----------------------------------------------------------------------

    def __delattr__(self, key):
        """Override to prevent any attribute deletion."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__delattr__(key)

# ---------------------------------------------------------------------------


class sppasGlobalSettings(sppasBaseSettings):
    """Global non-modifiable settings of SPPAS.

    These settings are immutable.

    :example:
    >>>with sppasGlobalSettings() as settings:
    >>>    print(settings.__name__)
    SPPAS
    >>> settings = sppasGlobalSettings()
    >>> settings._is_frozen = False       # raise AttributeError
    >>> settings.new_att = "some value"   # raise AttributeError

    """

    def __init__(self):
        """Create the dictionary and load the main config file."""
        # Temporarily mutable
        self._is_frozen = False
        # Create the class dictionary and load settings from a json config file
        super(sppasGlobalSettings, self).__init__()
        # Freeze the instance
        self._is_frozen = True

    # -----------------------------------------------------------------------

    def __setattr__(self, key, value):
        """Override to prevent any attribute setter."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    # -----------------------------------------------------------------------

    def __delattr__(self, key):
        """Override to prevent any attribute deletion."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__delattr__(key)

    # -----------------------------------------------------------------------

    def load(self):
        """Override. Do not load settings: fixed. """
        try:
            m = metadata("sppas")
        except:
            m = dict()
        v = m.get("Version", "5.1")
        r = v.split(".")
        if len(r) < 2:
            r[0] = "5"
            r[1] = "1"

        with sppasPathSettings() as sp:
            # Fill in the config dict
            self.__dict__ = dict(
                __docformat__="reStructuredText en",
                __name__=m.get("Name", "SPPAS"),
                __title__="the automatic annotation and analysis of speech",
                __summary__="SPPAS implements solutions for the automatic annotation and analysis of audio/video speech recordings.",
                __description__=m.get("Summary", "SPPAS can produce automatically annotations, perform analysis of annotated data\nand convert files from/to various formats."),
                __url__="https://sppas.org/",
                __author__=m.get("Author", "Brigitte Bigi"),
                __contact__="contact@sppas.org",
                __copyright__="Copyright (C) 2011-2026  Brigitte Bigi, CNRS",
                __version__=v,
                __release__=r[0] + "." + r[1],
                __encoding__="utf-8",
                __lang__="en"  # Fallback language [if no locale and no defined]
            )

    # -----------------------------------------------------------------------

    @staticmethod
    def get_lang_list(fallback: str | None = None):
        """Return the list of languages depending on the default locale.

        Return a list of languages, prioritizing the system locale
        and falling back to a default language if needed.

        This method attempts to detect the system's default locale language.
        If it fails (e.g., due to OS quirks like macOS), it falls back to
        an environment variable or the provided default language.

        The returned list is ordered with the preferred language first,
        and any fallback(s) after.

        :param fallback: (str) The default language code to use as fallback,
            typically "en".
        :return: (list) Language codes (e.g., ["en", "fr"]). May be empty.

        """
        # Start with the fallback language as the first choice
        lc = list()
        if fallback is not None:
            lc.append(fallback)

        try:
            # Python 3.6+ method to get locale.
            sys_locale, _ = locale.getlocale()

            if sys_locale is None:
                # Common on macOS or misconfigured systems
                # Try the LANG environment variable as an alternative
                sys_locale = os.getenv("LANG")

            if sys_locale == 'C':
                # Common on WSL or misconfigured systems
                # Try the LC_LANG environment variable as an alternative
                sys_locale = os.getenv("LC_LANG")

            if sys_locale is not None:
                # Extract the language code from locale (e.g., "fr_FR" -> "fr")
                if "_" in sys_locale:
                    sys_locale = sys_locale[:sys_locale.index("_")]
                ## Prefer the locale, then the given one -- used as fallback:
                ## lc.insert(0, sys_locale)
                # Append the detected system language after the fallback
                # This ensures the fallback is preferred if both are available
                # This was reversed prior to SPPAS 4.25 (April 2025)
                if locale not in lc:
                    lc.append(sys_locale)

            else:
                if len(lc) == 0:
                    lc.append("en")
                # Warn the user if no usable system locale was found
                logging.warning("The Operating System didn't defined a valid default locale.")
                logging.warning("It means it assigns the language in a *** non-standard way ***.")
                logging.warning("This problem can be fixed by setting properly the 'LANG' "
                                "environment variable. See the documentation of your OS.")
                logging.warning("As a consequence, the language is set to its default value: "
                                "{:s}".format(lc[0]))

        except Exception as e:
            # Log any unexpected error during locale detection
            logging.error("Can't get the system default locale: {}".format(e))

        return lc

# ----------------------------------------------------------------------------


class sppasSymbolSettings:
    """Representation of global non-modifiable symbols of SPPAS.

    This class defines:

        - unk: the default symbol used by annotations and resources to
          represent unknown entries
        - ortho: symbols used in an orthographic transcription, or after
          a text normalization
        - phone: symbols used to represent events in grapheme to phoneme
          conversion.
        - all: ortho+phone (i.e. all known symbols)

    The class ensures immutability after initialization.

    :example:
    >>> with sppasSymbolSettings() as settings:
    >>>     print(settings.unk)
    "dummy"
    >>> settings = sppasSymbolSettings()
    >>> print(settings.unk)
    "dummy"
    >>> settings.key = "value"  # raise AttributeError
    >>> del settings            # raise AttributeError

    """

    def __init__(self):
        """Create the sppasSymbolSettings dictionary."""
        self._is_frozen = False
        self.__dict__ = dict(
            unk="dummy",
            phone=sppasSymbolSettings.__phone_symbols(),
            ortho=sppasSymbolSettings.__ortho_symbols(),
            all=sppasSymbolSettings.__all_symbols()
        )
        self._is_frozen = True

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    # -----------------------------------------------------------------------

    def __setattr__(self, key, value):
        """Override to prevent any attribute setter."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    # -----------------------------------------------------------------------

    def __delattr__(self, key):
        """Override to prevent any attribute deletion."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__delattr__(key)

    # -----------------------------------------------------------------------

    @staticmethod
    def __ortho_symbols():
        return {
            '#': "silence",
            '+': "pause",
            '*': "noise",
            '@': "laugh",
            'dummy': 'dummy'
        }

    # -----------------------------------------------------------------------

    @staticmethod
    def __phone_symbols():
        return {
            'sil': "silence",
            '#': "silence",
            'sp': "pause",
            '+': "pause",
            'noise': "noise",
            'laugh': "laugh",
            'dummy': 'dummy'
        }

    # -----------------------------------------------------------------------

    @staticmethod
    def __all_symbols():
        s = dict()
        s.update(sppasSymbolSettings.__ortho_symbols())
        s.update(sppasSymbolSettings.__phone_symbols())
        return s

# ---------------------------------------------------------------------------


class sppasSeparatorSettings:
    """Representation of global non-modifiable separators of SPPAS.

    """

    def __init__(self):
        """Create the sppasSeparatorSettings dictionary.

        """
        self._is_frozen = False
        self.__dict__ = dict(
            phonemes="-",    # X-SAMPA standard
            syllables=".",   # X-SAMPA standard
            variants="|"     # used for all alternative tags
        )
        self._is_frozen = True

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    # -----------------------------------------------------------------------

    def __setattr__(self, key, value):
        """Override to prevent any attribute setter."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    # -----------------------------------------------------------------------

    def __delattr__(self, key):
        """Override to prevent any attribute deletion."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__delattr__(key)

# ---------------------------------------------------------------------------


class sppasAnnotationsSettings:
    """Representation of global non-modifiable settings of annotations.

    """

    def __init__(self):
        """Create the sppasAnnotationsSettings dictionary.

        """
        self._is_frozen = False
        self.__dict__ = dict(
            error=-1,
            ok=0,
            warning=1,
            ignore=2,
            info=3,

            # default file extension for annotated files created by SPPAS
            annot_extension=".xra",
            measure_extension=".PitchTier",  # the .mra format must be developed!
            table_extension=".arff",         # the .tra format must be developed!
            audio_extension=".wav",
            video_extension=".mp4",
            image_extension=".jpg",

            # all the input types of automatic annotations
            #  - standalone = only one input file
            #  - speaker = two input files of the same speaker
            #  - interaction = two input files of different speakers
            types=("STANDALONE", "SPEAKER", "INTERACTION"),

            # all the file formats for automatic annotations.
            # there are 4 main categories, and 3 sub-categories for the ANNOT one.
            typeformat=("ANNOT", "ANNOT_ANNOT", "ANNOT_MEASURE", "ANNOT_TABLE", "AUDIO", "IMAGE", "VIDEO"),

            # standard iso639-3 code for an undetermined language.
            UNDETERMINED="und"

        )
        self._is_frozen = True

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    # -----------------------------------------------------------------------

    def __setattr__(self, key, value):
        """Override to prevent any attribute setter."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    # -----------------------------------------------------------------------

    def __delattr__(self, key):
        """Override to prevent any attribute deletion."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__delattr__(key)

# ---------------------------------------------------------------------------


class sppasExtensionsSettings:
    """Representation of global non-modifiable settings of file extensions.

    """

    def __init__(self):
        """Create the sppasAnnotationsSettings dictionary.

        """
        self._is_frozen = False
        self.__dict__ = dict(
            # Supported input audio file extensions
            AUDIO=audioopy_extensions,

            # Default file extension for annotated files created by SPPAS
            annot_extension=".xra",
            measure_extension=".PitchTier",  # the .mra format must be developed!
            table_extension=".arff",         # the .tra format must be developed!
            audio_extension=".wav",
            video_extension=".mp4",
            image_extension=".jpg",
        )
        self._is_frozen = True

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    # -----------------------------------------------------------------------

    def __setattr__(self, key, value):
        """Override to prevent any attribute setter."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    # -----------------------------------------------------------------------

    def __delattr__(self, key):
        """Override to prevent any attribute deletion."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__delattr__(key)

class sppasVocabSettings:
    """Default content of the fallback resource files of the 'vocab' folder.

    These files are created in the 'vocab' resources folder if they are
    missing (see 'sppasSupportDirectories'). To avoid any duplication, the
    file names and part of their content are derived from existing settings:

        - the undetermined language code comes from 'annots.UNDETERMINED'
        - the unknown-word symbol comes from 'symbols.unk'

    :example:
    >>> with sppasVocabSettings() as settings:
    >>>     for filename, content in settings.files.items():
    >>>         print(filename)

    """

    def __init__(self):
        """Create the sppasVocabSettings dictionary."""
        self._is_frozen = False
        self.__dict__ = dict(
            files=sppasVocabSettings.__default_files()
        )
        self._is_frozen = True

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    # -----------------------------------------------------------------------

    def __setattr__(self, key, value):
        """Override to prevent any attribute setter."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    # -----------------------------------------------------------------------

    def __delattr__(self, key):
        """Override to prevent any attribute deletion."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__delattr__(key)

    # -----------------------------------------------------------------------

    @staticmethod
    def __default_files():
        """Return a dict matching a file name to its default content."""
        undetermined = annots.UNDETERMINED
        return {
            "Punctuations.txt": sppasVocabSettings.__punctuations(),
            undetermined + ".vocab": sppasVocabSettings.__und_vocab(),
            undetermined + ".stp": sppasVocabSettings.__und_stp(),
        }

    # -----------------------------------------------------------------------

    @staticmethod
    def __punctuations():
        """Return the default content of the punctuation marks file."""
        marks = [
            ' ̥',
            '!',
            '"',
            '#',
            '$',
            '%',
            '&',
            "'",
            '(',
            '(*',
            ')',
            '**',
            '***',
            '****',
            '+-',
            '+/',
            ',',
            '-',
            '-+',
            '--',
            '.',
            '.*',
            '.,',
            '..',
            '..,',
            '...',
            '...,',
            '....',
            '....,',
            '.....,',
            '.........',
            '/',
            '/ ̥',
            ':',
            ';',
            '<',
            '<<',
            '=',
            '>',
            '>>',
            '?',
            '[',
            '\\',
            ']',
            '^',
            '_',
            '`',
            '|',
            '~',
            '£',
            'ª',
            '«',
            '³',
            '·',
            '»',
            '»_',
            '¿',
            '——',
            '‖',
            '‘',
            '“',
            '”',
            '„',
            '…',
            '……',
            '⁚⁚',
            '€',
            '⋅',
            '◦',
            '❰',
            '❱',
            '、',
            '。',
            '《',
            '》',
            '・',
            '！',
            '＃',
            '％',
            '＆',
            '{',
            '}',
            '（',
            '）',
            '＋',
            '，',
            '－',
            '／',
            '：',
            '；',
            '＝',
            '？',
            '［',
            '］',
            '｀',
            '｛',
            '｜',
            '｝',
            '～',
            '￥',
            '–',
            '— ',
        ]
        return "\n".join(marks) + "\n"

    # -----------------------------------------------------------------------

    @staticmethod
    def __und_vocab():
        """Return the default vocabulary of the undetermined language."""
        letters = [chr(code) for code in range(ord('a'), ord('z') + 1)]
        return "\n".join(letters)

    # -----------------------------------------------------------------------

    @staticmethod
    def __und_stp():
        """Return the default stop-words of the undetermined language."""
        return symbols.unk

# ---------------------------------------------------------------------------
# Create an instance of each of the global settings
# ---------------------------------------------------------------------------


sg = sppasGlobalSettings()
paths = sppasPathSettings()
symbols = sppasSymbolSettings()
separators = sppasSeparatorSettings()
annots = sppasAnnotationsSettings()
vocab_defaults = sppasVocabSettings()
