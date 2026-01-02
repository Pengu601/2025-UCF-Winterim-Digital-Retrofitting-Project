import cv2
import threading
import time

# Dedicated Camera Class with Multi-threading capabilities for increased FPS
class ThreadedCamera:
    def __init__(self, src=0):
        # Initialize video camera
        self.capture = cv2.VideoCapture(src)

        # Minimize buffer size to reduce latency
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Set resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Read the first frame to ensure we have data
        (self.status, self.frame) = self.capture.read()
        
        # Used as a flag to stop the thread when needed
        self.stopped = False

    # Start the thread to read frames from the video stream
    def start(self):

        t = threading.Thread(target=self.update, args=())
        t.daemon = True # Daemon thread exits when main program exits
        t.start()
        return self

    # Updates the current frame read from the video stream to buffer
    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            if self.stopped:
                self.capture.release()
                return

            # Read the next frame from the stream
            (self.status, self.frame) = self.capture.read()

    # Return most recent frame from the buffer
    def read(self):

        return self.status, self.frame

    # Stop the thread
    def stop(self):

        self.stopped = True
