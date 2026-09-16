# DEPRECATED

This package implements the SPPAS Workspaces web application: the web version
of the "Files" page of the wxPython interface. Its user-facing name is "Files",
but what it actually manipulates are *workspaces* -- hence the package name
`app_wkps` and the `workspaces.html` page.

## Deployment: local only

This application is never served online. It always runs locally, behind the
local SPPAS web server, on the user's own machine -- never under uWSGI or any
remote/multi-user deployment. It manipulates the local workspaces, files and
references of the person running SPPAS; the "web" here is only the rendering
technology, not a network exposure. Every design decision may therefore assume
a single local user and direct access to the SPPAS data.

## Architecture: to be decided

The `page_files` sub-package dates from 2023. It was written as a proof of
concept -- the very first check of whether a web-based SPPAS interface was
worth pursuing -- and it has not been reworked since. It is currently organized
in the plain *data–processing–interface* style, not in MVC.

Two directions are open, and the choice is deliberately deferred:

- **keep the current implementation style**: data, processing and interface,
  as it stands today;
- **move to MVC**, with a clear separation of transport, controller, model and
  view, exactly like the Dashboard and Setup applications.

Which one is adopted will depend on the upcoming analysis of the existing code:
a synthesis of the needs and a Merise modeling of the workspaces domain. Until
that analysis is done, the PoC is kept as-is: it is the skeleton, not the final
form.
