# for face landmark detection
import pickle
import time
from threading import Event, Thread

import cv2
import face_recognition
import imutils
import numpy as np
import pyrealsense2.pyrealsense2 as rs
from fdlite import FaceDetection, FaceDetectionModel, FaceIndex
from imutils.video import FPS
from PIL import Image

data = pickle.loads(open('./encodings.pickle', "rb").read())

class Wakeface:
    def __init__(self, callback):
        self.callback = callback
        self.stopped = Event()
        self._thread = None

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        
        # load detection models
        self.detect_faces = FaceDetection(model_type=FaceDetectionModel.FRONT_CAMERA) # BACK_CAMERA FOR MORE RESOLUTION ; SHORT?
        
    def start(self):
        print("[INFO] starting video stream...")
        # Start streaming
        self.pipeline.start(self.config)

        self.stopped.clear()
        self._thread = Thread(target=self._run)
        self._thread.start()
    
    def _run(self):
        self.fps = FPS().start()

        someone_was_looking = False

        while not self.stopped.is_set():
            frames = self.pipeline.wait_for_frames()

            color_frame = frames.get_color_frame()
            color_image = np.asanyarray(color_frame.get_data())
            color_image = imutils.resize(color_image, width=500)

            (h, w) = color_image.shape[:2]

            img2 = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            img2 = Image.fromarray(img2)

            # detect face
            face_detections = self.detect_faces(img2)

            
            if len(face_detections):
                bboxes_looking = []
                someone_looking = False

                for face in face_detections:
                    # WAKEFACE
                    xr, yr = face[FaceIndex.RIGHT_EYE_TRAGION]
                    xl, yl = face[FaceIndex.LEFT_EYE_TRAGION]
                    xn, yn = face[FaceIndex.NOSE_TIP]

                    # Range mapping
                    xn = (xn - xl) / (xr - xl)
                    xl = 0
                    xr = 1

                    # Interval checking
                    incr = 0.25
                    if (xl + incr)  <= xn <= (xr - incr) :  # and yn >= max(yl, yr)
                        someone_looking = True
                        bboxes_looking.append(face.bbox.scale((w, h)))
                        #break
  
                if someone_looking : 
                    self.callback('face_listen')

                    if not someone_was_looking:
                        # FACE RECOGNITION  
                        names = self.recognize(color_image, bboxes_looking)
                        print(names)

                    someone_was_looking = True

                else:
                    self.callback('face_not_listen') 
                    someone_was_looking = False      
                    
            else:
                self.callback('not_faces')
                someone_was_looking = False 
            
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
        
    # https://pyimagesearch.com/2018/06/25/raspberry-pi-face-recognition/
    def recognize(self, frame, bboxes_looking):
        # FACE RECOGNITION   
        boxes = [(int(box.ymin), int(box.xmax), int(box.ymax), int(box.xmin)) for box in bboxes_looking]
        
        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(frame, boxes)
        names = []
        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(data["encodings"],
                encoding)
            name = "Unknown"
            # check to see if we have found a match
            if True in matches:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)
            
            # update the list of names
            names.append(name)
        
        return names

