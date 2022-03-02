import cv2
import boto3
import time
import json
from PIL import Image, ImageDraw, ExifTags
from numpy import asarray

def drawBounds(frame,response):
    """ Draw bounding boxes around faces """
    left = 0
    top = 0

    imgWidth = 640
    imgHeight = 480

    for faceDetail in response['FaceDetails']:
        box = faceDetail['BoundingBox']
        left = int(imgWidth * box['Left'])
        top = int(imgHeight * box['Top'])
        width = int(imgWidth * box['Width'])
        height = int(imgHeight * box['Height'])

        pt1 = (left,top)
        pt2 = (left+width,top+height)

        linecolor = (0, 255,   0)
        thickness = 3
        # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255,   0), 3)
        frame = cv2.rectangle(frame, pt1, pt2, linecolor, thickness)

    return frame # must be same format as original frame

def detectFacesFrame(frame):
    """ Detect faces in frame using Rekognition API """
    attributes = ["DEFAULT"]

    hasFrame, imageBytes = cv2.imencode(".jpg", frame)
    if hasFrame:
       session = boto3.session.Session()
       rekognition = session.client('rekognition')
       response = rekognition.detect_faces(Image={'Bytes': imageBytes.tobytes()},Attributes=attributes)
       newFrame = drawBounds(frame,response)

    return(newFrame)

def main():
    print("!!! only include as module  !!!")

if __name__ == "__main__":
    main()

