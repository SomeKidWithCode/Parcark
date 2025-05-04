# This is the final build file #

# ---------- Imports ---------- #

import cv2 as cv
import numpy as np
import RPi.GPIO as GPIO

from time import sleep
from gpiozero import AngularServo
from mfrc522 import SimpleMFRC522
from enum import Enum
from ecies.utils import generate_key
from ecies import encrypt, decrypt

import pytesseract, time, re, socket, binascii

# ---------- Constant Variables ---------- #

# Constant for the escape key when using cv.waitKey
ESC_KEY = 27

# Constant for the amount of money charged when exiting
CHARGE_RATE = 5

# Constants for the slicing dimensions for OCR
OCR_SLICE_WIDTH = 700
OCR_SLICE_HEIGHT = 200

# ----- Socket Constants ----- #

HEADER = 64                         # Header message size
PORT = 50512                        # Server port
FORMAT = "utf-8"                    # encode/decode format
DISCONNECT_MESSAGE = "DISCONNECT"   # Disconnect message
SERVER = "10.190.207.221"           # Sever IP Address
ADDR = (SERVER, PORT)               # IP-Port tuple

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

def init():
    SocketHandler.init()
    log("init", "Entering main loop.")
    mainLoop()

def mainLoop():
    getOCRResult()

def getOCRResult():
    sameResultCount = 0
    ocrRes = None

    while True:
        # Get cam frame
        img = getCameraFrame(False)

        if img is None:
            continue



        # Modify frame for better reading
        height, width = img.shape[:2]
    
        # Calculate center coordinates
        mid_x, mid_y = width // 2, height // 2
        
        # Calculate crop boundaries
        cw2, ch2 = OCR_SLICE_WIDTH // 2, OCR_SLICE_HEIGHT // 2
        x_start = mid_x - cw2
        x_end = mid_x + cw2 + (OCR_SLICE_WIDTH % 2)  # Handles odd widths
        y_start = mid_y - ch2
        y_end = mid_y + ch2 + (OCR_SLICE_HEIGHT % 2)  # Handles odd heights
        
        # Perform the crop
        img = img[y_start:y_end, x_start:x_end]



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

        # Use RegEx to filter the output so only characters we expect are outputed
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

            log("LPDatabase", "Attempting to charge {licensePlate}")
            sckt_msg = SocketHandler.send(f"{DatabaseCommands.TRYCHARGE}:{licensePlate}:{666}:{6.9}")
            if sckt_msg == "NULL":
                print("User account empty")
            else:
                print("Charge successful")

            return val
        else:
            raise Exception("Unable to fetch time from non-existent entry")

    @staticmethod
    def push(licensePlate):
        if licensePlate in LPDatabase.lpDict:
            raise Exception("A duplicate license plate entry cannot exist")
        else:
            LPDatabase.lpDict[licensePlate] = time.strftime("%H:%M:%S")

            log("LPDatabase", "Adding license plate {licensePlate} to register")
            SocketHandler.send(f"{DatabaseCommands.REGISTERPLATE}:{licensePlate}:{666}:{420}")


# ---------- Socket Handler Class ---------- #

class SocketHandler:
    clientSocket = None

    @staticmethod
    def init():
        log("SocketHandler", "Initalizing socket connection...")
        SocketHandler.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SocketHandler.clientSocket.connect(ADDR)
        log("SocketHandler", "Socket connected")

    # Be aware that this method (currently) blocks while it waits for server to respond
    @staticmethod
    def send(send_msg):
        message = send_msg.encode(FORMAT)
        send_msg_length = len(message)
        send_length = str(send_msg_length).encode(FORMAT)
        send_length += b" " * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)
        log("SocketHandler", f"Sent message to {SERVER} on port {PORT}: {msg}")

        receive_msg_length = conn.recv(HEADER).decode(FORMAT)
        if receive_msg_length:
            receive_msg_length = int(msg_length)
            receive_msg = conn.recv(receive_msg_length).decode(FORMAT)
            log("SocketHandler", "Received message from {SERVER} on port {PORT}: {receive_msg}")
            return receive_msg
    
    @staticmethod
    def disconnect():
        SocketHandler.send(DISCONNECT_MESSAGE)
        log("SocketHandler", "Disconnected from socket")

class DatabaseCommands(Enum):
    TRYCHARGE = "TRYCHARGE"
    GETBANKBALANCE = "GETBANKBALANCE"
    REGISTERPLATE = "REGISTERPLATE"
    DISCONNECT = DISCONNECT_MESSAGE

    GETPLATEINFO = 0xf
    SHUTDOWN = 0xff

# ---------- En/Decryption Class ---------- #

# That's just what I name classes that do both encryption and decryption
class DicryptionHandler:
    @staticmethod
    def generateKeys():
        log("DicryptionHandler", "Generating new key pair...")
        key = generate_key()

        privateKey = binascii.hexlify(key.secret)
        publicKey = binascii.hexlify(key.public_key.format(True))

        log("DicryptionHandler", "Generated new key pair")
        return (privateKey, publicKey)

    @staticmethod
    def encryptText(text):
        log("DicryptionHandler", "Attempting to encrypt message")

    @staticmethod    
    def decryptText(text):
        log("DicryptionHandler", "Attempting to decrypt message")

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

# Fn for cleaning up handles and resources
def cleanUpAndExit():
    # Release the camera capture
    camera.release()

    # Close all the OpenCV windows
    cv.destroyAllWindows()

    # Cleanup the GPIO system... whatever that actually does
    GPIO.cleanup()

    # Disconnect from the socket
    SocketHandler.disconnect()

    # Exit the Python runtime
    exit()

# Fn for exiting on Escape key
def exitOnEsc():
    if cv.waitKey(1) == ESC_KEY:
        return True

# Pretty printing for 'debug' messages
def log(source, msg):
    print(f"[{time.strftime("%H:%M:%S")} - {source}]: {msg}")










# Banish this to the Shadow Realm so everything works properly
init()