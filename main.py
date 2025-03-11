# Install the following: pip install spidev RPi.GPIO pi-rc522 keyboard


# ---------- Imports ---------- #

import cv2 as cv
import numpy as np

from time import sleep
from PIL import Image
from gpiozero import AngularServo
from pirc522 import RFID

import os, sys, inspect, pytesseract, time, signal, keyboard # type: ignore

# ---------- External Peripheral Creation ---------- #

# Create servo object
servo = AngularServo(18, min_pulse_width = 0.0005, max_pulse_width = 0.0025)

# Create rfid object
rfid = RFID()

# Create camera object
camera = cv.VideoCapture(0)
if not camera.isOpened():
    print("Error: Could not open camera.")
    exit()

# ---------- Testing Rig Code ---------- #

# Array of tests to do
tests = ["OCR", "RFID", "Servo", "CV test", "DB test"]

# A loop to select a test
def selectTest():
    print("Enter a test to run:")
    for test in tests:
        print(tests.index(test), ":", test)
    
    try:
        selectedTestNum = int(input())

        selectedTest = tests[selectedTestNum]
        print("Selected", selectedTest)
        print()

        if selectedTest == "OCR":
            OCRTest()
        elif selectedTest == "RFID":
            RFIDTest()
        elif selectedTest == "Servo":
            ServoTest()
        elif selectedTest == "CV test":
            objectDetector()
        elif selectedTest == "DB test":
            DBTest()

        print("Finshed/exited testing")
    # ValueError means that 'int(input())' failed because the provided value was not a number
    except ValueError:
        print(f"{selectedTestNum} is not a number")
        selectTest()
    # IndexError means that 'tests[selectedTestNum]' failed because the provided number was too high or low
    except IndexError:
        print("That is not an option")
        selectTest()
    # Anything else is just a general exception
    except Exception as e:
        print(f"An exception occured: {e}")
        
# OCR test function
def OCRTest():
    print("Started OCR test")

    while True:
        # Get cam frame and show it
        img = getCameraFrame()
        cv.imshow("img", img)

        # Modify frame for better reading
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        #imgarr = np.array(img)
        # Convert frame to text
        text = pytesseract.image_to_string(img)
        print(f"Gotten text <{text}>")

        if exitOnEsc():
            break

        sleep(1)

# RFID test function
def RFIDTest():
    print("Started RFID test")

    while continueReadingRFID:
        rfid.wait_for_tag()
        (error, tag_type) = rfid.request()
        if not error:
            (error, uid) = rfid.anticoll()
            if not error:
                print("Card detected with UID:", uid)
            
                # Select the scanned tag
                rfid.select_tag(uid)
            
                # Define the default key for MIFARE Classic cards
                default_key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            
                # Choose a block number to work with (avoid sector trailer blocks)
                block_num = 8
            
                # Authenticate the block
                error = rfid.auth(rfid.auth_a, block_num, default_key, uid)
                if error:
                    print("Authentication error on block", block_num)
                else:
                    # Read data from the block
                    data = rfid.read(block_num)
                    print("Data on block", block_num, ":", data)
                
                    # Prepare data to write: must be exactly 16 bytes.
                    # Here we write "Hello, RFID!" and pad with spaces.
                    write_str = "Hello, RFID!"
                    write_data = list(bytearray(write_str.ljust(16), 'utf-8'))
                
                    # Write data to the block
                    error = rfid.write(block_num, write_data)
                    if error:
                        print("Error writing to block", block_num)
                    else:
                        print("Data written successfully!")
                
                    # Stop crypto on the card to finalize the operation
                    rfid.stop_crypto1()
            
                # Pause briefly to avoid processing the same card multiple times
                time.sleep(1)
        if exitOnEsc():
            break
    
# Servo test function
def ServoTest():
    print("Started servo test")
    servo.angle = 0    # Move to 0 degrees
    sleep(2)
    servo.angle = 90   # Move to 90 degrees
    sleep(2)
    servo.angle = 180  # Move to 180 degrees

# Database test function
def DBTest():
    print("Started database test")

    lp1 = "Hippity hoppity, your soul is now my property"
    lp2 = "nuh uh. WHAT DO YOU MEAN NUH UH?"

    # Push normal test
    LPDatabase.push(lp1)
    print("Did push normal test")

    # Push error test
    try:
        LPDatabase.push(lp1)
    except Exception as e:
        print(f"Received exception: {e}")
    print("Did push error test")

    # Pull normal test
    val = LPDatabase.pull(lp1)
    print(val)
    print(f"Did pull normal test: {val}")

    # Pull error test
    try:
        val = LPDatabase.pull(lp2)
    except Exception as e:
        print(f"Received exception: {e}")
    print(val)
    print("Did pull error test")

# Object detector function
def objectDetector():
    while True:
        image = getCameraFrame()

        image_height, image_width, _ = image.shape

        # Sets our input as the image, turns it into a blob
        # Resizes and sets the colour mode to BGR
        model.setInput(cv.dnn.blobFromImage(image, size = (300, 300), swapRB = True))

        # Returns a blob array
        output = model.forward()
        
        for detection in output[0, 0, :, :]:
            confidence = detection[2]
            if confidence > 0.5: # This is our confidence threshold
                class_id = detection[1] # This is the ID of what it thinks it is
                class_name = getIDClassName(class_id,classNames) # Returning the name from Dictionary
                print(str(str(class_id) + " " + str(detection[2]) + " " + class_name))
                
                # Draw the bounding box, scaled to size of the image
                box_x = detection[3] * image_width
                box_y = detection[4] * image_height
                box_width = detection[5] * image_width
                box_height = detection[6] * image_height
                cv.rectangle(image, (int(box_x), int(box_y)), (int(box_width), int(box_height)), (23, 230, 210), thickness = 1)
                
                # Put some text on the bounding box
                cv.putText(image, class_name, (int(box_x), int(box_y + 0.05 * image_height)), cv.FONT_HERSHEY_SIMPLEX, (0.005 * image_width), (0, 0, 255))

        cv.imshow("image", image)

        if exitOnEsc():
            break

# ---------- RFID Payment System ---------- #

def chargeUserMoney():
    pass

# ---------- License Plate Database System ---------- #

class LPDatabase:
    lpDict = {}

    @staticmethod
    def pull(licensePlate):
        if licensePlate in LPDatabase.lpDict:
            val = LPDatabase.lpDict[licensePlate]
            # Pop deletes an entry in a dictionary
            LPDatabase.lpDict.pop(licensePlate)
            return val
        else:
            raise Exception("Unable to fetch time from non-existent entry")

    @staticmethod
    def push(licensePlate):
        if licensePlate in LPDatabase.lpDict:
            raise Exception("A duplicate license plate entry cannot exist")
        else:
            LPDatabase.lpDict[licensePlate] = time.strftime("%H:%M:%S") # Yes. From here: https://stackoverflow.com/questions/14700073/24-hour-format-for-python-timestamp

    @staticmethod
    def printDB():
        for key in LPDatabase.lpDict:
            print(key, LPDatabase.lpDict[key])

# ---------- Quick functions for opening and closing the boomgate ---------- #

def openBoomGate():
    pass

def closeBoomGate():
    pass

# ---------- Util Functions ---------- #

# Function to return name from the dictionary
def getIDClassName(class_id, classes):
    for key, value in classes.items():
        if class_id == key:
            return value

# Find the execution path and join it with the direct reference
def getExecutionPath(filename):
    return os.path.join(os.path.dirname(inspect.getfile(sys._getframe(1))), filename)

# Frame getter
def getCameraFrame():
    ret, frame = camera.read()
    # This should probably have a condition for if the frame fetch fails
    if ret:
        image = cv.resize(frame, (320, 240))
        return image

# Fn for cleaning up handles and resource
def cleanUpAndExit():
    camera.release()
    cv.destroyAllWindows()
    rfid.cleanup()
    exit()

# Fn for exiting on Escape key
def exitOnEsc():
    if cv.waitKey(1) == ESC_KEY:
        return True


# ---------- Object Recognisation Variables ---------- #

# Loading model
model = cv.dnn.readNetFromTensorflow(getExecutionPath("../OpenCV/models/frozen_inference_graph.pb"), getExecutionPath("../OpenCV/models/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"))

# Pretrained classes in the model
classNames = {
    0: "background", 1: "person", 2: "bicycle", 3: "car", 4: "motorcycle", 5: "airplane", 
    6: "bus", 7: "train", 8: "truck", 9: "boat", 10: "traffic light", 11: "fire hydrant",
    13: "stop sign", 14: "parking meter", 15: "bench", 16: "bird", 17: "cat", 18: "dog",
    19: "horse", 20: "sheep", 21: "cow", 22: "elephant", 23: "bear", 24: "zebra",
    25: "giraffe", 27: "backpack", 28: "umbrella", 31: "handbag", 32: "tie",
    33: "suitcase", 34: "frisbee", 35: "skis", 36: "snowboard",
    37: "sports ball", 38: "kite", 39: "baseball bat", 40: "baseball glove",
    41: "skateboard", 42: "surfboard", 43: "tennis racket", 44: "bottle",
    46: "wine glass", 47: "cup", 48: "fork", 49: "knife", 50: "spoon",
    51: "bowl", 52: "banana", 53: "apple", 54: "sandwich", 55: "orange",
    56: "broccoli", 57: "carrot", 58: "hot dog", 59: "pizza", 60: "donut",
    61: "cake", 62: "chair", 63: "couch", 64: "potted plant", 65: "bed",
    67: "dining table", 70: "toilet", 72: "tv", 73: "laptop", 74: "mouse",
    75: "remote", 76: "keyboard", 77: "cell phone", 78: "microwave", 79: "oven",
    80: "toaster", 81: "sink", 82: "refrigerator", 84: "book", 85: "clock",
    86: "vase", 87: "scissors", 88: "teddy bear", 89: "hair drier", 90: "toothbrush"
}

continueReadingRFID = True

# Intended constant for the escape key when using cv.waitKey
ESC_KEY = 27

# Banish this to the Shadow Realm so everything works properly
selectTest()