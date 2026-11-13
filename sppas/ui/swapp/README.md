# swapp — SPPAS Web-based APPlication

`swapp` is the web-based user interface of SPPAS. It is built on top of
`WhakerPy` for the dynamic HTML generation and `Whakerexa` for the front-end
toolkit. Accessibility is the first priority of any design decision in this
package.


## Organization of the package

- the root only contains the server process: `main_app.py` (HTTPD server),
  `main_comm.py` (communication socket), `main_settings.py`,
  `main_trace_store.py` and `main_trace_handler.py` (trace collector);
- `swapp_core/` holds the registries and the infrastructure: `swapps.py`
  (the `WEB_APPLICATIONS` and `WEB_PAGES` registries), `swapp_app_info.py` and
  `swapp_page_info.py` (their entry classes), `swappsg.py` (the shared globals),
  `swapp_utils.py` and `swapp_exc.py`;
- `nodes/` holds the reusable HTML nodes, grouped by role:
  `buttons/`, `dialogs/`, `inputs/`, `layout/`, `feedback/`;
- `swapp_base/` holds the base classes common to every app: `swapp_bakery.py`,
  `swapp_response.py`, `swapp_view.py`, `swapp_head.py`;
- `panels/` is a leftover and holds no composite panel: `links_panel.py`
  defines `swappBaseLinksNode`, the base node of the link cards, still used by the
  Dashboard and the About page, and `annot_param.py` defines
  `swappAnnotParamDialog`, written for `app_videocued` and unused since;
- each app is an `app_*` directory, like each wx page is a `page_*` one;
- `pages/` holds the generic pages;
- `statics/` and `whakerexa/` hold the front-end resources; `spinoff/`
  discovers the external apps and pages.

Nothing else is ever added to the root.


## Work in progress

Each app and each service has a design document in its own directory: a
single `.htm` or `.html` file, finished or being written. A document designs
everything which is worth doing; the code may do a part of it only, and what
is designed and not written yet raises `NotImplementedError` where it is to be
written. A place is kept that way, and nothing is patched in later.

- `app_plugins/`, `app_annotate/`: the design document only, no code yet;
- `app_convert/`: holds its code; the remediation of what a format cannot
  hold is designed and not written;
- `services/deposit/`, `services/files/`: hold their code;
- `services/options/`: holds the code of what the options panel of the
  desktop interface does -- one field per option, suited to its kind, and the
  values handed back to the app. The description on demand, the way back to
  the value an option arrived with, the bounds of an option, what is said of
  a refused value, and the file of an option where SPPAS answers from a
  server, are designed and not written;
- `app_wkps/` is being reworked.

A service has no page of its own: it is tried alone on a page of `app_test/`,
`test_files.html` for the provision of files and `test_options.html` for the
options.

The unit tests are in `tests/swapp/`. The ones of what is not written yet
fail: a failure there is expected, not a regression. The ones of the options
need the bounds of an option, which the API of SPPAS does not hold yet.


## Language

Everything written in this package is in American English: the comments and
the docstrings, as the `CODE_STYLE_GUIDE.md` of SPPAS requires, and the design
documents, the manuals and the messages of the interface as well. It is
*recognize*, *organization*, *color*, *modeling*, *traveled*; never
*recognise*, *organisation*, *colour*, *modelling*, *travelled*.


## Naming conventions

The package has a single radical: `swapp` -- SPPAS Web APPlication, as opposed
to `wxapp`. Everything swapp defines carries it. What comes from the framework
keeps its own name (`whakerpy`, `whakerexa`), and nothing is ever abbreviated
from `swapp`.

Names are written to be read: the words of a composed name are separated by an
`_`, never run together.

- **Directories.** Named after their role: `swapp_core/`, `swapp_base/`,
  `nodes/`, `pages/`. Apps keep the `app_` prefix -- `app_dashboard/`,
  `app_setup/` -- so that they group together in a listing.
- **Modules.** Same rule: `swapp_bakery.py`, `dashboard_maker.py`,
  `fieldset_license.py`. Two deliberate exceptions: `swapps.py` and
  `swappsg.py`, which are not two words ("the swapps", and the shared
  globals); and the leading `h` of `hbutton.py`, `hdialog.py`,
  `hstatus_node.py`, which says the module defines an `HTMLNode` --
  `button.py` alone would be too generic to be safe.
- **Classes.** Radical first, in lower case, as everywhere in SPPAS
  (`sppasOption`, `sppasParam`): `swappWebData`, `swappBaseView`,
  `swappWebPageInfo`, `swappHeader`. A spin-off applies its own radical the
  same way -- `splicsTextCueSView`, in autocs.
- **Shared globals.** `swapp_settings`, `swapp_trace`, `swapp_wkps`,
  `swapp_wxstate`, `swapp_notify`, all in `swapp_core/swappsg.py`.

The two registry entry classes are named as a pair: `swapp_app_info.py` holds
`swappWebApplicationInfo`, `swapp_page_info.py` holds `swappWebPageInfo`.


## Taxonomy: App / Page / Dialog

The user interface is made of three kinds of objects. The single decision
criterion is: *does the content keep its meaning outside the current
context?* No: it is a dialog. Yes, without business logic: it is a page.
Yes, with business logic and state: it is an app.

### App

A functional unit with business logic: it has a state, a controller, user
working data, and a life cycle. An app is implemented in its own `app_*`
module, with its own URL and its own JavaScript manager.

Examples: Dashboard, Setup.

### Page

A document with its own URL and without business logic: its content keeps
its meaning independently of the context it is reached from. It contains
either pure information or a single self-contained interaction, such as a
form. A page is reachable from the nav of any app; the user enters it and
leaves it, and nothing persists in it.

Examples: Feedback, About.

### Dialog

A brief interruption *inside* the current context. Its content has no
meaning outside of this context, and the user returns to it immediately:
confirmation, alert, error or information message, consent. A dialog has
no URL and no self-contained content.

Examples: Agreement, error and information alert dialogs.


## Service

Something the apps call, and the reader never reaches: it has no URL of its
own. A service is defined by what it refuses to know: the deposit holds files
without knowing what a file is for; the options give what an app lets one set
without knowing what a single value means -- they build the form, the app
shows it. That ignorance is deliberate, and it is what lets one service serve
every app of swapp, and the ones to come.

A service is not decided by the criterion above: it shows no content of its
own. Each one has its design document in `services/`.

Examples: the deposit, the provision of files, the options.


## Serving mechanism

### How apps are served

Each app is a module named `app_*`. It declares a `WebData` class, derived
from `swappWebData` (see `swapp_base/swapp_bakery.py`), which answers two
questions: `is_page(page_name)` and `bake_response(page_name)`.

All the `WebData` classes are registered in the `WEB_APPLICATIONS` list of
`swapp_core/swapps.py`. When a page is requested, `main_app.py` iterates over this list
and asks each entry `is_page()`; the first one that answers `True` bakes
the response.

**Important:** `WEB_APPLICATIONS` has a second role. The Dashboard model
reads it to create the application cards displayed in the Dashboard. As a
consequence, an entry in `WEB_APPLICATIONS` is, by definition, an app: it
is dispatched *and* it gets a card. 

#### Where an app can be served

The same apps are served by two servers: the local one of `main_app.py`,
and the wsgi service of `main_wsgi.py`. Each says which it is when it
starts, in `swapp_serverstate.local`.

An app says for itself where it may be served, with `local_only()` of
`swappWebData` — `False` by default, so an app which does nothing of the
machine has nothing to declare. Setup declares `True`: it installs
packages on the machine it runs on, and a web service would install them
on the server, for everybody, at the request of anybody.

The declaration is read twice, and both are needed: the dispatcher drops
such an app when the server is the service, so its pages answer the "Page
not found" of swapp (`swapp_core/swapp_dispatcher.py`), and the Dashboard
disables its card without removing it (`app_dashboard/dashboard_controller.py`).
A disabled card is what a reader sees; the dispatcher is what a forged
request cannot get past.

#### Why the Desktop card is not in the registry

The card launching the wx interface is built by the Dashboard view itself,
and its launch is a method of the Dashboard controller. It is not an entry
of `WEB_APPLICATIONS`, and it is not an oversight. Five differences keep it
out, and they were checked in 2026-11:

- it has no page at all, while the registry exists to route page names;
- its button is not a link: `create_app_card()` builds a link for a page
  name ending in `.html`, and an action button otherwise, whose id
  `desktop_button` the JavaScript of the Dashboard knows by name;
- it carries a state no app has, `busy`, fed by the subprocess and by the
  socket: only one instance of the wx interface may run;
- its launch blocks: the HTTP response arrives when wx is closed, and the
  client re-enables the button on it;
- its picture is a logo, where the apps carry an image.

Its two rules about where it may run -- the disabled card, and the refused
launch -- are therefore written by hand in the controller, beside the launch
itself. The wx interface is not a web application, and it is to disappear
in a few years.

### How pages are served

Pages live in the `pages/` package. Each page has its own module; a page 
has no model, no dedicated JavaScript manager, and a controller only when 
the page processes events (a form, for example).

The `WEB_PAGES` registry lists all the known pages, exactly as
`WEB_APPLICATIONS` lists the apps: one `swappWebPageInfo(recipe, show)` entry
per page. Each page recipe describes itself with the `page()`, `name()`
and `icon()` class methods. A spin-off module declares its pages with a
`SWAPP_PAGES` list of `swappWebPageInfo`, exactly as it declares its app with
`SWAPP_CLASS`: whatever the origin of a page, the mechanics is the same.

All the pages are served by the single `swappPagesData` provider. It owns
no page list: it exposes the `is_page()`/`bake_response()` interface over
the given `WEB_PAGES` registry, consulted by `main_app.py` after the
apps. This keeps the App/Page taxonomy visible in the code and keeps
pages out of the Dashboard cards.

The `show` member of a `swappWebPageInfo` follows the same principle as the
app cards: only the pages declared with True get a link button in the
"Find out more" section of the Dashboard. The buttons carry the
`page-button` class and are handled by the JS `DashboardManager`, which
preserves the accessibility parameters when navigating. The "Traces"
page is declared with False: it is served, but reachable from the nav
of the apps only.

### How a page is shown

The reader chooses a theme, a color scheme and a contrast one. The three
choices are announced by the client and kept by `bake()` of
`swappBaseResponse`, the only place every request goes through. They are
named in the address SPPAS is opened at (`client_url()`), where the
managers of Whakerexa read them and carry them from a page to the next.

An application can bring its own theme: it is its identity, and it is
never kept as the choice of the reader. It says so twice, and writes
nothing else. Its bakery answers `theme_name()`: the Dashboard marks its
launch button and does not carry the current theme into its address. Its
head declares the theme while it is populated -- `add_theme(name, href)`
then `set_default_theme(name)` -- so that the nav, built right after, gives
the theme of SPPAS back in the link leading to the Dashboard.

An application brings more than a theme, and everything the loader of
Whakerexa is told is declared on its tag by `swappHeadNode`. Each of these
declarations is written by a method of the head, so that an application
adds to it or replaces it while its head is populated, and never has to
write the tag itself:

- the buttons whose link the framework attaches, once the page is loaded --
  `add_links(ids)`, `set_links(ids)`, `get_links()`. A page cannot attach
  them itself: its script runs before its body exists.
- the icon sets it draws from -- `add_icons(name, path, files)`,
  `set_icons(declaration)`, `set_default_icons(name)`,
  `set_icons_fallback(name)`, and their readers. The fallback is the set of
  SPPAS: an application replacing the whole list says which set falls back
  instead.
- the themes the button cycles through -- `add_theme(name, href)`,
  `set_themes(declaration)`, `set_default_theme(name)`, and their readers.
  Naming a theme of the framework in the declaration leaves out the others.


### How SPPAS is closed

The Exit button of the Dashboard closes SPPAS, which is both interfaces or
neither. When the Desktop is not running, the server answers 410 and stops,
as before. When it is running, it is asked first: it answers right away when
nothing holds it back, and acknowledges when it has to put the question to
its own reader. The acknowledgment leaves an exit waiting, and the Dashboard
shows a modal dialog until the answer comes -- the state belongs to the
server, so a second tab and a reloaded page find the same one.

Waiting concerns every page, and not the Dashboard alone: the base response
answers the state of the exit to the periodic call of any page, and the boot
shared by all of them shows the dialog. A page served while an exit waits is
written with its dialog open, so it arrives blocked instead of leaving a gap
to click through. Nothing dismisses that dialog: Escape is refused, a close
reopens it, and any click or key is taken in the capture phase -- the
shortcuts of the page are registered on the document too, and a key would
otherwise open the Journal under the dialog. The page behind it is gray and
inert, and the server clears the events it receives while waiting: a click
which would get through acts on nothing.

The answer arrives as a message of its own, and it stops nothing by itself:
a granted exit is noted in the shared state, the next poll reads it, and the
page asks for the last one -- the server serves it, says the session is over,
and stops. This last page is answered to a request asking for a page, never
to the JSON of a poll: stopping on data nobody displays would leave the
reader in front of a page whose server is already gone. A refusal removes the
dialog at the next poll. A Desktop leaving while an exit waits has answered
by leaving. A Desktop which never answers holds SPPAS open: an interface
waiting for its reader has no deadline.


## The trace/info store

The swapp server is the collector of the traces of all the SPPAS
components. The shared store (`swapp_trace`, a `swappTraceStore`) replaces
the wx log window: it accumulates the useful trace/info messages, to be
displayed by the trace page, saved into the log files, or sent with a
feedback.

The store is fed by two producers:

- the python logging of the server process, through `swappTraceHandler`,
  added to the root logger at startup. It stays there whatever a page does
  with the destination of the logs: `sppasLogSetup` removes the handlers it
  added itself, and only them, so that changing the log file does not empty
  the Journal in silence;
- the wx interface, through the communication socket (its python logging
  records are sent by a dedicated handler).

The journal page (journal.html) lives in a single named tab (`sppas_infos`): the "Journal"
button of every app menu reuses and reloads it. The page sends a periodic
heartbeat (`TraceManager`), so the server knows the tab is open: when it
is not, the Dashboard bakes a dialog inviting the user to open it -- its
single button opens the named tab. The user either has the tab, or has
the message telling to open it.

Above the header of the store, the page displays the update state of the
source code, read from `cfg.update_info` like the About page does: a
warning if a newer version exists on PyPI, an information if the installed
one is up to date.

Each record keeps its "source" (`swapp` or `wxapp`) and its "origin": the
useful/important messages of the API (`sppas/core`, `sppas/src`) are
distinguished from the secondary messages of the interfaces (`sppas/ui`),
from the `pathname` of the record, without modifying the existing code.
The records of the communication modules below the WARNING level are
excluded from the store: each socket message -- including every TRACE --
produces its own debug and info records, storing them would drown the
useful trace.
