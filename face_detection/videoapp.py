#from mytflite import performDetects
#from rekognitionFaces import *
from flask import Flask, render_template, Response
from flask_cors import CORS, cross_origin
import cv2
import sys
sys.path.append('/home/ec2-user/video-server')
from threading import Thread
import os
import time
import numpy as np

class VideoStream:
    """class that grabs the video frames in a seperate thread  requires uswgi master=false and threads=enabled"""
    def __init__(self,stream_url,resolution=(640,480),framerate=30):
        self.stream = cv2.VideoCapture(stream_url)
        while not self.stream.isOpened():
            self.stream = cv2.VideoCapture(stream_url)
            time.sleep(10)
            print("Unable to open stream - {}  Waiting for 10 seconds...".format(str(stream_url)))
            #raise Exception("Could not open video stream")
        # ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])

        # Check success
        if not self.stream.isOpened():
            raise Exception("Could not open video stream")

        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

        # Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
        # Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()
            #time.sleep(0.10)

    def read(self):
        # Return the most recent frame
        return self.frame

    def stop(self):
        # Indicate that the camera and thread should be stopped
        self.stopped = True

app = Flask(__name__)

# Initialize video stream
#videoStreamUrl = "http://192.168.5.220:8080/?action=stream_0" # stream_0 is the raw video stream  stream_1 is the labeled video stream
videostream = VideoStream(sys.argv[1]).start()



time.sleep(1)

#camera = cv2.VideoCapture(videoStreamUrl)

""" if not camera.isOpened():
    print('Cannot open RTSP stream - start edge capture/streaming processes first')
    exit(-1) """

faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eyeCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

def get_faces(img):
    #https://www.mygreatlearning.com/blog/real-time-face-detection/
    #https://www.bogotobogo.com/python/OpenCV_Python/python_opencv3_Image_Object_Detection_Face_Detection_Haar_Cascade_Classifiers.php

        # converting image from color to grayscale
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    """ cols, rows = img.shape
    brightness = np.sum(img) / (255 * cols * rows)
    minimum_brightness = 0.66
    imgGray = cv2.convertScaleAbs(imgGray, alpha = 1, beta = 255 * (minimum_brightness - brightness)) """

    # Getting corners around the face
    # 1.3 = scale factor, 5 = minimum neighbor can be detected
    faces = faceCascade.detectMultiScale(imgGray, 1.25, 3)

    # drawing bounding box around face
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0,   0), 2)
        cv2.putText(img, 'face', (x, y-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text
        roi_gray = imgGray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]
        eyes = eyeCascade.detectMultiScale(roi_gray)
        for (ex,ey,ew,eh) in eyes:
            cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
            cv2.putText(roi_color, 'eye', (x, y-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text

    return img

def gen_frames():  # generate frame by frame from camera
    while True:
        # Capture frame-by-frame
        #success, frame = camera.read()  # read the camera frame
        # Grab frame from video stream
        frame1 = videostream.read()
        frame = frame1.copy()

        frame = get_faces(frame) # get faces via local inference
        #frame = detectFacesFrame(frame)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/portrait')
def portrait():
    """Video streaming home page. Portrait"""
    return render_template('portrait.html')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('landscape.html')



if __name__ == '__main__':
    app.run(debug=True)
