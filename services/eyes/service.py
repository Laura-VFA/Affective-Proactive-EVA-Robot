import os
import queue
import random
import time
from pathlib import Path
from threading import Event, Lock, Thread

import cv2

from .draw import draw_face, get_face_from_file
from .interpolation import get_in_between_faces


class Eyes:
    WIDTH = 1080
    HEIGHT = 1920

    def __init__(self, faces_dir='services/eyes/faces', face_cache='services/eyes/face_cache'):
        cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

        self.faces_dir = Path(faces_dir)
        self.face_cache = Path(face_cache)

        self.transition_faces = queue.Queue() # Queue for managing and processing the canvas face re-drawings

        self.current_face = 'neutral'
        self.current_face_points = get_face_from_file(self.faces_dir/'neutral.json')
        self.transition_faces.put((self.current_face, self.current_face_points)) # Introduce the first state face in the queue

        self.stopped = Event()
        self.lock = Lock() # Semaphore for concurrent variables access control
        self.start()
    
    def _set(self, face, steps=3):
        if self.current_face != face:
            target_face = get_face_from_file(self.faces_dir/f'{face}.json')

            in_between_faces = get_in_between_faces(self.current_face_points, target_face, steps)
            
            for index, face_points in enumerate(in_between_faces):
                self.transition_faces.put((f'{self.current_face}TO{face}_{index+1}of{steps}', face_points))

            self.transition_faces.put((face,target_face))

            # Update current face
            self.current_face_points = target_face
            self.current_face = face 
    
    def set(self, face):
        with self.lock:
            self._set(face)

    def _run(self):
        next_blink = time.time() + random.randint(4,7) # Time of blink

        while not self.stopped.is_set():
            try:
                name_transition, new_face = self.transition_faces.get(timeout=0.1) # get face to draw from queue
                
                face_file = str(self.face_cache/f'{name_transition}.png')
                if os.path.exists(face_file):
                    canvas = cv2.imread(face_file) # Read the face from cache
                else:
                    canvas = draw_face(new_face, Eyes.WIDTH, Eyes.HEIGHT) # Draw it
                    cv2.imwrite(face_file, canvas) 
                cv2.imshow("window", canvas)

            except queue.Empty: # "A lot" of time without new transitions/faces in the queue
                if time.time() > next_blink: # blink time
                    current_face = self.current_face

                    with self.lock:
                        self._set(f'{current_face}_closed', 1) # Make the blink
                        self._set(current_face, 1)

                    next_blink = time.time() + random.randint(4,7) # Calculate next blink time
                continue
            
            finally:
                if cv2.waitKey(1) == ord('q'): # Close the window
                    break    
                pass

        cv2.destroyAllWindows()      
        
    def start(self):
        self.thread = Thread(target = self._run)
        self.stopped.clear()
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.thread.join()
