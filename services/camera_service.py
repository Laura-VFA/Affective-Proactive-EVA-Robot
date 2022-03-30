import pickle
import time
from threading import Event, Thread
import json
import queue

import cv2
import face_recognition
from fdlite import FaceDetection, FaceDetectionModel, FaceIndex
from imutils.video import FPS
from PIL import Image
from .camera import Camera
from .presence_detector.object_detector import ObjectDetector
from .presence_detector.object_detector import ObjectDetectorOptions

#dict_encodings = pickle.loads(open('./encodings.json', "r").read())

class FaceDB:
    dict_encodings = None
    encodings_file = None

    @staticmethod
    def load(encodings_file='./encodings.json'):
        FaceDB.encodings_file = encodings_file

        with open(encodings_file) as json_file:
            FaceDB.dict_encodings = json.load(json_file)
    
    @staticmethod
    def dump():
        with open(FaceDB.encodings_file, 'w') as json_file:
            json.dump(FaceDB.dict_encodings, json_file)



class CameraService:
    camera = None
    def __init__(self) -> None:
        if not CameraService.camera:
            CameraService.camera = Camera()


class Wakeface(CameraService):
    
    def __init__(self, callback):
        super().__init__()

        self.callback = callback
        self.stopped = Event()
        self._thread_wakeface = None
        self._thread_recognizer = None

        self.face_queue = None
        
        # load detection models
        self.detect_faces = FaceDetection(model_type=FaceDetectionModel.FRONT_CAMERA) # BACK_CAMERA FOR MORE RESOLUTION ; SHORT?
        
        
    def start(self):

        self.stopped.clear()
        self._thread_wakeface = Thread(target=self._run)
        self._thread_recognizer = Thread(target=self._run_recognize)
        self._thread_wakeface.start()
        self._thread_recognizer.start()
        
    
    def _run(self):

        CameraService.camera.start(self.__class__.__name__)

        self.fps = FPS().start()

        someone_was_looking = False

        while not self.stopped.is_set():
            # Get frame
            frame = CameraService.camera.get_color_frame(resize=True)
            (h, w) = frame.shape[:2]

            # Detect faces
            face_detections = self.detect_faces(
                Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            )
            
            if not face_detections :
                self.callback('not_faces')
                while not self.face_queue.empty(): self.face_queue.get(block=True)
                someone_was_looking = False 

            else:
                bboxes_looking = [ # Filter looking faces
                    face.bbox.scale((w, h))
                    for face in face_detections
                    if Wakeface.check_looking(face)
                ]
  
                if not bboxes_looking : # No one looking
                    self.callback('face_not_listen') 
                    while not self.face_queue.empty(): self.face_queue.get(block=False)
                    someone_was_looking = False   

                else:
                    self.callback('face_listen')

                    if not someone_was_looking: # Someone looking the first time
                        someone_was_looking = True

                        # FACE RECOGNITION  
                        self.face_queue.put({
                            'frame': frame,
                            'bboxes_looking': bboxes_looking
                        })
                
            self.fps.update()
    
    def stop(self):
        self.stopped.set()
        if self._thread_recognizer is not None and self._thread_recognizer.is_alive():
            self._thread_recognizer.join()
        
        if self._thread_wakeface is not None and self._thread_wakeface.is_alive():
            self._thread_wakeface.join()

        CameraService.camera.stop(self.__class__.__name__)

        self.fps.stop()
        print("[INFO] elasped time: {:.2f}".format(self.fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}".format(self.fps.fps()))

    @staticmethod
    def check_looking(face, incr=0.25):
        # WAKEFACE
        xr, yr = face[FaceIndex.RIGHT_EYE_TRAGION]
        xl, yl = face[FaceIndex.LEFT_EYE_TRAGION]
        xn, yn = face[FaceIndex.NOSE_TIP]

        # Range mapping
        xn = (xn - xl) / (xr - xl)
        xl = 0
        xr = 1

        # Interval checking
        return (xl + incr)  <= xn <= (xr - incr)  # and yn >= max(yl, yr)

    def _run_recognize(self):
        self.face_queue = queue.Queue()

        while not self.stopped.is_set():
            try:
                recognition_params = self.face_queue.get(timeout=.5)
            except queue.Empty:
                continue
            
            names = self.recognize(**recognition_params)
            self.callback('face_recognized', username=names[0])
        
    # https://pyimagesearch.com/2018/06/25/raspberry-pi-face-recognition/
    def recognize(self, frame, bboxes_looking):
        boxes = [(int(box.ymin), int(box.xmax), int(box.ymax), int(box.xmin)) for box in bboxes_looking]
        
        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(frame, boxes)
        names = []
        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(FaceDB.dict_encodings["encodings"],
                encoding)
            name = None
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
                    name = FaceDB.dict_encodings["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)
            
            # update the list of names
            names.append(name)
        
        return names
    

class RecordFace(CameraService):
    def __init__(self, callback):
        super().__init__()

        self.callback = callback
        self.stopped = Event()
        self._thread = None
        
        # load detection models
        self.detect_faces = FaceDetection(model_type=FaceDetectionModel.FRONT_CAMERA) # BACK_CAMERA FOR MORE RESOLUTION ; SHORT?

        
    def start(self, name):

        self.stopped.clear()
        self._thread = Thread(target=self._run, args=(name,))
        self._thread.start()
    
    def _run(self, name, n_frames=6):

        CameraService.camera.start(self.__class__.__name__)
        
        counter = 0
        while counter < n_frames and not self.stopped.is_set():
            print('recording frame!!')
            # Get frame
            frame = CameraService.camera.get_color_frame(resize=True)
            (h, w) = frame.shape[:2]

            # Detect faces
            face_detections = self.detect_faces(
                Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            )

            if face_detections:

                bboxes_looking = [ # Filter looking faces
                    face.bbox.scale((w, h))
                    for face in face_detections
                    if Wakeface.check_looking(face)
                ]
 
                if bboxes_looking:

                    # get encodings 
                    boxes = [(int(box.ymin), int(box.xmax), int(box.ymax), int(box.xmin)) for box in bboxes_looking]
                    
                    # compute the facial embeddings for each face bounding box
                    encodings = face_recognition.face_encodings(frame, boxes)
                    encoding = encodings[0]
                    FaceDB.dict_encodings['encodings'].append(encoding.tolist())
                    FaceDB.dict_encodings['names'].append(name)
                    counter += 1

                    self.callback('recording_face', progress=counter*100/n_frames)

        FaceDB.dump()
        
        CameraService.camera.stop(self.__class__.__name__)


    def stop(self):
        self.stopped.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()



        
class PresenceDetector(CameraService):
    # Based on:
    # Copyright 2021 The TensorFlow Authors. All Rights Reserved.
    #
    # Licensed under the Apache License, Version 2.0 (the "License");
    # you may not use this file except in compliance with the License.
    # You may obtain a copy of the License at
    #
    #     http://www.apache.org/licenses/LICENSE-2.0
    #
    # Unless required by applicable law or agreed to in writing, software
    # distributed under the License is distributed on an "AS IS" BASIS,
    # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    # See the License for the specific language governing permissions and
    # limitations under the License.

    def __init__(self, callback, model='./presence_detector/efficientdet_lite0.tflite', 
                    num_threads=1) -> None:

        super().__init__()

        self.callback = callback
        self.stopped = Event()
        self._thread = None

          # Initialize the object detection model
        options = ObjectDetectorOptions(
            num_threads=num_threads,
            score_threshold=0.3,
            max_results=3,
            label_allow_list = ['person']
        )
        self.detector = ObjectDetector(model_path=model, options=options)
    
    def start(self):

        self.stopped.clear()
        self._thread = Thread(target=self._run)
        self._thread.start()
    
    def _run(self):
        CameraService.camera.start(self.__class__.__name__)
        while not self.stopped.is_set():
            frame = CameraService.camera.get_color_frame(resize=True)

            # Run object detection estimation using the model.
            detections = self.detector.detect(frame)

            if detections:
                self.callback('person_detected')
            else:
                self.callback('empty_room')


    def stop(self):
        self.stopped.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()
        
        CameraService.camera.stop(self.__class__.__name__)

