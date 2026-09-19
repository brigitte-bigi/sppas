This package implements the SPPAS Dashboard web application following a
Model–View–Controller (MVC) architecture with a clear separation of concerns.

- **swappDashboardResponseRecipe** acts as the *HTTP transport layer*. It handles
  request/response flow, HTTP status management, and page delivery to the client.
  It must remain focused on communication and response serialization.

- **swappDashboardController** represents the *MVC controller*.
  It manages the application logic: updating internal states such as user
  agreement, interacting with the model (e.g., list of swappWebApplicationInfo
  instances), and invoking the view to construct the HTML representation of the
  dashboard.

- **swappDashboardView** is the *View* component responsible for building the static
  and dynamic HTML structure (head, header, body, footer, scripts) using
  WhakerPy's HTMLTree utilities.

- **swappDashboardModel** is represented by the set of application descriptors
  (`swappWebApplicationInfo` objects) managed by the controller and displayed in the
  dashboard as interactive cards.

This structure ensures a clean separation between transport (HTTP),
application logic (Controller), data (Model), and presentation (View), improving
maintainability and scalability of the SPPAS web interface.

