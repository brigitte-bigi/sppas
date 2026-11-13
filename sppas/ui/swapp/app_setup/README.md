This package implements the SPPAS Setup web application using a strict
Model–View–Controller (MVC) architecture with a clear separation of concerns.

- **swappSetupResponseRecipe** acts as the HTTP transport layer.
It handles request parsing, event dispatching, HTTP status management, and
response serialization. It does not implement business logic and remains
independent of the application state and UI structure.

- **swappSetupController** is the MVC controller.
It manages application logic, fieldset progression, installation workflow,
dependency selection, and state transitions. It interacts with the model and
delegates all HTML structural updates to the view. It remains independent
from any HTTP framework.

- **swappSetupView** is the View component responsible for constructing and
updating the HTMLTree structure (header, fieldsets, actions, footer).
It encapsulates all presentation-related logic and ensures that the HTML
representation follows the current state provided by the controller.

- **swappSetupModel** represents the application data.
It encapsulates the dependency objects (sppasInstallerDeps) and exposes the
state required by the controller and the view. It is the only place where a
choice is held: what is to be installed, what the person accepted, and which
feature can be installed on the machine.

- **swappSetupFieldsets** creates the fieldset nodes for the view. A fieldset
holding choices is created anew each time it is shown, and written from the
model: no fieldset keeps a state of its own. The index of the fieldset which
is shown is held by the controller.

A click on a checkbox is sent to the server, which changes the model and
answers the state of each checkbox the page has to show. The JavaScript of
the page displays that answer and decides nothing.

This architecture ensures a strict separation between transport (HTTP),
application logic (Controller), data (Model), and presentation (View).
It improves testability, maintainability, and the long-term portability of the
Setup application, regardless of the underlying web server implementation.

