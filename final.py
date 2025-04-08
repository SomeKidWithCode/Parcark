# This is the final build file #

# ---------- Imports ---------- #

import cv2 as cv
import numpy as np
import RPi.GPIO as GPIO

from time import sleep
from gpiozero import AngularServo
from mfrc522 import SimpleMFRC522

import pytesseract, time, re

# ---------- Constant Variables ---------- #

# Intended constant for the escape key when using cv.waitKey
ESC_KEY = 27

# Intended constant for the amount of money charged when exiting
CHARGE_RATE = 5

# ---------- External Peripheral Creation ---------- #

# Create servo object
servo = AngularServo(18, min_pulse_width = 0.0005, max_pulse_width = 0.0025)

# Create rfid object
rfid = SimpleMFRC522()

# Create camera object
camera = cv.VideoCapture(0)
if not camera.isOpened():
    print("Error: Could not open camera.")
    exit()

def mainLoop():
    getOCRResult()

def getOCRResult():
    sameResultCount = 0
    ocrRes = None

    while True:
        # Get cam frame
        img = getCameraFrame()

        if img is None:
            continue

        # Modify frame for better reading
        img = cv.resize(img, (320, 120))

        # Turn the image into a ndarray object
        # This is NumPy's class for array manipulation
        img = np.array(img)

        # Create an empty array using the dimensions of the img
        img_empty = np.zeros((img.shape[0], img.shape[1]))

        # Apply various image modifactions to make text reading easier

        # Convert image from normal colorspace to grayscale colorspace
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Applies normalisation. Since I can't understand the documentation for this, I assume that it means mapping the colors of the array
        img = cv.normalize(img, img_empty, 0, 255, cv.NORM_MINMAX)
        # According to the docs, applies a threshold mechanic, as to effectively limit pixels colors whose values are to small or large
        img = cv.threshold(img, 100, 255, cv.THRESH_BINARY)[1]
        # This applies a Gaussian filter. Magic really.
        img = cv.GaussianBlur(img, (1, 1), 0)

        # Show the fully modified image
        cv.imshow("Camera Vision", img)

        # Obtain the raw processed text
        text = pytesseract.image_to_string(img)

        # Use RegEx to filter the output so only characters we expect are outputted
        filteredText = "".join(re.findall("[0-9a-zA-Z-]", text))

        if ocrRes == filteredText and ocrRes != "":
            sameResultCount = sameResultCount + 1
        else:
            ocrRes = filteredText
            sameResultCount = 0

        if sameResultCount == 5:
            break
        
        print(f"result: {ocrRes}, same res count: {sameResultCount}")

        if exitOnEsc():
            break
    
    print(f"final result: {ocrRes}")

#def 

# ---------- Testing Rig Code ---------- #

# RFID test function
def RFIDTest():
    print("Started RFID test")

    try:
        while True:
            print("Hold tag near reader")
            tag_id, text = rfid.read()
            print(f"ID: {tag_id}\nData: {text}")
            rfid.write("E")
    except KeyboardInterrupt:
        GPIO.cleanup()

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

# ---------- RFID Payment System ---------- #

def chargeUserMoney():
    try:
        print("Present credit card")
        _, text = rfid.read()
        storedMoney = int(text)
        print(f"Current card balance: ${storedMoney}")
        print(f"Current charge rate: ${CHARGE_RATE}")
        
        if storedMoney >= CHARGE_RATE:
            storedMoney -= CHARGE_RATE
            rfid.write(str(storedMoney))
            print(f"New card balance: ${storedMoney}")
        else:
            print("*Credit card declines*")
            print("You do not have enough cash. Prepare to die.")
        
    except ValueError:
        print("The rfid tag presented has not been formatted properly. Please use the \'Mon hax\' test to set card data")
    except Exception as e:
        print(f"An exception occured: {e}")

# Debug function for writing money
def moneyHax():
    print("How much would you like to put on your card?")
    try:
        # We do this to verify the the user input a number
        money = int(input())
        print("Hold tag near reader")
        # RFID only accepts strings
        rfid.write(str(money))
        print(f"Set money to {money}")
    except ValueError:
        print(f"{money} is not a number")
        moneyHax()
    except Exception as e:
        print(f"An exception occured: {e}")

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
            LPDatabase.lpDict[licensePlate] = time.strftime("%H:%M:%S")

# ---------- Quick functions for opening and closing the boomgate ---------- #

def openBoomGate():
    servo.angle = 90

def closeBoomGate():
    servo.angle = 0

# ---------- Util Functions ---------- #

# Frame getter
def getCameraFrame(resize = True, nW = 320, nH = 240):
    success, frame = camera.read()
    if success:
        if resize:
            frame = cv.resize(frame, (nW, nH))
        return frame

# Fn for cleaning up handles and resource
def cleanUpAndExit():
    # Release the camera capture
    camera.release()
    # Close all the OpenCV windows
    cv.destroyAllWindows()
    # Cleanup the GPIO system... whatever that actually does
    GPIO.cleanup()
    # Exit the Python interpreter
    exit()

# Fn for exiting on Escape key
def exitOnEsc():
    if cv.waitKey(1) == ESC_KEY:
        return True











# Banish this to the Shadow Realm so everything works properly
mainLoop()