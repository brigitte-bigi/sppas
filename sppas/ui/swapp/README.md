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
  `swapp_response.py`, `swapp_view.py`, `swapp_head.py`, and `swapp_help.py`
  and `swapp_help_button.py`, the view of the help of any app and the button
  of its nav, and `swapp_process.py` and `swapp_process_progress.py`, a long
  process of any app and the progress it is given;
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

- `app_annotate/`: holds its code;
- `app_plugins/`: the design document, and the shell of the app: a page which
  shows its nav and its help, and nothing else yet;
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


## Where the logic lives

Three languages are used here, and each one has one charge. **Python holds every
rule of the business**: what is offered, what a decision implies, what is refused,
what is computed. **HTML is what is shown**, and it is written by Python, which is
what `WhakerPy` is for. **JavaScript sends what the page holds and puts in place
what the server wrote**, and it is written only where nothing else can do it.

The criterion is not the amount of JavaScript, it is what it is allowed to know:
**JavaScript computes nothing the model knows.** It shows, it hides, it sends a
form, it puts a fragment in place, it asks again at intervals while something
lasts. Whatever has to be *decided* is decided in Python, even when that costs a
request: a request answered locally costs nothing a reader can feel.

The test which settles the doubtful cases: **a rule which would have to be
written twice -- once in Python, once in JavaScript -- is written in Python
only.** A rule in two languages is two rules, and the day one of them changes,
the other stays. Whoever maintains this package maintains Python.

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

The help of an app is one of its views, and not a page: see "How the help
of an app is shown".

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
and a wsgi service. Which one serves them is `served_locally` of the
settings of swapp (`swapp_settings`, saved in `.webapp~`), the first ones
loaded by this package. It holds for every reader, and it is `False`
unless it is said otherwise: the local server says it when it starts.

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

### How the nav of a view is built

The nav is written by `populate_body_nav()` of `swappBaseView`, in sections.
The first one holds what changes the look of the page: the pin of the menu,
the theme, the contrast and the color. The second one holds the items every
view has, in this order: the Dashboard, the Journal and the Help. The Help of
an app sends the form `_form_id()` gives, or a form of its own when it gives
none; the Help of a page is disabled, as `_has_help()` says. Then
`_populate_body_nav()` appends the items of the view, in a section of their
own: Exit in the Dashboard, the SPPAS website in Setup, Close in the Journal,
Back in the page of a test.

### How the help of an app is shown

The help of an app is not a page: it is one of the views of the app, and the
same one for every app. A page is entered and left with nothing kept, while an
app carries its record in the form of its page: a help reached by a link would
lose it.

The Help button of the nav is written by `append_help_button()` of
`swappBaseView`. It is a submit button: it sends the form which carries the
record of the app, with `event_bake=swapp_help`. The bakery of an app names
that form with `form_id()`, and gives it to its view. An app which has no form
gets an empty one of its own, beside the button: its Help button works the same
way, and the day it holds a record, it names its form.

The help is answered by `bake()` of `swappBaseResponse`, before the app, which
is asked nothing: the main content is replaced by the view of the help,
`swappHelpNode` of `swapp_base/swapp_help.py`. It holds the document the bakery
names with `help_document()` -- the user manual and the conceptual folder of
the app, written by hand and served as it is -- or a text saying that it is not
written yet. Its form takes the identifier of the form of the app, so that the
Help button of the nav is tied to a form while the help is shown, and it carries
hidden what the form of the app transmitted.

Its Back button sends all of it again, with `event_bake=swapp_back`. Each app
answers this task with its default view, built from the record it received: it
asks nothing more of the app than any request which carries a record. The two
names are declared once, in `swapp_base/swapp_help.py`.

While the help is shown, the Help button of the nav is a Back button too: a
help may be long, and the Back button of its top is out of sight once it is
read. The button is a `swappHelpButton` (`swapp_base/swapp_help_button.py`):
it keeps its identifier and its form, so that its key, `h`, opens the help and
goes back from it, and only what it sends and what it says change. The nav is
built once: `bake()` of `swappBaseResponse` sets the button at every request,
as it sets the dialog of the exit.

The help and the way back are navigations, whatever the app: the boot shared
by all the pages takes their submission before the manager of the app, which
would send it without leaving the page, and carries the accessibility
parameters in the address. The same boot starts the Book extra of Whakerexa
when the help is shown. The head of every page loads the stylesheet of the
Book, and the one of the toggle group, which a document may show as its app
does.

A page is not concerned: its Help button of the nav is disabled. The
`app_wkps/` app is not concerned either while it is reworked:
its bakery is not a `swappBaseResponse`.

### How a long process of an app is followed

A process of an app lasts longer than the request which started it: the
conversion of Convert, the run of Annotate, the installation of Setup. It is
a `swappProcess` (`swapp_base/swapp_process.py`), the same for every app. It
performs what the app gives it in a thread, and where it stands is written in
a file of the folder of the logs of SPPAS, and nowhere else: the file is
written again at once each time, and whatever answers a request reads it
there, by the name the page transmits. Nothing of the process is held by the
server between two requests.

What performs the process -- the app, or the API -- is given a
`swappProcessProgress` (`swapp_base/swapp_process_progress.py`): it is a
`sppasBaseProgress`, set as any other one, and each time it is set it writes
the file. That is how a process is laid over an API which knows nothing of
swapp: the API is given a progress, as it always was.

The page asks where the process stands with `event_name=swapp_progress`, and
the name of the process in the field `swapp_process`. It is answered by
`bake()` of `swappBaseResponse`, whatever the app, as the help is: 202 while
the process goes, 200 and the hundred once it has ended. The client is one
module, `statics/js/swapp_process.js`: an app gives it the name and what it
does once the process has ended.

What an app shows of the result is not the process's: the results of a
conversion stay in the report of Convert, read when the page asks for them.

The conversion of Convert, the run of Annotate and the installation of Setup
are processes of swapp. The API of the annotations is not changed: given
nothing when it is created, its manager performs the annotations in the thread
of its caller, which is the thread of the process, and it is given the
progress of the process. Neither is the installer of Setup: it installs in
the thread of the process, and it is given the progress of the process.

### How a long process holds the page

A long process of an app is modal: while it goes, the page shows its progress,
and nothing else of the app answers. The sign of it is the progress bar,
`percent_progress`, which the server writes while the process goes, and only
then.

The boot shared by all the pages watches the main content, because a process
starts and ends without the page being loaded again. While the progress is
there, the items of the nav which leave the page or send something are `inert`:
out of reach of the mouse, of the keyboard and of a screen reader, and a key
which would click one of them is taken in the capture phase. What changes the
look of the page stays available -- the pin of the menu, the theme, the
contrast, the color: it touches nothing of the process. An inert item is not
dimmed, as no disabled item of the nav is.

Whether a process goes is said by `is_running()` of `swappBaseResponse`: by
default, it is read in the file of the process the request names, and it is
False when the request names none. Annotate and Setup override it: Annotate
holds its run, as its document requires, Setup holds its installation, and
each reads whether it goes in the file of its process. While a process goes, the help
is not answered:
asking for it is going back to the default view of the app, which then is the
progress.

A page of Annotate or of Setup asked for while it goes, after a reload for
instance, shows its progress and follows it. A page of Convert does not: it
has lost the name of the process. While the progress is in the page of
Convert, its sheet shows it alone.

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
