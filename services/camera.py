import numpy as np
import pyrealsense2.pyrealsense2 as rs
import imutils
from threading import Lock

class Camera:
    def __init__(self) -> None:

        self.active_services = set()

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        self.lock = Lock()

    
    def get_color_frame(self, resize=False):
        frames = self.pipeline.wait_for_frames()
        color_image = np.asanyarray(frames.get_color_frame().get_data())
        if not resize:
            return color_image

        return imutils.resize(color_image, width=500)
    
    def start(self, service):
        with self.lock:
            if not self.active_services:
                self.pipeline.start(self.config)
            
            self.active_services.add(service)

    
    def stop(self, service):
        with self.lock:
            if not self.active_services:
                return

            self.active_services.discard(service)

            if not self.active_services:
                self.pipeline.poll_for_frames() # clear last frame buffer
                self.pipeline.stop()
