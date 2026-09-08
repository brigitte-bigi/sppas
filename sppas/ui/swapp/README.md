# swapp — SPPAS Web-based APPlication

`swapp` is the web-based user interface of SPPAS. It is built on top of
`WhakerPy` for the dynamic HTML generation and `Whakerexa` for the front-end
toolkit. Accessibility is the first priority of any design decision in this
package.


## Organization of the package

- the root only contains the server process: `main_app.py` (HTTPD server),
  `main_comm.py` (communication socket), `main_settings.py`,
  `main_trace_store.py` and `main_trace_handler.py` (trace collector);
- `wappcore/` holds the registries and the infrastructure: `wapps.py`
  (the `WEB_APPLICATIONS` and `WEB_PAGES` registries), `wappinfo.py` and
  `wpageinfo.py` (their entry classes), `wappsg.py` (the shared globals),
  `wapputils.py` and `wexc.py`;
- `nodes/` holds the reusable HTML nodes, grouped by role:
  `buttons/`, `dialogs/`, `inputs/`, `layout/`, `feedback/`;
- `wappbase/` holds the base classes common to every app: `wappbakery.py`,
  `wappresponse.py`, `wappview.py`, `wapphead.py`;
- `panels/` holds the composite panels, assembled from nodes and shared
  across apps;
- each app is an `app_*` directory, like each wx page is a `page_*` one;
- `pages/` holds the generic pages;
- `statics/` and `whakerexa/` hold the front-end resources; `spinoff/`
  discovers the external apps and pages.

Nothing else is ever added to the root.


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


## Serving mechanism

### How apps are served

Each app is a module named `app_*`. It declares a `WebData` class, derived
from `swappWebData` (see `wappbase/wappbakery.py`), which answers two
questions: `is_page(page_name)` and `bake_response(page_name)`.

All the `WebData` classes are registered in the `WEB_APPLICATIONS` list of
`wappcore/wapps.py`. When a page is requested, `main_app.py` iterates over this list
and asks each entry `is_page()`; the first one that answers `True` bakes
the response.

**Important:** `WEB_APPLICATIONS` has a second role. The Dashboard model
reads it to create the application cards displayed in the Dashboard. As a
consequence, an entry in `WEB_APPLICATIONS` is, by definition, an app: it
is dispatched *and* it gets a card. 

### How pages are served

Pages live in the `pages/` package. Each page has its own module; a page 
has no model, no dedicated JavaScript manager, and a controller only when 
the page processes events (a form, for example).

The `WEB_PAGES` registry lists all the known pages, exactly as
`WEB_APPLICATIONS` lists the apps: one `WebPageInfo(recipe, show)` entry
per page. Each page recipe describes itself with the `page()`, `name()`
and `icon()` class methods. A spin-off module declares its pages with a
`SWAPP_PAGES` list of `WebPageInfo`, exactly as it declares its app with
`SWAPP_CLASS`: whatever the origin of a page, the mechanics is the same.

All the pages are served by the single `swappPagesData` provider. It owns
no page list: it exposes the `is_page()`/`bake_response()` interface over
the given `WEB_PAGES` registry, consulted by `main_app.py` after the
apps. This keeps the App/Page taxonomy visible in the code and keeps
pages out of the Dashboard cards.

The `show` member of a `WebPageInfo` follows the same principle as the
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


## The trace/info store

The swapp server is the collector of the traces of all the SPPAS
components. The shared store (`wapp_trace`, a `swappTraceStore`) replaces
the wx log window: it accumulates the useful trace/info messages, to be
displayed by the trace page, saved into the log files, or sent with a
feedback.

The store is fed by two producers:

- the python logging of the server process, through `swappTraceHandler`,
  added to the root logger at startup;
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
