import cv2
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
        """Update the camera feed in the UI"""
        if not hasattr(self, 'camera') or self.camera is None or not self.camera.isOpened():
            return
            
        ret, frame = self.camera.read()
        if not ret:
            return
            
        # Convert the frame to RGB format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get the dimensions of the label
        if hasattr(self.main_window, 'cam_label'):
            label_width = self.main_window.cam_label.width()
            label_height = self.main_window.cam_label.height()
            
            # Resize the frame to fit the label while maintaining aspect ratio
            h, w, ch = frame_rgb.shape
            aspect_ratio = w / h
            
            if label_width / label_height > aspect_ratio:
                # Label is wider than the frame
                new_width = int(label_height * aspect_ratio)
                new_height = label_height
            else:
                # Label is taller than the frame
                new_width = label_width
                new_height = int(label_width / aspect_ratio)
                
            frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
            
            # Convert the frame to QImage
            h, w, ch = frame_resized.shape
            bytes_per_line = ch * w
            q_img = QImage(frame_resized.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Convert QImage to QPixmap and set it to the label
            pixmap = QPixmap.fromImage(q_img)
            self.main_window.cam_label.setPixmap(pixmap)
            self.main_window.cam_label.setAlignment(Qt.AlignCenter)
    
    def release_camera(self):
        """Release camera resources"""
        if hasattr(self, 'camera') and self.camera is not None:
            self.camera.release()
            self.camera = None
