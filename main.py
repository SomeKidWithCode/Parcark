# Imports
import cv2 as cv
import os, sys, inspect
from PIL import Image
import numpy as np
import pytesseract

# Array of tests to do
tests = ["OCR", "RFID", "Servo", "CV test"]

# A loop to select a test
def selectTest():
    print("Select a test to run:")
    for test in tests:
        print(tests.index(test), ":", test)

    selectedTestNum = input()

    try:
        selectedTest = tests[selectedTestNum]
        #testIndex = tests.index(selectedTest)
        print("Selected", selectedTest)

        if selectedTest == "OCR":
            OCRTest()
        elif selectedTest == "RFID":
            RFIDTest()
        elif selectedTest == "Servo":
            ServoTest()
        elif selectedTest == "CV test":
            objectDetector()
    except Exception as e:
        print(f"An exception occured: {e}")
        print("That is not an option")
        selectTest()

# OCR test function
def OCRTest():
    print("Started OCR test")
    img = getCameraFrame()
    imgarr = np.array(img)
    text = pytesseract.image_to_string(imgarr)

# RFID test function
def RFIDTest():
    print("Started RFID test")

# Servo test function
def ServoTest():
    print("Started servo test")

selectTest()

# 
def getCameraFrame():
    ret, frame = camera.read()
    if ret:
        image = cv.resize(frame, (320, 240))
        return image


# ----- Stuff ----- #

# Attempting to use the webcam to get the image to process
camera = cv.VideoCapture(0)
if not camera.isOpened():
    print("Error: Could not open camera.")
    exit()

# Pretrained classes in the model - Dictionary
classNames = {0: 'background',
              1: 'person', 2: 'bicycle', 3: 'car', 4: 'motorcycle', 5: 'airplane', 6: 'bus',
              7: 'train', 8: 'truck', 9: 'boat', 10: 'traffic light', 11: 'fire hydrant',
              13: 'stop sign', 14: 'parking meter', 15: 'bench', 16: 'bird', 17: 'cat',
              18: 'dog', 19: 'horse', 20: 'sheep', 21: 'cow', 22: 'elephant', 23: 'bear',
              24: 'zebra', 25: 'giraffe', 27: 'backpack', 28: 'umbrella', 31: 'handbag',
              32: 'tie', 33: 'suitcase', 34: 'frisbee', 35: 'skis', 36: 'snowboard',
              37: 'sports ball', 38: 'kite', 39: 'baseball bat', 40: 'baseball glove',
              41: 'skateboard', 42: 'surfboard', 43: 'tennis racket', 44: 'bottle',
              46: 'wine glass', 47: 'cup', 48: 'fork', 49: 'knife', 50: 'spoon',
              51: 'bowl', 52: 'banana', 53: 'apple', 54: 'sandwich', 55: 'orange',
              56: 'broccoli', 57: 'carrot', 58: 'hot dog', 59: 'pizza', 60: 'donut',
              61: 'cake', 62: 'chair', 63: 'couch', 64: 'potted plant', 65: 'bed',
              67: 'dining table', 70: 'toilet', 72: 'tv', 73: 'laptop', 74: 'mouse',
              75: 'remote', 76: 'keyboard', 77: 'cell phone', 78: 'microwave', 79: 'oven',
              80: 'toaster', 81: 'sink', 82: 'refrigerator', 84: 'book', 85: 'clock',
              86: 'vase', 87: 'scissors', 88: 'teddy bear', 89: 'hair drier', 90: 'toothbrush'}

# Function to return name from the dictionary
def id_class_name(class_id, classes):
    for key, value in classes.items():
        if class_id == key:
            return value

# Find the execution path and join it with the direct reference
def execution_path(filename):
  return os.path.join(os.path.dirname(inspect.getfile(sys._getframe(1))), filename)			

  # Loading model
model = cv.dnn.readNetFromTensorflow(execution_path('../OpenCV/models/frozen_inference_graph.pb'), execution_path('../OpenCV/models/ssd_mobilenet_v2_coco_2018_03_29.pbtxt'))

def objectDetector():
    while True:
        image = getCameraFrame()

        image_height, image_width, _ = image.shape

        # Sets our input as the image, turns it into a blob
        # Resizes and sets the colour mode to BGR
        model.setInput(cv.dnn.blobFromImage(image, size=(300, 300), swapRB=True))

        # Returns a blob array
        output = model.forward()
        
        for detection in output[0, 0, :, :]:
            confidence = detection[2]
            if confidence > .5: # This is our confidence threshold
                class_id = detection[1] # This is the ID of what it thinks it is
                class_name=id_class_name(class_id,classNames) # Returning the name from Dictionary
                print(str(str(class_id) + " " + str(detection[2])  + " " + class_name))
                
                # Draw the bounding box, scaled to size of the image
                box_x = detection[3] * image_width
                box_y = detection[4] * image_height
                box_width = detection[5] * image_width
                box_height = detection[6] * image_height
                cv.rectangle(image, (int(box_x), int(box_y)), (int(box_width), int(box_height)), (23, 230, 210), thickness=1)
                
                # Put some text on the bounding box
                cv.putText(image,class_name ,(int(box_x), int(box_y+.05*image_height)),cv.FONT_HERSHEY_SIMPLEX,(.005*image_width),(0, 0, 255))

        cv.imshow('image', image)

        key = cv.waitKey(1)

        if key == 27: # exit on ESC
            break