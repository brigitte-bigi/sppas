import unittest
from unittest.mock import patch, MagicMock

from sppas.ui.wxapp.__main__ import SPPASLauncher


class TestSPPASLauncher(unittest.TestCase):

    def setUp(self):
        """Initialize the SPPASLauncher instance for testing."""
        self.launcher = SPPASLauncher()

    @patch('sys.version_info', (3, 6))  # Mocking Python version to test version check
    def test_check_python_version_warn(self):
        """Test that a warning is issued when Python version is lower than the required."""
        with patch('builtins.print') as mocked_print:
            self.launcher.check_python_version()
            mocked_print.assert_called_with(
                "[ WARNING ] You need to update Python version to launch the application. The GUI of SPPAS requires version 3.7.")

    @patch('sys.version_info', (3, 8))  # Mocking Python version to test version recommendation
    def test_check_python_version_info(self):
        """Test that an info message is displayed when Python version is older than recommended."""
        with patch('builtins.print') as mocked_print:
            self.launcher.check_python_version()
            mocked_print.assert_called_with("[ INFO ] You should consider updating Python to 3.9+.")

    @patch('sppas.__main__.sppasApp')
    @patch('sppas.__main__.sppasLogFile')
    def test_import_dependencies_success(self, MockLogFile, MockApp):
        """Test successful import of dependencies."""
        MockLogFile.return_value = MagicMock()
        MockApp.return_value = MagicMock()

        self.launcher.import_dependencies()

        self.assertEqual(self.launcher.status, 0)
        self.assertIsNotNone(self.launcher.__app)
        self.assertIsInstance(self.launcher.__report, MagicMock)

    #
    # @patch('sppas.__main__.sppasLogFile', new_callable=MagicMock)
    # @patch('sppas.__main__.sppasApp', new_callable=MagicMock)
    # def test_import_dependencies_failure(self, MockLogFile, MockApp):
    #     """Test failure when importing dependencies."""
    #     MockLogFile.side_effect = Exception("Dependency Error")
    #
    #     self.launcher.import_dependencies()
    #
    #     self.assertEqual(self.launcher.status, 1)
    #     self.assertIn("Dependency Error", self.launcher.__error_message)

    # @patch('webbrowser.open')
    # def test_handle_error(self, mock_open):
    #     """Test that the error handling function behaves correctly."""
    #     self.launcher.__error_message = "Test error message"
    #     self.launcher.__status = 1
    #
    #     with patch('builtins.print') as mocked_print:
    #         self.launcher.handle_error()
    #         mocked_print.assert_any_call("Test error message")
    #         mocked_print.assert_any_call(f"* * * * *  SPPAS exited with error number: 0001  * * * * * ")
    #         mock_open.assert_called_with("https://sppas.org/book_09_annexes.html#error-0001")

    @patch('webbrowser.open')
    @patch('sppas.__main__.sppasApp')
    def test_run_wx_application_success(self, MockApp, mock_open):
        """Test successful running of wx application."""
        MockApp.return_value.run.return_value = 0  # Mock the run method to simulate success
        self.launcher.import_dependencies()  # Ensure that dependencies are loaded
        self.launcher.run_wx_application()

        self.assertEqual(self.launcher.status, 0)

    @patch('sppas.__main__.sppasApp')
    def test_run_wx_application_failure(self, MockApp):
        """Test running of wx application when an error occurs."""
        MockApp.return_value.run.side_effect = Exception("Application Error")
        self.launcher.import_dependencies()  # Ensure that dependencies are loaded

        with self.assertRaises(Exception):  # Check that an exception is raised
            self.launcher.run_wx_application()

    @patch('sppas.__main__.sppasLogFile')
    @patch('webbrowser.open')
    def test_write_error_report(self, mock_open, MockLogFile):
        """Test the writing of an error report."""
        mock_report = MagicMock()
        mock_report.get_filename.return_value = "error_report.txt"
        MockLogFile.return_value = mock_report

        self.launcher.__status = 1
        self.launcher.__error_message = "Test error message"
        self.launcher.write_error_report()

        mock_open.assert_called_with(url="error_report.txt")


if __name__ == "__main__":
    unittest.main()
