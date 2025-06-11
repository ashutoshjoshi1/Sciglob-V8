import cv2
import os
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QImage, QPixmap

class CameraManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.camera = None
    
    def init_camera(self):
        """Initialize the camera"""
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            if hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage("Warning: Could not open camera")
        else:
            if hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage("Camera initialized")
    
    def update_camera_feed(self):
        """Update the camera feed in the UI with error handling for resize issues"""
        if not hasattr(self, 'camera') or self.camera is None:
            return
        
        try:
            # Check if camera is opened
            if not self.camera.isOpened():
                return
            
            ret, frame = self.camera.read()
            if not ret or frame is None or frame.size == 0:
                return
            
            # Convert the frame to RGB format
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Get the dimensions of the label
            if not hasattr(self.main_window, 'cam_label'):
                return
            
            label_width = self.main_window.cam_label.width()
            label_height = self.main_window.cam_label.height()
            
            if label_width <= 0 or label_height <= 0:
                return  # Skip resize if label has invalid dimensions
            
            # Get original frame dimensions
            h, w, ch = frame_rgb.shape
            if h <= 0 or w <= 0:
                return  # Skip if frame has invalid dimensions
            
            # Calculate aspect ratio and new dimensions
            aspect_ratio = w / h
            
            if label_width / label_height > aspect_ratio:
                # Label is wider than the frame
                new_width = max(1, int(label_height * aspect_ratio))
                new_height = max(1, label_height)
            else:
                # Label is taller than the frame
                new_width = max(1, label_width)
                new_height = max(1, int(label_width / aspect_ratio))
            
            # Try to resize the frame, catch specific resize errors
            try:
                frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
            except cv2.error as e:
                # Silently ignore resize errors
                # This catches the "inv_scale_x > 0" assertion error
                return
            
            # Convert the frame to QImage
            h, w, ch = frame_resized.shape
            bytes_per_line = ch * w
            q_img = QImage(frame_resized.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Convert QImage to QPixmap and set it to the label
            pixmap = QPixmap.fromImage(q_img)
            self.main_window.cam_label.setPixmap(pixmap)
            self.main_window.cam_label.setAlignment(Qt.AlignCenter)
        
        except Exception as e:
            # Log other errors instead of silently ignoring, to aid debugging.
            # In a production app, this might go to a logging framework.
            print(f"Error in update_camera_feed: {e}")
            # Optionally, could set a placeholder image or message on cam_label on error.
            pass
    
    def release_camera(self):
        """Release camera resources"""
        if hasattr(self, 'camera') and self.camera is not None:
            self.camera.release()
            self.camera = None

    def save_image(self, full_path_filename):
        if not hasattr(self, 'camera') or self.camera is None or not self.camera.isOpened():
            print("Camera not initialized or not open. Cannot save image.")
            # Optionally, emit a signal or use main_window.statusBar() if accessible and appropriate
            if hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage("Error: Camera not available to save image.")
            return False

        ret, frame = self.camera.read()
        if not ret or frame is None:
            print("Failed to capture frame from camera. Cannot save image.")
            if hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage("Error: Failed to capture frame for saving.")
            return False

        try:
            # Ensure the directory for the file exists
            directory = os.path.dirname(full_path_filename)
            if directory and not os.path.exists(directory): # Check if directory string is not empty
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
                if hasattr(self.main_window, 'statusBar'):
                    self.main_window.statusBar().showMessage(f"Info: Created directory {directory}")


            cv2.imwrite(full_path_filename, frame)
            print(f"Camera image saved successfully to {full_path_filename}")
            if hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage(f"Success: Image saved to {full_path_filename}")
            return True
        except Exception as e:
            print(f"Error saving camera image to {full_path_filename}: {e}")
            if hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage(f"Error: Could not save image: {e}")
            return False
