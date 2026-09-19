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
state required by the controller and the view.

This architecture ensures a strict separation between transport (HTTP),
application logic (Controller), data (Model), and presentation (View).
It improves testability, maintainability, and the long-term portability of the
Setup application, regardless of the underlying web server implementation.

