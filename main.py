import sys
import traceback # Added for detailed error information
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, Qt
from gui.main_window import MainWindow

def main():
    #Set high DPI attributes BEFORE creating QApplication
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    
    # Enable automatic scaling based on screen DPI
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    
    # Now create the application
    app = QApplication(sys.argv)
    
    # Set application style for better cross-platform appearance
    app.setStyle('Fusion')  # Fusion style works well with custom stylesheets
    
    # Disable complex animations for better performance
    app.setEffectEnabled(Qt.UI_AnimateCombo, False)
    app.setEffectEnabled(Qt.UI_AnimateTooltip, False)
    
    # Set up exception handling for clean exit
    sys._excepthook = sys.excepthook
    # tb is the conventional name for the traceback object in excepthook
    def exception_hook(exctype, value, tb):
        """Handle uncaught exceptions and show error message"""
        sys._excepthook(exctype, value, tb) # This will typically print to stderr
        # Also, show a user-friendly dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(f"An unexpected error occurred: {exctype.__name__}")
        msg.setInformativeText(str(value))
        msg.setWindowTitle("Application Error")
        # Use the traceback module to format the traceback for the detailed text
        detailed_traceback = "".join(traceback.format_exception(exctype, value, tb))
        msg.setDetailedText("Traceback:\n" + detailed_traceback)
        msg.exec_()
    sys.excepthook = exception_hook
    
    # Splash screen
    splash_pix = QPixmap("asset/splash.jpg")
    if not splash_pix.isNull():
        splash = QSplashScreen(splash_pix)
        splash.show()
        app.processEvents()
    
    # Create main window
    win = MainWindow()
    
    # Override the close behavior at the application level
    def confirm_exit():
        # This function will be called when the application is about to quit
        reply = QMessageBox.question(
            win, 'Exit Confirmation',
            'Do you want to quit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Call MainWindow's method to handle resource cleanup
            if hasattr(win, 'shutdown_resources'):
                try:
                    win.shutdown_resources()
                except Exception as e:
                    print(f"Error during shutdown_resources: {e}") # Keep for console/log
                    error_msg = QMessageBox()
                    error_msg.setIcon(QMessageBox.Warning)
                    error_msg.setText("Error during application cleanup.")
                    error_msg.setInformativeText(f"Some resources may not have been released properly: {e}")
                    error_msg.setWindowTitle("Shutdown Warning")
                    error_msg.exec_()
            
            # Allow the application to quit
            QTimer.singleShot(500, app.quit) # Delay might be for UI messages to show
        else:
            # Prevent the application from quitting
            app.setQuitOnLastWindowClosed(False)
            # QTimer.singleShot(0, ...) schedules the lambda to be called after the current
            # event (handling the QMessageBox 'No' response) has finished processing.
            # This ensures that QuitOnLastWindowClosed is reset to True, so that if the
            # user closes the window again (or another window if multiple are open),
            # the application can quit as expected. If not reset, the app might become
            # unclosable via normal window close operations after saying 'No' once.
            QTimer.singleShot(0, lambda: app.setQuitOnLastWindowClosed(True))
    
    # Connect the aboutToQuit signal to our handler
    app.aboutToQuit.connect(confirm_exit)
    
    win.show()
    
    if 'splash' in locals() and splash is not None: # Ensure splash object exists
        splash.finish(win)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
