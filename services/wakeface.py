# for face landmark detection
import time
from threading import Event, Thread

import cv2
import imutils
import numpy as np
import pyrealsense2.pyrealsense2 as rs
from fdlite import FaceDetection, FaceDetectionModel, FaceIndex
from imutils.video import FPS
from PIL import Image


class Wakeface:
    def __init__(self, callback):
        self.callback = callback
        self.stopped = Event()
        self._thread = None

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        
        # load detection models
        self.detect_faces = FaceDetection(model_type=FaceDetectionModel.FRONT_CAMERA) # BACK_CAMERA FOR MORE RESOLUTION
        
    def start(self):
        print("[INFO] starting video stream...")
        # Start streaming
        self.pipeline.start(self.config)

        self.stopped.clear()
        self._thread = Thread(target=self._run)
        self._thread.start()
    
    def _run(self):
        self.fps = FPS().start()
        

        while not self.stopped.is_set():
            frames = self.pipeline.wait_for_frames()

            color_frame = frames.get_color_frame()
            color_image = np.asanyarray(color_frame.get_data())
            color_image = imutils.resize(color_image, width=500)

            (h, w) = color_image.shape[:2]

            img = color_image

            img2 = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            img2 = Image.fromarray(img2)

            # detect face
            face_detections = self.detect_faces(img2)
            if len(face_detections):
                
                someone_looking = False
                for face in face_detections:
                    xr, yr = face[FaceIndex.RIGHT_EYE_TRAGION]
                    xl, yl = face[FaceIndex.LEFT_EYE_TRAGION]
                    xn, yn = face[FaceIndex.NOSE_TIP]
                    
                    #img = cv2.circle(img, (int(xr*w), int(yr*h)), 4, (255, 0, 0), 3)
                    #img = cv2.circle(img, (int(xl*w), int(yl*h)), 4, (255, 0, 0), 3)
                    #img = cv2.circle(img, (int(xn*w), int(yn*h)), 4, (255, 0, 0), 3)

                    # Range mapping
                    xn = (xn - xl) / (xr - xl)
                    xl = 0
                    xr = 1

                    # Interval checking
                    incr = 0.25
                    if (xl + incr)  <= xn <= (xr - incr) :  # and yn >= max(yl, yr)
                        someone_looking = True
                        break

                
                if someone_looking : 
                    self.callback('face_listen')
                else:
                    self.callback('face_not_listen')          
                    
            else:
                self.callback('not_faces')
            
            self.fps.update()
    
    def stop(self):
        self.stopped.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

        self.pipeline.poll_for_frames()
        self.pipeline.stop()
        self.fps.stop()
        print("[INFO] elasped time: {:.2f}".format(self.fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}".format(self.fps.fps()))
        




