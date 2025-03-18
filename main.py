# ---------- Imports ---------- #

import cv2 as cv
import numpy as np
import RPi.GPIO as GPIO

from time import sleep
from gpiozero import AngularServo
from mfrc522 import SimpleMFRC522

import pytesseract, time

# ---------- Variables ---------- #

continueReadingRFID = True

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

# ---------- Testing Rig Code ---------- #

# Array of tests to do
tests = ["OCR", "RFID", "Servo", "DB test", "Mon hax", "Charger test", "Exit"]

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
        elif selectedTest == "DB test":
            DBTest()
        elif selectedTest == "Mon hax":
            moneyHax()
        elif selectedTest == "Charger test":
            chargeUserMoney()
        elif selectedTest == "Exit":
            print("Exited testing")
            cleanUpAndExit()

        selectTest()
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

        # Modify frame for better reading
        img = cv.resize(img, (320, 120))

        img = np.array(img)

        img_empty = np.zeros((img.shape[0], img.shape[1]))

        # Apply various image modifactions to make text reading easier
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        img = cv.normalize(img, img_empty, 0, 255, cv.NORM_MINMAX)
        img = cv.threshold(img, 100, 255, cv.THRESH_BINARY)[1]
        img = cv.GaussianBlur(img, (1, 1), 0)

        # Show the modified image
        cv.imshow("Camera Vision", img)

        # Obtain the processed text
        text = pytesseract.image_to_string(img)
        print(f"Text: <{text}>")

        if exitOnEsc():
            break

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
 
# Servo test function
def ServoTest():
    print("Started servo test")
    while True:
        servo.angle = 0    # Move to 0 degrees
        sleep(2)
        servo.angle = 90   # Move to 90 degrees
        sleep(2)
        servo.angle = -90  # Move to 180 degrees

        if exitOnEsc():
            break

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
        money = int(input())
        print("Hold tag near reader")
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
            LPDatabase.lpDict[licensePlate] = time.strftime("%H:%M:%S") # Yes. From here: https://stackoverflow.com/questions/14700073/24-hour-format-for-python-timestamp

    @staticmethod
    def printDB():
        for key in LPDatabase.lpDict:
            print(key, LPDatabase.lpDict[key])

# ---------- Quick functions for opening and closing the boomgate ---------- #

def openBoomGate():
    servo.angle = 90

def closeBoomGate():
    servo.angle = 0

# ---------- Util Functions ---------- #

# Frame getter
def getCameraFrame():
    success, frame = camera.read()
    # This should probably have a condition for if the frame fetch fails
    if success:
        image = cv.resize(frame, (320, 240))
        return image

# Fn for cleaning up handles and resource
def cleanUpAndExit():
    camera.release()
    cv.destroyAllWindows()
    #rfid.cleanup()
    GPIO.cleanup()
    exit()

# Fn for exiting on Escape key
def exitOnEsc():
    if cv.waitKey(1) == ESC_KEY:
        return True










# Banish this to the Shadow Realm so everything works properly
selectTest()