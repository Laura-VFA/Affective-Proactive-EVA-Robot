import queue
import random
import time
from pathlib import Path
from threading import Event, Lock, Thread

import cv2

from .draw import draw_face, get_face_from_file
from .interpolation import get_in_between_faces


class EvaEyes:
    WIDTH = 1080
    HEIGHT = 1920

    def __init__(self, faces_dir='services/eyes/faces'):
        cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

        self.faces_dir = Path(faces_dir)

        self.transition_faces = queue.Queue()

        self.current_face = 'neutral'
        self.current_face_points = get_face_from_file(self.faces_dir/'neutral.json')
        self.transition_faces.put(self.current_face_points)
        self.stopped = Event()
        self.lock = Lock()
        self.start()
    
    def _set(self, face):
        if self.current_face != face:
            target_face = get_face_from_file(self.faces_dir/f'{face}.json')

            in_between_faces = get_in_between_faces(self.current_face_points, target_face, 2)
            
            for face_points in in_between_faces:
                self.transition_faces.put(face_points)

            self.transition_faces.put(target_face)

            # update current face
            self.current_face_points = target_face
            self.current_face = face 
    
    def set(self, face):
        with self.lock:
            self._set(face)

    def _run(self):
        next_blink = time.time() + random.randint(4,7)

        while not self.stopped.is_set():
            try:
                new_face = self.transition_faces.get(timeout=0.1)
                print('start drawing')
                aux = time.time()
                canvas = draw_face(new_face, EvaEyes.WIDTH, EvaEyes.HEIGHT)
                print(time.time()-aux)
                
                #cv2.imshow("window", canvas)
                #time.sleep(0.033)
            except queue.Empty:
                if time.time() > next_blink: # blink time
                    current_face = self.current_face

                    with self.lock:
                        self._set(f'{current_face}_closed')
                        self._set(current_face)

                    next_blink = time.time() + random.randint(4,7)
                continue
            finally:
                #if cv2.waitKey(1) == ord('q'):
                #    break    
                pass

        cv2.destroyAllWindows()      
        
    def start(self):
        self.thread = Thread(target = self._run)
        self.stopped.clear()
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.thread.join()
