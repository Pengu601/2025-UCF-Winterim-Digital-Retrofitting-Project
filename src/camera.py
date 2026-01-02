import cv2
import threading
import time

class ThreadedCamera:
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src)
        # Minimize buffer size to reduce latency
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Optional: Set resolution (can be parameterized if needed)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Read the first frame to ensure we have data
        (self.status, self.frame) = self.capture.read()
        
        self.stopped = False

    def start(self):
        # Start the thread to read frames from the video stream
        t = threading.Thread(target=self.update, args=())
        t.daemon = True # Daemon thread exits when main program exits
        t.start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            if self.stopped:
                self.capture.release()
                return

            # Read the next frame from the stream
            (self.status, self.frame) = self.capture.read()
            
            # Small sleep to prevent CPU hogging if camera is slow, 
            # though usually read() blocks until frame is ready.
            # time.sleep(0.001) 

    def read(self):
        # Return the most recent frame
        return self.status, self.frame

    def stop(self):
        # Indicate that the thread should be stopped
        self.stopped = True
